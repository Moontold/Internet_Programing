from datetime import date, datetime, timezone
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.errors import AppError
from app.core.finance import Charge, ParentAccount, PaymentItem, monthly_stats, settle, validate_payment
from app.models import Parent, Payment, User
from app.repositories.lesson_repository import LessonRepository
from app.repositories.parent_repository import ParentRepository
from app.repositories.payment_repository import PaymentRepository
from app.repositories.student_repository import StudentRepository
from app.schemas import finance as schemas
from app.schemas.parent import ParentShort


def to_payment_schema(payment: Payment) -> schemas.Payment:
    return schemas.Payment(
        id=payment.id,
        amount=payment.amount,
        paid_on=payment.paid_on,
        comment=payment.comment,
        created_at=payment.created_at,
    )


def _to_items(payments: Sequence[Payment]) -> list[PaymentItem]:
    return [PaymentItem(amount=item.amount, paid_on=item.paid_on) for item in payments]


def _today() -> date:
    return datetime.now(timezone.utc).astimezone(settings.tz).date()


class FinanceService:
    """Платежи и счёт родителя. Баланс и «оплачено» не хранятся — считаются при каждом запросе."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._payments = PaymentRepository(db=db)
        self._parents = ParentRepository(db=db)
        self._students = StudentRepository(db=db)
        self._lessons = LessonRepository(db=db)

    async def _get_parent(self, parent_id: int) -> Parent:
        parent = await self._parents.get(parent_id=parent_id)
        if parent is None:
            raise AppError('Родитель не найден')
        return parent

    async def _account(self, parent: Parent) -> ParentAccount:
        """Счёт на родителя: все его дети, в том числе деактивированные."""
        student_ids = [child.id for child in parent.children]
        charges = await self._lessons.held_charges(student_ids=student_ids)
        payments = await self._payments.list_for_parent(parent_id=parent.id)
        return settle(charges=charges, payments=_to_items(payments))

    # --- чтение для других сервисов ----------------------------------------------------

    async def account_for_parent(self, parent_id: int) -> ParentAccount:
        return await self._account(parent=await self._get_parent(parent_id=parent_id))

    async def paid_ids_for_students(self, student_ids: list[int]) -> set[tuple[int, int]]:
        """Оплаченные участия (lesson_id, student_id) по счетам родителей этих учеников."""
        students = await self._students.get_many(ids=student_ids)
        parent_ids = {item.parent_id for item in students}
        paid: set[tuple[int, int]] = set()
        for parent_id in parent_ids:
            account = await self.account_for_parent(parent_id=parent_id)
            paid |= account.paid_ids
        return paid

    async def own_balance(self, user: User) -> schemas.ParentBalance:
        parent = await self._parents.get_by_user_id(user_id=user.id)
        if parent is None:
            raise AppError('Профиль родителя не найден')
        account = await self._account(parent=parent)
        return schemas.ParentBalance(balance=account.balance, debt=account.debt)

    # --- чтение репетитора --------------------------------------------------------------

    async def summary(self) -> schemas.FinanceSummary:
        rows: list[schemas.ParentAccountRow] = []
        for parent in await self._parents.list_all():
            account = await self._account(parent=parent)
            rows.append(schemas.ParentAccountRow(
                parent=ParentShort(id=parent.id, full_name=parent.user.full_name, phone=parent.phone),
                balance=account.balance,
                debt=account.debt,
                unpaid_count=len(account.unpaid),
            ))
        rows.sort(key=lambda row: (-row.debt, -max(row.balance, 0), row.parent.full_name))
        return schemas.FinanceSummary(
            parents=rows,
            total_debt=sum(row.debt for row in rows),
            total_prepaid=sum(max(row.balance, 0) for row in rows),
        )

    async def stats(self, year: int) -> schemas.MonthlyStats:
        start = datetime(year, 1, 1, tzinfo=settings.tz).astimezone(timezone.utc)
        end = datetime(year + 1, 1, 1, tzinfo=settings.tz).astimezone(timezone.utc)
        charges = await self._lessons.held_charges_between(start=start, end=end)
        payments = await self._payments.list_between(start=date(year, 1, 1), end=date(year, 12, 31))
        months = monthly_stats(charges=charges, payments=_to_items(payments), tz=settings.tz, year=year)
        return schemas.MonthlyStats(
            year=year,
            months=[
                schemas.MonthStatsItem(
                    month=item.month,
                    lessons_count=item.lessons_count,
                    earned=item.earned,
                    received=item.received,
                )
                for item in months
            ],
        )

    async def parent_finance(self, parent_id: int) -> schemas.ParentFinance:
        parent = await self._get_parent(parent_id=parent_id)
        account = await self._account(parent=parent)
        names = {child.id: child.user.full_name for child in parent.children}
        payments = await self._payments.list_for_parent(parent_id=parent.id)
        return schemas.ParentFinance(
            balance=account.balance,
            debt=account.debt,
            unpaid=[self._to_unpaid(charge=item, names=names) for item in account.unpaid],
            payments=[to_payment_schema(payment=item) for item in payments],
        )

    @staticmethod
    def _to_unpaid(charge: Charge, names: dict[int, str]) -> schemas.UnpaidCharge:
        return schemas.UnpaidCharge(
            lesson_id=charge.lesson_id,
            student_id=charge.student_id,
            student_name=names.get(charge.student_id, ''),
            held_at=charge.held_at,
            price=charge.price,
        )

    # --- правка репетитором -----------------------------------------------------------

    async def _get_payment(self, payment_id: int) -> Payment:
        payment = await self._payments.get(payment_id=payment_id)
        if payment is None:
            raise AppError('Платёж не найден')
        return payment

    async def add_payment(self, parent_id: int, data: schemas.PaymentCreate) -> schemas.Payment:
        await self._get_parent(parent_id=parent_id)
        validate_payment(amount=data.amount, paid_on=data.paid_on, today=_today())
        payment = await self._payments.add(Payment(
            parent_id=parent_id,
            amount=data.amount,
            paid_on=data.paid_on,
            comment=data.comment,
        ))
        await self._db.commit()
        return to_payment_schema(payment=await self._get_payment(payment_id=payment.id))

    async def update_payment(self, payment_id: int, data: schemas.PaymentUpdate) -> schemas.Payment:
        payment = await self._get_payment(payment_id=payment_id)
        validate_payment(
            amount=data.amount if data.amount is not None else payment.amount,
            paid_on=data.paid_on if data.paid_on is not None else payment.paid_on,
            today=_today(),
        )
        if data.amount is not None:
            payment.amount = data.amount
        if data.paid_on is not None:
            payment.paid_on = data.paid_on
        if data.comment is not None:
            payment.comment = data.comment
        await self._db.commit()
        return to_payment_schema(payment=payment)

    async def delete_payment(self, payment_id: int) -> None:
        payment = await self._get_payment(payment_id=payment_id)
        await self._payments.delete(payment=payment)
        await self._db.commit()

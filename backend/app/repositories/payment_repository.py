from datetime import date
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Payment


class PaymentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, payment_id: int) -> Optional[Payment]:
        result = await self._db.execute(select(Payment).where(Payment.id == payment_id))
        return result.scalar_one_or_none()

    async def add(self, payment: Payment) -> Payment:
        self._db.add(payment)
        await self._db.flush()
        return payment

    async def delete(self, payment: Payment) -> None:
        await self._db.delete(payment)
        await self._db.flush()

    async def list_for_parent(self, parent_id: int) -> Sequence[Payment]:
        stmt = (
            select(Payment)
            .where(Payment.parent_id == parent_id)
            .order_by(Payment.paid_on.desc(), Payment.id.desc())
        )
        return (await self._db.execute(stmt)).scalars().all()

    async def list_between(self, start: date, end: date) -> Sequence[Payment]:
        """Платежи с start <= paid_on <= end."""
        stmt = select(Payment).where(Payment.paid_on >= start, Payment.paid_on <= end)
        return (await self._db.execute(stmt)).scalars().all()

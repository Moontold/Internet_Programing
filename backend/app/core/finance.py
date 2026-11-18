"""Финансы: зачёт платежей по проведённым занятиям и заработок по месяцам. Чистые функции без БД.

Правила и контрольные примеры — docs/Требования/Спринт 3. Финансы и уведомления.md, разделы 1–2.
"""
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Iterable
from zoneinfo import ZoneInfo

from app.core.errors import AppError

MAX_PAYMENT = 1_000_000


@dataclass(frozen=True)
class Charge:
    """Начисление: участие ученика в проведённом неудалённом занятии по ставке участия."""

    lesson_id: int
    student_id: int
    held_at: datetime  # scheduled_start проведённого занятия, UTC
    price: int


@dataclass(frozen=True)
class PaymentItem:
    amount: int
    paid_on: date


@dataclass(frozen=True)
class ParentAccount:
    balance: int
    debt: int
    unpaid: list[Charge] = field(default_factory=list)
    paid_ids: set[tuple[int, int]] = field(default_factory=set)  # (lesson_id, student_id)


@dataclass(frozen=True)
class MonthStats:
    month: str  # 'YYYY-MM' в часовом поясе установки
    lessons_count: int
    earned: int
    received: int


def _charge_order(charge: Charge) -> tuple[datetime, int, int]:
    return charge.held_at, charge.lesson_id, charge.student_id


def settle(charges: Iterable[Charge], payments: Iterable[PaymentItem]) -> ParentAccount:
    """Платежи закрывают начисления от самого раннего; частично покрытое — не оплачено.

    Если сумма платежей не положительна, не оплачено ничего, даже начисление с нулевой ставкой.
    """
    paid_total = sum(item.amount for item in payments)
    ordered = sorted(charges, key=_charge_order)
    running = 0
    covered = paid_total > 0
    paid_ids: set[tuple[int, int]] = set()
    unpaid: list[Charge] = []
    for charge in ordered:
        running += charge.price
        covered = covered and running <= paid_total
        if covered:
            paid_ids.add((charge.lesson_id, charge.student_id))
        else:
            unpaid.append(charge)
    balance = paid_total - running
    return ParentAccount(balance=balance, debt=max(0, -balance), unpaid=unpaid, paid_ids=paid_ids)


def validate_payment(amount: int, paid_on: date, today: date) -> None:
    """Правила ввода платежа; today — сегодняшняя дата в часовом поясе установки."""
    if amount == 0:
        raise AppError('Сумма платежа не может быть нулевой')
    if abs(amount) > MAX_PAYMENT:
        raise AppError('Сумма платежа слишком большая')
    if paid_on > today:
        raise AppError('Дата платежа не может быть в будущем')


def monthly_stats(
    charges: Iterable[Charge],
    payments: Iterable[PaymentItem],
    tz: ZoneInfo,
    year: int,
) -> list[MonthStats]:
    """Двенадцать месяцев года: начисления — по местной дате занятия, платежи — по paid_on.

    Групповое занятие даёт начисление каждому участнику, но в число проведённых входит один раз.
    """
    lessons: list[set[int]] = [set() for _ in range(12)]
    earned = [0] * 12
    received = [0] * 12
    for charge in charges:
        local = charge.held_at.astimezone(tz)
        if local.year != year:
            continue
        lessons[local.month - 1].add(charge.lesson_id)
        earned[local.month - 1] += charge.price
    for payment in payments:
        if payment.paid_on.year != year:
            continue
        received[payment.paid_on.month - 1] += payment.amount
    return [
        MonthStats(
            month=f'{year}-{index + 1:02d}',
            lessons_count=len(lessons[index]),
            earned=earned[index],
            received=received[index],
        )
        for index in range(12)
    ]

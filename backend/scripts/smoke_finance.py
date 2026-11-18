"""Смоук-скрипт чистой логики финансов: app.core.finance.

Запуск из каталога backend: python scripts/smoke_finance.py
Не требует БД и .env. Контрольные примеры П-1 – П-9 — из раздела 2 документа
docs/Требования/Спринт 3. Финансы и уведомления.md.
"""
import sys
from datetime import date, datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.errors import AppError  # noqa: E402
from app.core.finance import Charge, PaymentItem, monthly_stats, settle, validate_payment  # noqa: E402

TZ = ZoneInfo('Europe/Moscow')
MASHA, PETYA = 1, 2
failed = 0


def check(condition: bool, label: str) -> None:
    global failed
    print(('ok    ' if condition else 'FAIL  ') + label)
    if not condition:
        failed += 1


def held(month: int, day: int, hour: int = 14) -> datetime:
    return datetime(2026, month, day, hour, 0, tzinfo=timezone.utc)


def pay(*amounts: int, paid_on: date = date(2026, 10, 20)) -> list[PaymentItem]:
    return [PaymentItem(amount=item, paid_on=paid_on) for item in amounts]


def validation_error(amount: int, paid_on: date, today: date) -> str:
    try:
        validate_payment(amount=amount, paid_on=paid_on, today=today)
    except AppError as error:
        return error.message
    return ''


def base_checks() -> None:
    charges = [
        Charge(lesson_id=3, student_id=1, held_at=held(9, 10), price=1500),
        Charge(lesson_id=1, student_id=1, held_at=held(9, 1), price=1500),
        Charge(lesson_id=2, student_id=1, held_at=held(9, 5), price=1500),
    ]
    none = settle(charges=charges, payments=[])
    check(none.balance == -4500 and none.debt == 4500, 'без платежей: долг = сумма')
    check([item.lesson_id for item in none.unpaid] == [1, 2, 3], 'неоплаченные в порядке дат')
    check(none.paid_ids == set(), 'ничего не оплачено')

    partial = settle(charges=charges, payments=pay(3200))
    check(partial.balance == -1300 and partial.paid_ids == {(1, 1), (2, 1)}, 'частичная оплата: первые два оплачены')
    check([item.lesson_id for item in partial.unpaid] == [3], 'частично покрытое = не оплачено')

    prepaid = settle(charges=charges, payments=pay(10000))
    check(prepaid.balance == 5500 and prepaid.debt == 0 and prepaid.unpaid == [], 'предоплата')

    free = [Charge(lesson_id=9, student_id=1, held_at=held(9, 2), price=0)]
    check(settle(charges=free, payments=[]).paid_ids == set(), 'нулевая ставка без платежей не оплачена')
    check(settle(charges=free, payments=pay(100)).paid_ids == {(9, 1)}, 'нулевая ставка при платеже оплачена')

    same_time = [
        Charge(lesson_id=5, student_id=2, held_at=held(9, 3), price=800),
        Charge(lesson_id=5, student_id=1, held_at=held(9, 3), price=1000),
    ]
    group = settle(charges=same_time, payments=pay(1000))
    check(group.paid_ids == {(5, 1)} and group.debt == 800, 'одно время: порядок по id ученика')


def control_examples() -> None:
    z1 = Charge(lesson_id=1, student_id=MASHA, held_at=held(10, 1), price=1500)
    z2 = Charge(lesson_id=2, student_id=PETYA, held_at=held(10, 3), price=1200)
    z3 = Charge(lesson_id=3, student_id=MASHA, held_at=held(10, 8), price=1500)
    z4 = Charge(lesson_id=4, student_id=PETYA, held_at=held(10, 10), price=1200)
    z5 = Charge(lesson_id=5, student_id=MASHA, held_at=held(10, 15), price=1500)
    base = [z4, z2, z3, z1]  # порядок на входе не важен

    def paid(account) -> list[int]:
        return sorted(lesson for lesson, _ in account.paid_ids)

    p1 = settle(charges=base, payments=pay(3000))
    check(paid(p1) == [1, 2] and p1.balance == -2400 and p1.debt == 2400, 'П-1 недоплата: З1, З2; долг 2400')
    p2 = settle(charges=base, payments=pay(5400))
    check(paid(p2) == [1, 2, 3, 4] and p2.balance == 0 and p2.debt == 0, 'П-2 ровная оплата: баланс 0')
    p3 = settle(charges=base, payments=pay(6000))
    check(paid(p3) == [1, 2, 3, 4] and p3.balance == 600, 'П-3 переплата: предоплата 600')
    p4 = settle(charges=[*base, z5], payments=pay(6000))
    check(paid(p4) == [1, 2, 3, 4] and p4.debt == 900, 'П-4 переплата, затем З5: долг 900')
    p5 = settle(charges=base, payments=pay(6000, -1000))
    check(paid(p5) == [1, 2, 3] and p5.debt == 400, 'П-5 возврат: З1 – З3; долг 400')
    p6 = settle(charges=[z1, z2, z4], payments=pay(3000))
    check(paid(p6) == [1, 2] and p6.debt == 900, 'П-6 отмена З3: З4 не оплачено; долг 900')
    z2_free = Charge(lesson_id=2, student_id=PETYA, held_at=z2.held_at, price=0)
    p7 = settle(charges=[z1, z2_free, z3, z4], payments=pay(1500))
    check(paid(p7) == [1, 2] and p7.debt == 2700, 'П-7 нулевая ставка у З2: З1, З2; долг 2700')
    p8 = settle(charges=base, payments=pay(2700, paid_on=date(2026, 9, 30)))
    check(paid(p8) == [1, 2] and p8.debt == 2700, 'П-8 платёж задним числом: З1, З2; долг 2700')
    z6 = [
        Charge(lesson_id=6, student_id=MASHA, held_at=held(10, 17), price=1500),
        Charge(lesson_id=6, student_id=PETYA, held_at=held(10, 17), price=1200),
    ]
    p9 = settle(charges=z6, payments=[])
    check(len(p9.unpaid) == 2 and p9.debt == 2700, 'П-9 групповое: два начисления; долг 2700')

    october = monthly_stats(charges=[*base, z5], payments=pay(6000, -1000), tz=TZ, year=2026)[9]
    check(
        october.month == '2026-10' and october.lessons_count == 5 and october.earned == 6900 and october.received == 5000,
        'октябрь по П-5 + З5: 5 занятий, наработано 6900, получено 5000',
    )


def stats_checks() -> None:
    stats = monthly_stats(
        charges=[
            Charge(lesson_id=1, student_id=1, held_at=held(9, 1), price=1500),
            # 2026-09-30 22:00 UTC = 1 октября 01:00 по Москве
            Charge(lesson_id=2, student_id=1, held_at=datetime(2026, 9, 30, 22, 0, tzinfo=timezone.utc), price=1500),
            Charge(lesson_id=3, student_id=1, held_at=held(11, 2), price=1000),
            Charge(lesson_id=3, student_id=2, held_at=held(11, 2), price=800),
        ],
        payments=[
            PaymentItem(amount=3000, paid_on=date(2026, 9, 15)),
            PaymentItem(amount=100, paid_on=date(2025, 12, 31)),
        ],
        tz=TZ,
        year=2026,
    )
    check(len(stats) == 12 and stats[0].month == '2026-01' and stats[11].month == '2026-12', '12 месяцев года')
    sep, octo, nov = stats[8], stats[9], stats[10]
    check(sep.lessons_count == 1 and sep.earned == 1500 and sep.received == 3000, 'сентябрь: 1 занятие, получено 3000')
    check(octo.lessons_count == 1 and octo.earned == 1500 and octo.received == 0, 'граница месяца по местному времени')
    check(nov.lessons_count == 1 and nov.earned == 1800, 'групповое занятие считается один раз, наработано по всем')
    check(sum(item.received for item in stats) == 3000, 'платёж другого года не считается')


def validation_checks() -> None:
    today = date(2026, 10, 20)
    check(validation_error(amount=0, paid_on=today, today=today) == 'Сумма платежа не может быть нулевой', 'нулевой платёж')
    check(validation_error(amount=1_000_001, paid_on=today, today=today) == 'Сумма платежа слишком большая',
          'платёж больше 1 000 000')
    check(validation_error(amount=-1_000_000, paid_on=today, today=today) == '', 'возврат 1 000 000 допустим')
    check(validation_error(amount=500, paid_on=date(2026, 10, 21), today=today) == 'Дата платежа не может быть в будущем',
          'платёж с завтрашней датой')
    check(validation_error(amount=500, paid_on=today, today=today) == '', 'платёж сегодняшним днём допустим')


def main() -> int:
    base_checks()
    control_examples()
    stats_checks()
    validation_checks()
    if failed:
        print(f'\nпровалено проверок: {failed}')
        return 1
    print('\nALL OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

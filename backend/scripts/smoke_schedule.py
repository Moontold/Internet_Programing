"""Смоук-скрипт чистой логики расписания app.core.schedule.

Запуск из каталога backend: python scripts/smoke_schedule.py
Не требует БД и .env: проверяет функции на примерных датах.
"""
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.schedule import (  # noqa: E402
    SeriesRule,
    day_before,
    is_finished,
    is_whole_periods,
    local_shift,
    missing_occurrences,
    occurrences,
    shift_start,
)

MSK = ZoneInfo('Europe/Moscow')
BERLIN = ZoneInfo('Europe/Berlin')

failed = 0


def check(condition: bool, label: str) -> None:
    global failed
    print(('ok    ' if condition else 'FAIL  ') + label)
    if not condition:
        failed += 1


def main() -> int:
    # Вторник 2026-09-08 17:00 по Москве = 14:00 UTC
    first = datetime(2026, 9, 8, 17, 0, tzinfo=MSK)
    weekly = SeriesRule(first_start=first, duration_minutes=60, interval_weeks=1, until=None)
    horizon = datetime(2026, 10, 7, 0, 0, tzinfo=timezone.utc)

    occ = occurrences(rule=weekly, horizon_end=horizon, tz=MSK)
    check(len(occ) == 5, f'каждую неделю без until: 5 вхождений до горизонта (получено {len(occ)})')
    check(all(item.tzinfo == timezone.utc for item in occ), 'все вхождения в UTC')
    check(occ[0] == first.astimezone(timezone.utc), 'первое вхождение = first_start')
    check(all(later - earlier == timedelta(weeks=1) for earlier, later in zip(occ, occ[1:])), 'шаг — неделя')
    check(all(item.astimezone(MSK).hour == 17 for item in occ), 'у всех местное время 17:00')

    biweekly = SeriesRule(first_start=first, duration_minutes=60, interval_weeks=2, until=date(2026, 10, 6))
    occ2 = occurrences(rule=biweekly, horizon_end=horizon + timedelta(weeks=20), tz=MSK)
    check(
        [item.astimezone(MSK).date() for item in occ2] == [date(2026, 9, 8), date(2026, 9, 22), date(2026, 10, 6)],
        'раз в две недели, until включительно',
    )
    check(occurrences(rule=weekly, horizon_end=first - timedelta(minutes=1), tz=MSK) == [], 'горизонт раньше начала — пусто')

    # Летнее время: в Берлине 29.03.2026 часы переводятся вперёд, занятие остаётся в 17:00 местного
    berlin_first = datetime(2026, 3, 24, 17, 0, tzinfo=BERLIN)
    berlin = occurrences(
        rule=SeriesRule(first_start=berlin_first, duration_minutes=60, interval_weeks=1, until=None),
        horizon_end=datetime(2026, 4, 2, tzinfo=timezone.utc),
        tz=BERLIN,
    )
    check([item.astimezone(BERLIN).hour for item in berlin] == [17, 17], 'переход на летнее время: 17:00 местного сохраняется')
    check(berlin[1] - berlin[0] == timedelta(days=7) - timedelta(hours=1), 'переход на летнее время: в UTC шаг на час короче')

    existing = {occ[0], occ[2]}
    missing = missing_occurrences(rule=weekly, horizon_end=horizon, tz=MSK, existing=existing)
    check(missing == [occ[1], occ[3], occ[4]], 'missing_occurrences пропускает существующие')
    check(missing_occurrences(rule=weekly, horizon_end=horizon, tz=MSK, existing=set(occ)) == [], 'повторный проход ничего не порождает')
    as_msk = {item.astimezone(MSK) for item in occ}
    check(missing_occurrences(rule=weekly, horizon_end=horizon, tz=MSK, existing=as_msk) == [], 'existing в другом поясе распознаётся')

    check(day_before(moment=occ[2], tz=MSK) == date(2026, 9, 21), 'day_before: местная дата минус день')
    late = datetime(2026, 9, 22, 0, 30, tzinfo=MSK)  # 21:30 UTC предыдущего дня
    check(day_before(moment=late, tz=MSK) == date(2026, 9, 21), 'day_before считает по местной дате, а не по UTC')

    moved = datetime(2026, 9, 23, 18, 30, tzinfo=MSK)  # третье занятие перенесли на среду 18:30
    check(local_shift(old_start=occ[2], new_start=moved, tz=MSK) == timedelta(days=1, minutes=90), 'local_shift: сутки и полтора часа')
    shifted = shift_start(original_start=occ[3], old_start=occ[2], new_start=moved, tz=MSK)
    check(shifted.astimezone(MSK) == datetime(2026, 9, 30, 18, 30, tzinfo=MSK), 'shift_start сдвигает следующее на ту же дельту')
    check(shifted.tzinfo == timezone.utc, 'shift_start возвращает UTC')

    check(is_whole_periods(shift=timedelta(weeks=1), interval_weeks=1), 'сдвиг на неделю в еженедельной серии — целый период')
    check(is_whole_periods(shift=timedelta(weeks=-4), interval_weeks=2), 'сдвиг на -4 недели при периоде 2 — целый период')
    check(not is_whole_periods(shift=timedelta(weeks=1), interval_weeks=2), 'неделя при периоде 2 — не целый')
    check(not is_whole_periods(shift=timedelta(hours=1), interval_weeks=1), 'час — не целый период')
    check(not is_whole_periods(shift=timedelta(0), interval_weeks=1), 'нулевой сдвиг — не сдвиг')

    now = datetime(2026, 9, 8, 15, 0, tzinfo=timezone.utc)
    check(is_finished(start=occ[0], duration_minutes=60, now=now), 'is_finished: занятие закончилось')
    check(not is_finished(start=occ[0], duration_minutes=61, now=now), 'is_finished: занятие ещё идёт')

    print('\nALL OK' if failed == 0 else f'\nFAIL: {failed}')
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())

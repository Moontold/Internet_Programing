"""Чистая логика расписания: без БД и ORM, на входе и выходе только даты.

Арифметика повторений ведётся в часовом поясе установки, чтобы «каждый вторник
в 17:00» оставалось 17:00 по местному времени и при переходе на летнее время;
результаты возвращаются в UTC.
"""
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class SeriesRule:
    first_start: datetime
    duration_minutes: int
    interval_weeks: int
    until: date | None


def _to_utc(moment: datetime) -> datetime:
    return moment.astimezone(timezone.utc)


def _local_naive(moment: datetime, tz: ZoneInfo) -> datetime:
    return moment.astimezone(tz).replace(tzinfo=None)


def occurrences(rule: SeriesRule, horizon_end: datetime, tz: ZoneInfo) -> list[datetime]:
    """Начала всех вхождений серии (UTC) от first_start до horizon_end и until включительно."""
    if rule.interval_weeks < 1:
        raise ValueError('interval_weeks must be >= 1')
    local_first = _local_naive(moment=rule.first_start, tz=tz)
    step = timedelta(weeks=rule.interval_weeks)
    result: list[datetime] = []
    index = 0
    while True:
        local_moment = (local_first + step * index).replace(tzinfo=tz)
        if rule.until is not None and local_moment.date() > rule.until:
            break
        moment_utc = _to_utc(local_moment)
        if moment_utc > horizon_end:
            break
        result.append(moment_utc)
        index += 1
    return result


def missing_occurrences(
    rule: SeriesRule,
    horizon_end: datetime,
    tz: ZoneInfo,
    existing: set[datetime],
) -> list[datetime]:
    """Вхождения, для которых ещё нет строки занятия. existing — значения original_start."""
    existing_utc = {_to_utc(item) for item in existing}
    return [item for item in occurrences(rule=rule, horizon_end=horizon_end, tz=tz) if item not in existing_utc]


def local_date(moment: datetime, tz: ZoneInfo) -> date:
    return moment.astimezone(tz).date()


def day_before(moment: datetime, tz: ZoneInfo) -> date:
    """Местная дата накануне moment: новое until серии при разрезе «это и последующие»."""
    return local_date(moment=moment, tz=tz) - timedelta(days=1)


def local_shift(old_start: datetime, new_start: datetime, tz: ZoneInfo) -> timedelta:
    """Сдвиг по местным часам: на сколько перенесли занятие с old_start на new_start."""
    return _local_naive(moment=new_start, tz=tz) - _local_naive(moment=old_start, tz=tz)


def shift_start(original_start: datetime, old_start: datetime, new_start: datetime, tz: ZoneInfo) -> datetime:
    """Сдвигает original_start на ту же местную дельту, что и old_start → new_start. Результат в UTC.

    Режимы «все» и «это и последующие»: репетитор перенёс одно занятие, остальные
    занятия серии двигаются на столько же по местному времени.
    """
    shift = local_shift(old_start=old_start, new_start=new_start, tz=tz)
    local = _local_naive(moment=original_start, tz=tz) + shift
    return _to_utc(local.replace(tzinfo=tz))


def is_whole_periods(shift: timedelta, interval_weeks: int) -> bool:
    """Сдвиг на целое число периодов серии накладывает вхождения друг на друга."""
    return shift != timedelta(0) and shift % timedelta(weeks=interval_weeks) == timedelta(0)


def lesson_end(start: datetime, duration_minutes: int) -> datetime:
    return start + timedelta(minutes=duration_minutes)


def is_finished(start: datetime, duration_minutes: int, now: datetime) -> bool:
    return lesson_end(start=start, duration_minutes=duration_minutes) <= now

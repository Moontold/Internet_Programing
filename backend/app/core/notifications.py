"""Построители уведомлений: без БД, сети и ORM. Проверяются scripts/smoke_notifications.py.

Виды, тексты, получатели и ключи дедупликации — матрица 4.2 документа
docs/Требования/Спринт 3. Финансы и уведомления.md. Текст уведомления целиком лежит в title,
body оставлен для подробностей.
"""
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Sequence
from zoneinfo import ZoneInfo

TITLE_MAX = 300

MONTHS = (
    'января', 'февраля', 'марта', 'апреля', 'мая', 'июня',
    'июля', 'августа', 'сентября', 'октября', 'ноября', 'декабря',
)
WEEKDAYS = ('пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс')


class Kind:
    """Виды уведомлений; повторяет models.enums.NotificationKind, не импортируя ORM."""

    LESSON_SOON = 'lesson_soon'
    LESSON_SOON_TUTOR = 'lesson_soon_tutor'
    HOMEWORK = 'homework'
    DEBT = 'debt'
    LESSON_CANCELLED = 'lesson_cancelled'
    LESSON_MOVED = 'lesson_moved'
    SCHEDULE_CHANGED = 'schedule_changed'
    HOMEWORK_MISSING = 'homework_missing'
    PAYMENT_REMINDER = 'payment_reminder'


@dataclass(frozen=True)
class LessonInfo:
    lesson_id: int
    start: datetime
    series_title: str = ''
    topic: str = ''
    student_names: tuple[str, ...] = ()

    @property
    def label(self) -> str:
        """Название занятия в тексте: название серии, иначе тема, иначе «Занятие»."""
        return self.series_title.strip() or self.topic.strip() or 'Занятие'


@dataclass(frozen=True)
class StudentRow:
    student_id: int
    student_user_id: int
    student_name: str
    student_active: bool
    parent_user_id: int
    parent_active: bool


@dataclass(frozen=True)
class Draft:
    user_id: int
    kind: str
    title: str
    body: str = ''
    lesson_id: Optional[int] = None
    dedupe_key: Optional[str] = None


# --- форматирование -------------------------------------------------------------------

def fmt_date(moment: datetime, tz: ZoneInfo) -> str:
    """«вт, 20 октября, 17:00» в часовом поясе установки."""
    local = moment.astimezone(tz)
    return f'{WEEKDAYS[local.weekday()]}, {local.day} {MONTHS[local.month - 1]}, {local:%H:%M}'


def fmt_money(amount: int) -> str:
    """Сумма с пробелом между разрядами: 2400 → «2 400»."""
    return f'{amount:,}'.replace(',', ' ')


def _stamp(moment: datetime) -> int:
    """Время занятия в ключе дедупликации: после переноса ключ другой, напоминание придёт снова."""
    return int(moment.timestamp())


# --- получатели -----------------------------------------------------------------------

def active_students(rows: Sequence[StudentRow]) -> list[StudentRow]:
    return [row for row in rows if row.student_active]


def active_parent_rows(rows: Sequence[StudentRow]) -> list[StudentRow]:
    """Строки с активным родителем: для текстов с именем ребёнка — по уведомлению на ребёнка."""
    return [row for row in rows if row.parent_active]


def active_parent_ids(rows: Sequence[StudentRow]) -> list[int]:
    """Активные родители без повторов: для текстов без имени ребёнка — одно уведомление на родителя."""
    return sorted({row.parent_user_id for row in rows if row.parent_active})


def _audience_ids(rows: Sequence[StudentRow]) -> list[int]:
    """Активные ученики и их активные родители, родитель — один раз."""
    return [*(row.student_user_id for row in active_students(rows=rows)), *active_parent_ids(rows=rows)]


# --- построители ----------------------------------------------------------------------

def lesson_soon_drafts(lesson: LessonInfo, rows: Sequence[StudentRow], tz: ZoneInfo) -> list[Draft]:
    date = fmt_date(moment=lesson.start, tz=tz)
    stamp = _stamp(moment=lesson.start)
    drafts = [
        Draft(
            user_id=row.student_user_id,
            kind=Kind.LESSON_SOON,
            title=f'Скоро занятие: {lesson.label}, {date}.',
            lesson_id=lesson.lesson_id,
            dedupe_key=f'{Kind.LESSON_SOON}:{lesson.lesson_id}:{stamp}:{row.student_user_id}',
        )
        for row in active_students(rows=rows)
    ]
    drafts += [
        Draft(
            user_id=row.parent_user_id,
            kind=Kind.LESSON_SOON,
            title=f'Скоро занятие у ребёнка {row.student_name}: {lesson.label}, {date}.',
            lesson_id=lesson.lesson_id,
            # Двое детей одного родителя в группе — два уведомления, ключ различается учеником
            dedupe_key=f'{Kind.LESSON_SOON}:{lesson.lesson_id}:{stamp}:{row.parent_user_id}:{row.student_id}',
        )
        for row in active_parent_rows(rows=rows)
    ]
    return drafts


def lesson_soon_tutor_draft(lesson: LessonInfo, tutor_user_id: int, tz: ZoneInfo) -> Draft:
    names = ', '.join(lesson.student_names)
    return Draft(
        user_id=tutor_user_id,
        kind=Kind.LESSON_SOON_TUTOR,
        title=f'Через 30 минут: {lesson.label}, {fmt_date(moment=lesson.start, tz=tz)}. Участники: {names}.',
        lesson_id=lesson.lesson_id,
        dedupe_key=f'{Kind.LESSON_SOON_TUTOR}:{lesson.lesson_id}:{_stamp(moment=lesson.start)}',
    )


def homework_drafts(lesson: LessonInfo, rows: Sequence[StudentRow], tz: ZoneInfo) -> list[Draft]:
    date = fmt_date(moment=lesson.start, tz=tz)
    drafts = [
        Draft(
            user_id=row.student_user_id,
            kind=Kind.HOMEWORK,
            title=f'Домашнее задание к занятию {lesson.label}, {date}.',
            lesson_id=lesson.lesson_id,
            dedupe_key=f'{Kind.HOMEWORK}:{lesson.lesson_id}:{row.student_user_id}',
        )
        for row in active_students(rows=rows)
    ]
    drafts += [
        Draft(
            user_id=row.parent_user_id,
            kind=Kind.HOMEWORK,
            title=f'Домашнее задание для ребёнка {row.student_name} к занятию {lesson.label}, {date}.',
            lesson_id=lesson.lesson_id,
            dedupe_key=f'{Kind.HOMEWORK}:{lesson.lesson_id}:{row.parent_user_id}:{row.student_id}',
        )
        for row in active_parent_rows(rows=rows)
    ]
    return drafts


def debt_draft(lesson: LessonInfo, parent_user_id: int, debt: int) -> Draft:
    return Draft(
        user_id=parent_user_id,
        kind=Kind.DEBT,
        title=f'Задолженность за занятия: {fmt_money(amount=debt)} ₽.',
        lesson_id=lesson.lesson_id,
        dedupe_key=f'{Kind.DEBT}:{lesson.lesson_id}:{parent_user_id}',
    )


def lesson_cancelled_drafts(lesson: LessonInfo, rows: Sequence[StudentRow], tz: ZoneInfo) -> list[Draft]:
    title = f'Занятие отменено: {lesson.label}, {fmt_date(moment=lesson.start, tz=tz)}.'
    return [
        Draft(
            user_id=user_id,
            kind=Kind.LESSON_CANCELLED,
            title=title,
            lesson_id=lesson.lesson_id,
            dedupe_key=f'{Kind.LESSON_CANCELLED}:{lesson.lesson_id}:{user_id}',
        )
        for user_id in _audience_ids(rows=rows)
    ]


def lesson_moved_drafts(
    lesson: LessonInfo,
    rows: Sequence[StudentRow],
    old_start: datetime,
    tz: ZoneInfo,
) -> list[Draft]:
    title = (
        f'Занятие перенесено: {lesson.label}, '
        f'{fmt_date(moment=old_start, tz=tz)} → {fmt_date(moment=lesson.start, tz=tz)}.'
    )
    return [
        Draft(user_id=user_id, kind=Kind.LESSON_MOVED, title=title, lesson_id=lesson.lesson_id)
        for user_id in _audience_ids(rows=rows)
    ]


def schedule_changed_drafts(lesson: LessonInfo, rows: Sequence[StudentRow], tz: ZoneInfo) -> list[Draft]:
    """lesson — первое затронутое будущее занятие после изменения."""
    title = (
        f'Изменилось расписание: {lesson.label}, начиная с {fmt_date(moment=lesson.start, tz=tz)}. '
        'Новое расписание — на сайте.'
    )
    return [
        Draft(user_id=user_id, kind=Kind.SCHEDULE_CHANGED, title=title, lesson_id=lesson.lesson_id)
        for user_id in _audience_ids(rows=rows)
    ]


def homework_missing_draft(lesson: LessonInfo, tutor_user_id: int, tz: ZoneInfo) -> Draft:
    return Draft(
        user_id=tutor_user_id,
        kind=Kind.HOMEWORK_MISSING,
        title=f'Не задана домашка: {lesson.label}, {fmt_date(moment=lesson.start, tz=tz)}.',
        lesson_id=lesson.lesson_id,
        dedupe_key=f'{Kind.HOMEWORK_MISSING}:{lesson.lesson_id}',
    )


def payment_reminder_draft(parent_user_id: int, debt: int) -> Draft:
    return Draft(
        user_id=parent_user_id,
        kind=Kind.PAYMENT_REMINDER,
        title=f'Напоминание об оплате: задолженность за занятия — {fmt_money(amount=debt)} ₽.',
    )


# --- запись и отбор -------------------------------------------------------------------

def drafts_to_rows(drafts: Sequence[Draft]) -> list[dict]:
    return [
        {
            'user_id': draft.user_id,
            'kind': draft.kind,
            'title': draft.title[:TITLE_MAX],
            'body': draft.body,
            'lesson_id': draft.lesson_id,
            'dedupe_key': draft.dedupe_key,
        }
        for draft in drafts
    ]


def is_due_soon(start: datetime, now: datetime, lead: timedelta) -> bool:
    """Занятие ещё не началось и начнётся не позже чем через lead."""
    return now < start <= now + lead


def needs_homework_reminder(
    start: datetime,
    duration_minutes: int,
    now: datetime,
    delay: timedelta,
    window: timedelta,
) -> bool:
    """Занятие закончилось не меньше delay назад, но не раньше чем window назад."""
    end = start + timedelta(minutes=duration_minutes)
    return now - window <= end <= now - delay

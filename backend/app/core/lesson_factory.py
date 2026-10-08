"""Мост между ORM и чистой логикой расписания: правило из серии, занятия из вхождений. Без обращений к БД."""
from datetime import datetime
from typing import Iterable

from app.core.schedule import SeriesRule, is_finished
from app.models import Lesson, LessonSeries, LessonStatus, LessonStudent, Student


def series_rule(series: LessonSeries) -> SeriesRule:
    return SeriesRule(
        first_start=series.first_start,
        duration_minutes=series.duration_minutes,
        interval_weeks=series.interval_weeks,
        until=series.until,
    )


def build_lesson(
    series_id: int | None,
    start: datetime,
    duration_minutes: int,
    students: Iterable[Student],
    now: datetime,
) -> Lesson:
    """Новое занятие; уже закончившееся сразу получает статус «проведено».

    Деактивированные ученики в новые занятия не попадают, ставка копируется из карточки.
    """
    finished = is_finished(start=start, duration_minutes=duration_minutes, now=now)
    lesson = Lesson(
        series_id=series_id,
        original_start=start,
        scheduled_start=start,
        duration_minutes=duration_minutes,
        status=LessonStatus.HELD if finished else LessonStatus.PLANNED,
        detached=series_id is None,
    )
    lesson.participants = [
        LessonStudent(student_id=student.id, price=student.price_per_lesson)
        for student in students
        if student.is_active
    ]
    return lesson


def sync_participants(lesson: Lesson, students: Iterable[Student]) -> None:
    """Приводит состав занятия к students: лишних убирает, недостающих активных добавляет."""
    wanted = {student.id: student for student in students}
    lesson.participants = [item for item in lesson.participants if item.student_id in wanted]
    present = {item.student_id for item in lesson.participants}
    for student_id, student in wanted.items():
        if student_id not in present and student.is_active:
            lesson.participants.append(LessonStudent(student_id=student_id, price=student.price_per_lesson))

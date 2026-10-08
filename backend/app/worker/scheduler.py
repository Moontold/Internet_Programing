import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Awaitable, Callable

from sqlalchemy import or_

from app.config import settings
from app.core.lesson_factory import build_lesson, series_rule
from app.core.schedule import is_finished, missing_occurrences
from app.database import DataBaseWorker, create_db
from app.models import Lesson, LessonSeries, LessonStatus, LoginAttempt, Session

MINUTE = 60
HOUR = 3600
DAY = 86400
# Записи о попытках входа нужны только для окна блокировки в 15 минут
LOGIN_ATTEMPTS_KEEP = timedelta(days=1)


class Scheduler:
    """Фоновые задачи: порождение занятий из серий, закрытие прошедших, очистка сессий."""

    def __init__(self) -> None:
        self.log = logging.getLogger('Scheduler')
        self.db: DataBaseWorker = create_db()

    # --- задачи --------------------------------------------------------------------------

    async def mark_finished_lessons(self) -> None:
        """Запланированные занятия, время которых закончилось, становятся проведёнными."""
        now = datetime.now(timezone.utc)
        candidates = await self.db.filter(
            Lesson,
            Lesson.status == LessonStatus.PLANNED,
            Lesson.deleted_at.is_(None),
            Lesson.scheduled_start <= now,
        )
        finished = [
            lesson.id
            for lesson in candidates
            if is_finished(start=lesson.scheduled_start, duration_minutes=lesson.duration_minutes, now=now)
        ]
        if not finished:
            return
        updated = await self.db.update_where(
            Lesson,
            Lesson.id.in_(finished),
            Lesson.status == LessonStatus.PLANNED,
            values={'status': LessonStatus.HELD},
        )
        self.log.info('Marked held: %s lessons', updated)

    async def top_up_series(self) -> None:
        """Дополняет действующие серии занятиями до горизонта; прошлое не порождается."""
        now = datetime.now(timezone.utc)
        today = now.astimezone(settings.tz).date()
        horizon_end = now + timedelta(weeks=settings.schedule_horizon_weeks)
        active = await self.db.filter(LessonSeries, or_(LessonSeries.until.is_(None), LessonSeries.until >= today))
        created = 0
        for series in active:
            if not any(student.is_active for student in series.students):
                continue
            existing = await self.db.column(Lesson.original_start, Lesson.series_id == series.id)
            starts = [
                item
                for item in missing_occurrences(
                    rule=series_rule(series=series),
                    horizon_end=horizon_end,
                    tz=settings.tz,
                    existing=set(existing),
                )
                if item >= now
            ]
            if not starts:
                continue
            lessons = [
                build_lesson(
                    series_id=series.id,
                    start=start,
                    duration_minutes=series.duration_minutes,
                    students=series.students,
                    now=now,
                )
                for start in starts
            ]
            await self.db.new_objs(lessons)
            created += len(lessons)
        if created:
            self.log.info('Generated %s lessons', created)

    async def cleanup(self) -> None:
        """Удаляет истёкшие сессии и старые записи о попытках входа."""
        now = datetime.now(timezone.utc)
        sessions = await self.db.delete_where(Session, Session.expires_at < now)
        attempts = await self.db.delete_where(LoginAttempt, LoginAttempt.attempted_at < now - LOGIN_ATTEMPTS_KEEP)
        self.log.info('Cleanup: %s sessions, %s login attempts', sessions, attempts)

    # --- цикл ----------------------------------------------------------------------------

    async def _every(self, seconds: int, task: Callable[[], Awaitable[None]], name: str) -> None:
        """Запускает задачу сразу и затем раз в seconds; сбой одной задачи не останавливает другие."""
        while True:
            try:
                await task()
            except Exception as exc:  # noqa: BLE001
                self.log.exception('Task %s failed: %s', name, exc)
            await asyncio.sleep(seconds)

    async def run(self) -> None:
        self.log.info(
            'Scheduler started, tz=%s, horizon=%s weeks',
            settings.app_timezone,
            settings.schedule_horizon_weeks,
        )
        await asyncio.gather(
            self._every(seconds=MINUTE, task=self.mark_finished_lessons, name='mark_finished_lessons'),
            self._every(seconds=HOUR, task=self.top_up_series, name='top_up_series'),
            self._every(seconds=DAY, task=self.cleanup, name='cleanup'),
        )

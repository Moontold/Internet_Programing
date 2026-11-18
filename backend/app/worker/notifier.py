import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

from sqlalchemy.orm import selectinload

from app.config import settings
from app.core import notifications as builders
from app.database import DataBaseWorker
from app.models import Lesson, LessonSeries, LessonStatus, LessonStudent, Notification, Role, Student, User

LESSON_OPTIONS = [
    selectinload(Lesson.participants).selectinload(LessonStudent.student).selectinload(Student.parent),
]


class Notifier:
    """Напоминания по времени: «Скоро занятие», «Через 30 минут», «Не задана домашка», очистка старых.

    Доставка во ВКонтакте появится в спринте 4: записи ждут её с vk_state = pending.
    """

    def __init__(self, db: DataBaseWorker) -> None:
        self.log = logging.getLogger('Notifier')
        self._db = db

    # --- вспомогательное ----------------------------------------------------------------

    async def _tutor_user_id(self) -> Optional[int]:
        tutors = await self._db.filter(User, User.role == Role.TUTOR, User.is_active.is_(True), limit=1)
        return tutors[0].id if tutors else None

    async def _series_titles(self, lessons: Sequence[Lesson]) -> dict[int, str]:
        ids = {item.series_id for item in lessons if item.series_id is not None}
        if not ids:
            return {}
        return {item.id: item.title for item in await self._db.filter(LessonSeries, LessonSeries.id.in_(ids))}

    @staticmethod
    def _rows(lesson: Lesson) -> list[builders.StudentRow]:
        return [
            builders.StudentRow(
                student_id=item.student.id,
                student_user_id=item.student.user_id,
                student_name=item.student.user.full_name,
                student_active=item.student.user.is_active,
                parent_user_id=item.student.parent.user_id,
                parent_active=item.student.parent.user.is_active,
            )
            for item in lesson.participants
        ]

    @staticmethod
    def _info(lesson: Lesson, rows: Sequence[builders.StudentRow], titles: dict[int, str]) -> builders.LessonInfo:
        return builders.LessonInfo(
            lesson_id=lesson.id,
            start=lesson.scheduled_start,
            series_title=titles.get(lesson.series_id or -1, ''),
            topic=lesson.topic,
            student_names=tuple(row.student_name for row in rows),
        )

    async def _emit(self, drafts: list[builders.Draft]) -> None:
        created = await self._db.new_rows_ignore_conflicts(
            model=Notification,
            rows=[{**row, 'vk_state': 'pending', 'vk_attempts': 0} for row in builders.drafts_to_rows(drafts=drafts)],
            index_elements=['dedupe_key'],
        )
        if created:
            self.log.info('Created %s notifications', created)

    # --- задачи --------------------------------------------------------------------------

    async def notify_upcoming(self) -> None:
        """Только не начавшиеся занятия: после простоя за прошедшие ничего не создаётся."""
        now = datetime.now(timezone.utc)
        lead = timedelta(hours=settings.notify_lead_hours)
        tutor_lead = timedelta(minutes=settings.notify_tutor_lead_minutes)
        lessons = await self._db.filter(
            Lesson,
            Lesson.status == LessonStatus.PLANNED,
            Lesson.deleted_at.is_(None),
            Lesson.scheduled_start > now,
            Lesson.scheduled_start <= now + lead,
            options=LESSON_OPTIONS,
        )
        if not lessons:
            return
        tutor_id = await self._tutor_user_id()
        titles = await self._series_titles(lessons=lessons)
        drafts: list[builders.Draft] = []
        for lesson in lessons:
            rows = self._rows(lesson=lesson)
            info = self._info(lesson=lesson, rows=rows, titles=titles)
            drafts += builders.lesson_soon_drafts(lesson=info, rows=rows, tz=settings.tz)
            if tutor_id is not None and builders.is_due_soon(start=lesson.scheduled_start, now=now, lead=tutor_lead):
                drafts.append(builders.lesson_soon_tutor_draft(lesson=info, tutor_user_id=tutor_id, tz=settings.tz))
        await self._emit(drafts=drafts)

    async def notify_missing_homework(self) -> None:
        """Через час после конца проведённого занятия текст домашки пуст; окно — сутки назад."""
        tutor_id = await self._tutor_user_id()
        if tutor_id is None:
            return
        now = datetime.now(timezone.utc)
        window = timedelta(hours=settings.notify_homework_window_hours)
        delay = timedelta(minutes=settings.notify_homework_delay_minutes)
        lessons = await self._db.filter(
            Lesson,
            Lesson.status == LessonStatus.HELD,
            Lesson.deleted_at.is_(None),
            Lesson.homework_text == '',
            Lesson.scheduled_start >= now - window,
            options=LESSON_OPTIONS,
        )
        due = [
            lesson
            for lesson in lessons
            if builders.needs_homework_reminder(
                start=lesson.scheduled_start,
                duration_minutes=lesson.duration_minutes,
                now=now,
                delay=delay,
                window=window,
            )
        ]
        if not due:
            return
        titles = await self._series_titles(lessons=due)
        await self._emit(drafts=[
            builders.homework_missing_draft(
                lesson=self._info(lesson=lesson, rows=self._rows(lesson=lesson), titles=titles),
                tutor_user_id=tutor_id,
                tz=settings.tz,
            )
            for lesson in due
        ])

    async def purge_old(self) -> None:
        cutoff = datetime.now(timezone.utc) - timedelta(days=settings.notifications_keep_days)
        removed = await self._db.delete_where(Notification, Notification.created_at < cutoff)
        if removed:
            self.log.info('Purged %s old notifications', removed)

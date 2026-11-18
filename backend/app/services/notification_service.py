from dataclasses import replace
from datetime import datetime, timezone
from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core import notifications as builders
from app.core.errors import AppError
from app.models import Lesson, Student
from app.repositories.lesson_repository import LessonRepository
from app.repositories.notification_repository import NotificationRepository
from app.repositories.parent_repository import ParentRepository
from app.repositories.student_repository import StudentRepository
from app.schemas import notification as schemas
from app.services.finance_service import FinanceService

DEFAULT_LIMIT = 20


def to_rows(students: Sequence[Student]) -> list[builders.StudentRow]:
    """Ученики с загруженными родителями → простые строки для чистых построителей."""
    return [
        builders.StudentRow(
            student_id=student.id,
            student_user_id=student.user_id,
            student_name=student.user.full_name,
            student_active=student.user.is_active,
            parent_user_id=student.parent.user_id,
            parent_active=student.parent.user.is_active,
        )
        for student in students
    ]


class NotificationService:
    """Колокольчик и событийные уведомления. Вызывающий оборачивает триггеры в защиту от сбоев."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._notifications = NotificationRepository(db=db)
        self._students = StudentRepository(db=db)
        self._parents = ParentRepository(db=db)
        self._lessons = LessonRepository(db=db)
        self._finance = FinanceService(db=db)

    # --- чтение ------------------------------------------------------------------------

    async def feed(self, user_id: int, limit: int = DEFAULT_LIMIT) -> schemas.NotificationsList:
        rows = await self._notifications.list_for_user(user_id=user_id, limit=limit)
        return schemas.NotificationsList(
            items=[
                schemas.NotificationItem(
                    id=row.id,
                    kind=row.kind,
                    title=row.title,
                    body=row.body,
                    lesson_id=row.lesson_id,
                    created_at=row.created_at,
                    read=row.read_at is not None,
                )
                for row in rows
            ],
            unread_count=await self._notifications.unread_count(user_id=user_id),
        )

    async def mark_read(self, user_id: int) -> None:
        await self._notifications.mark_all_read(user_id=user_id, now=datetime.now(timezone.utc))

    # --- общие части --------------------------------------------------------------------

    async def _students_of(self, lesson: Lesson) -> Sequence[Student]:
        return await self._students.get_many(ids=[item.student_id for item in lesson.participants])

    async def lesson_info(self, lesson: Lesson, rows: Sequence[builders.StudentRow]) -> builders.LessonInfo:
        labels = await self._lessons.series_labels(series_ids=[lesson.series_id] if lesson.series_id else [])
        label = labels.get(lesson.series_id or -1)
        return builders.LessonInfo(
            lesson_id=lesson.id,
            start=lesson.scheduled_start,
            series_title=label.title if label else '',
            topic=lesson.topic,
            student_names=tuple(row.student_name for row in rows),
        )

    async def _audience(self, lesson: Lesson) -> tuple[builders.LessonInfo, list[builders.StudentRow]]:
        rows = to_rows(students=await self._students_of(lesson=lesson))
        return await self.lesson_info(lesson=lesson, rows=rows), rows

    @staticmethod
    def _is_future(lesson: Lesson) -> bool:
        return lesson.scheduled_start > datetime.now(timezone.utc)

    # --- событийные триггеры --------------------------------------------------------------

    async def notify_cancelled(self, lesson: Lesson) -> None:
        """Отменено одно будущее занятие; отмена задним числом не уведомляет."""
        if not self._is_future(lesson=lesson):
            return
        info, rows = await self._audience(lesson=lesson)
        await self._notifications.add_drafts(drafts=builders.lesson_cancelled_drafts(lesson=info, rows=rows, tz=settings.tz))

    async def notify_moved(self, lesson: Lesson, old_start: datetime) -> None:
        """Одно занятие перенесено на будущее время."""
        if not self._is_future(lesson=lesson):
            return
        info, rows = await self._audience(lesson=lesson)
        await self._notifications.add_drafts(
            drafts=builders.lesson_moved_drafts(lesson=info, rows=rows, old_start=old_start, tz=settings.tz)
        )

    async def schedule_changed_drafts(self, first_affected: Lesson, link_lesson_id: int) -> list[builders.Draft]:
        """first_affected — первое затронутое будущее занятие, link_lesson_id — занятие, с которого начата правка.

        Черновики готовятся до правки, если первое затронутое занятие при ней удаляется.
        """
        info, rows = await self._audience(lesson=first_affected)
        info = replace(info, lesson_id=link_lesson_id)
        return builders.schedule_changed_drafts(lesson=info, rows=rows, tz=settings.tz)

    async def add(self, drafts: Sequence[builders.Draft]) -> None:
        await self._notifications.add_drafts(drafts=drafts)

    async def notify_schedule_changed(self, first_affected: Lesson, link_lesson_id: int) -> None:
        """Одно сообщение каждому ученику и родителю на изменение."""
        await self.add(drafts=await self.schedule_changed_drafts(first_affected=first_affected, link_lesson_id=link_lesson_id))

    async def notify_homework(self, lesson: Lesson) -> None:
        """Домашка к проведённому занятию и «Задолженность» родителю, если после этого есть долг."""
        students = await self._students_of(lesson=lesson)
        rows = to_rows(students=students)
        info = await self.lesson_info(lesson=lesson, rows=rows)
        drafts = builders.homework_drafts(lesson=info, rows=rows, tz=settings.tz)
        for student in self._one_per_parent(students=students):
            account = await self._finance.account_for_parent(parent_id=student.parent_id)
            if account.debt > 0:
                drafts.append(builders.debt_draft(lesson=info, parent_user_id=student.parent.user_id, debt=account.debt))
        await self._notifications.add_drafts(drafts=drafts)

    @staticmethod
    def _one_per_parent(students: Sequence[Student]) -> list[Student]:
        """У родителя двое детей в одном занятии — «Задолженность» всё равно одна."""
        seen: dict[int, Student] = {}
        for student in students:
            if student.parent.user.is_active:
                seen.setdefault(student.parent_id, student)
        return list(seen.values())

    async def remind_payment(self, parent_id: int) -> None:
        """Кнопка «Напомнить об оплате»: работает только при долге, повторяется при каждом нажатии."""
        parent = await self._parents.get(parent_id=parent_id)
        if parent is None:
            raise AppError('Родитель не найден')
        account = await self._finance.account_for_parent(parent_id=parent_id)
        if account.debt <= 0:
            raise AppError('У этого родителя нет задолженности')
        if not parent.user.is_active:
            raise AppError('Учётная запись родителя отключена')
        await self._notifications.add_drafts(
            drafts=[builders.payment_reminder_draft(parent_user_id=parent.user_id, debt=account.debt)]
        )

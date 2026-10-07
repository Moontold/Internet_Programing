from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Lesson, LessonSeries, LessonStatus, LessonStudent, Student


class LessonRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    @staticmethod
    def _with_participants() -> Select:
        return select(Lesson).options(
            selectinload(Lesson.participants).selectinload(LessonStudent.student).selectinload(Student.user),
        )

    def _base(self) -> Select:
        """Видимые занятия: удалённые (deleted_at) из выборок исключены."""
        return self._with_participants().where(Lesson.deleted_at.is_(None))

    async def get(self, lesson_id: int) -> Optional[Lesson]:
        result = await self._db.execute(self._base().where(Lesson.id == lesson_id))
        return result.scalar_one_or_none()

    async def add(self, lesson: Lesson) -> Lesson:
        self._db.add(lesson)
        await self._db.flush()
        return lesson

    async def add_many(self, lessons: list[Lesson]) -> None:
        self._db.add_all(lessons)
        await self._db.flush()

    async def delete(self, lesson: Lesson) -> None:
        await self._db.delete(lesson)
        await self._db.flush()

    async def soft_delete(self, lesson: Lesson, now: datetime) -> None:
        """Строка остаётся «надгробием»: занимает своё место в серии, и worker не порождает её снова."""
        lesson.deleted_at = now
        lesson.status = LessonStatus.CANCELLED
        lesson.detached = True
        await self._db.flush()

    async def existing_original_starts(self, series_id: int) -> set[datetime]:
        """Все занятые места серии, включая удалённые занятия."""
        result = await self._db.execute(select(Lesson.original_start).where(Lesson.series_id == series_id))
        return set(result.scalars().all())

    async def planned_in_series(
        self,
        series_id: int,
        from_original_start: Optional[datetime] = None,
    ) -> Sequence[Lesson]:
        stmt = self._base().where(Lesson.series_id == series_id, Lesson.status == LessonStatus.PLANNED)
        if from_original_start is not None:
            stmt = stmt.where(Lesson.original_start >= from_original_start)
        result = await self._db.execute(stmt.order_by(Lesson.original_start))
        return result.scalars().all()

    async def not_held_in_series(
        self,
        series_id: int,
        from_original_start: Optional[datetime] = None,
    ) -> Sequence[Lesson]:
        """Запланированные, отменённые и удалённые занятия серии — всё, что ещё не стало историей."""
        stmt = self._with_participants().where(Lesson.series_id == series_id, Lesson.status != LessonStatus.HELD)
        if from_original_start is not None:
            stmt = stmt.where(Lesson.original_start >= from_original_start)
        result = await self._db.execute(stmt.order_by(Lesson.original_start))
        return result.scalars().all()

    async def list_between(
        self,
        start: datetime,
        end: datetime,
        student_id: Optional[int] = None,
    ) -> Sequence[Lesson]:
        stmt = self._base().where(Lesson.scheduled_start >= start, Lesson.scheduled_start < end)
        if student_id is not None:
            stmt = stmt.join(LessonStudent, LessonStudent.lesson_id == Lesson.id).where(
                LessonStudent.student_id == student_id
            )
        result = await self._db.execute(stmt.order_by(Lesson.scheduled_start))
        return result.scalars().unique().all()

    async def series_titles(self, series_ids: list[int]) -> dict[int, str]:
        if not series_ids:
            return {}
        result = await self._db.execute(
            select(LessonSeries.id, LessonSeries.title).where(LessonSeries.id.in_(series_ids))
        )
        return {row.id: row.title for row in result.all()}

from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import Select, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.stats import HomeworkCounts
from app.models import HomeworkStatus, Lesson, LessonSeries, LessonStatus, LessonStudent, Student, lesson_files


class LessonRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    @staticmethod
    def _with_participants() -> Select:
        return select(Lesson).options(
            selectinload(Lesson.participants).selectinload(LessonStudent.student).selectinload(Student.user),
            selectinload(Lesson.files),
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

    async def list_for_students(self, student_ids: list[int], start: datetime, end: datetime) -> Sequence[Lesson]:
        if not student_ids:
            return []
        stmt = (
            self._base()
            .join(LessonStudent, LessonStudent.lesson_id == Lesson.id)
            .where(
                LessonStudent.student_id.in_(student_ids),
                Lesson.scheduled_start >= start,
                Lesson.scheduled_start < end,
            )
            .order_by(Lesson.scheduled_start)
        )
        result = await self._db.execute(stmt)
        return result.scalars().unique().all()

    async def get_by_file_id(self, file_id: int) -> Optional[Lesson]:
        stmt = self._base().join(lesson_files, lesson_files.c.lesson_id == Lesson.id).where(
            lesson_files.c.file_id == file_id
        )
        result = await self._db.execute(stmt)
        return result.scalars().first()

    async def homework_counts(self, student_id: int) -> HomeworkCounts:
        """Сделано, не сделано и средняя оценка по проведённым занятиям ученика."""
        stmt = (
            select(
                func.coalesce(func.sum(case((LessonStudent.homework_status == HomeworkStatus.DONE, 1), else_=0)), 0),
                func.coalesce(func.sum(case((LessonStudent.homework_status == HomeworkStatus.NOT_DONE, 1), else_=0)), 0),
                func.avg(LessonStudent.homework_grade),
            )
            .select_from(LessonStudent)
            .join(Lesson, Lesson.id == LessonStudent.lesson_id)
            .where(
                LessonStudent.student_id == student_id,
                Lesson.status == LessonStatus.HELD,
                Lesson.deleted_at.is_(None),
            )
        )
        done, not_done, avg = (await self._db.execute(stmt)).one()
        return HomeworkCounts(done=int(done), not_done=int(not_done), avg_grade=float(avg) if avg is not None else None)

    async def previous_grade(self, student_id: int, before: datetime) -> Optional[int]:
        """Оценка ученика за последнее проведённое занятие до before."""
        stmt = (
            select(LessonStudent.homework_grade)
            .join(Lesson, Lesson.id == LessonStudent.lesson_id)
            .where(
                LessonStudent.student_id == student_id,
                Lesson.status == LessonStatus.HELD,
                Lesson.deleted_at.is_(None),
                Lesson.scheduled_start < before,
            )
            .order_by(Lesson.scheduled_start.desc())
            .limit(1)
        )
        return (await self._db.execute(stmt)).scalar_one_or_none()

    async def series_titles(self, series_ids: list[int]) -> dict[int, str]:
        if not series_ids:
            return {}
        result = await self._db.execute(
            select(LessonSeries.id, LessonSeries.title).where(LessonSeries.id.in_(series_ids))
        )
        return {row.id: row.title for row in result.all()}

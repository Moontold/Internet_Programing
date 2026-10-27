from datetime import date
from typing import Optional, Sequence

from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import LessonSeries, series_students


class SeriesRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, series_id: int) -> Optional[LessonSeries]:
        result = await self._db.execute(select(LessonSeries).where(LessonSeries.id == series_id))
        return result.scalar_one_or_none()

    async def add(self, series: LessonSeries) -> LessonSeries:
        self._db.add(series)
        await self._db.flush()
        return series

    @staticmethod
    def _active(today: date) -> Select:
        return select(LessonSeries).where(or_(LessonSeries.until.is_(None), LessonSeries.until >= today))

    async def list_active_for_student(self, student_id: int, today: date) -> Sequence[LessonSeries]:
        stmt = (
            self._active(today=today)
            .join(series_students, series_students.c.series_id == LessonSeries.id)
            .where(series_students.c.student_id == student_id)
            .order_by(LessonSeries.first_start)
        )
        result = await self._db.execute(stmt)
        return result.scalars().unique().all()

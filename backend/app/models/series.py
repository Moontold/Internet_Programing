from datetime import date, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.student import Student

series_students = Table(
    'series_students',
    Base.metadata,
    Column('series_id', ForeignKey('lesson_series.id', ondelete='CASCADE'), primary_key=True),
    Column('student_id', ForeignKey('students.id', ondelete='CASCADE'), primary_key=True),
)


class LessonSeries(Base):
    """Правило повторения «каждые N недель с first_start до until (включительно) или бессрочно»."""

    __tablename__ = 'lesson_series'

    id: Mapped[int] = mapped_column(primary_key=True)
    first_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    interval_weeks: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    until: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    students: Mapped[list['Student']] = relationship(secondary=series_students, lazy='selectin', order_by='Student.id')

from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.student import Student


class Lesson(Base):
    """Конкретное занятие: порождено из серии или создано разово.

    original_start — место занятия в правиле серии, ключ идемпотентности порождения;
    scheduled_start — фактическое время после переносов. Удалённое занятие остаётся
    строкой с deleted_at, чтобы worker не породил его заново.
    """

    __tablename__ = 'lessons'
    __table_args__ = (UniqueConstraint('series_id', 'original_start', name='uq_lesson_series_original'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    series_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey('lesson_series.id', ondelete='SET NULL'), nullable=True, index=True
    )
    original_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scheduled_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(16), nullable=False, default='planned', index=True)
    detached: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    topic: Mapped[str] = mapped_column(String(300), nullable=False, default='')
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    participants: Mapped[list['LessonStudent']] = relationship(
        back_populates='lesson', cascade='all, delete-orphan', lazy='selectin', order_by='LessonStudent.student_id'
    )


class LessonStudent(Base):
    """Участие ученика в занятии; ставка копируется из карточки при порождении."""

    __tablename__ = 'lesson_students'

    lesson_id: Mapped[int] = mapped_column(ForeignKey('lessons.id', ondelete='CASCADE'), primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('students.id', ondelete='CASCADE'), primary_key=True)
    price: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    lesson: Mapped['Lesson'] = relationship(back_populates='participants')
    student: Mapped['Student'] = relationship(lazy='joined')

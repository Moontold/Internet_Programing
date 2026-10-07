from datetime import date, datetime, timedelta, timezone
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.errors import AppError
from app.core.lesson_factory import build_lesson, series_rule, sync_participants
from app.core.schedule import (
    day_before,
    is_whole_periods,
    local_date,
    local_shift,
    missing_occurrences,
    shift_start,
)
from app.models import Lesson, LessonSeries, LessonStatus, Student
from app.repositories.lesson_repository import LessonRepository
from app.repositories.series_repository import SeriesRepository
from app.repositories.student_repository import StudentRepository
from app.schemas import series as schemas


def to_series_schema(series: LessonSeries) -> schemas.Series:
    return schemas.Series(
        id=series.id,
        first_start=series.first_start,
        duration_minutes=series.duration_minutes,
        interval_weeks=series.interval_weeks,
        until=series.until,
        title=series.title,
        students=[schemas.SeriesStudent(id=item.id, full_name=item.user.full_name) for item in series.students],
    )


def _is_live_planned(lesson: Lesson) -> bool:
    return lesson.status == LessonStatus.PLANNED and lesson.deleted_at is None


class SeriesService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._series = SeriesRepository(db=db)
        self._lessons = LessonRepository(db=db)
        self._students = StudentRepository(db=db)

    # --- общие шаги ----------------------------------------------------------------------

    async def get_or_raise(self, series_id: int) -> LessonSeries:
        series = await self._series.get(series_id=series_id)
        if series is None:
            raise AppError('Серия занятий не найдена')
        return series

    async def load_students(self, student_ids: list[int]) -> list[Student]:
        """Ученики для нового состава: все должны существовать и быть активными."""
        students = list(await self._students.get_many(ids=student_ids))
        if len(students) != len(set(student_ids)):
            raise AppError('Некоторые ученики не найдены')
        inactive = [item.user.full_name for item in students if not item.is_active]
        if inactive:
            raise AppError('Ученик деактивирован: ' + ', '.join(inactive))
        return students

    @staticmethod
    def _check_until(until: Optional[date], first_start: datetime) -> None:
        if until is not None and until < local_date(moment=first_start, tz=settings.tz):
            raise AppError('Дата окончания серии раньше первого занятия')

    @staticmethod
    def _horizon_end(now: datetime) -> datetime:
        return now + timedelta(weeks=settings.schedule_horizon_weeks)

    async def generate(self, series: LessonSeries, from_moment: Optional[datetime]) -> int:
        """Порождает недостающие занятия серии до горизонта. Повторный вызов ничего не создаёт.

        from_moment отсекает прошлое: при правке серии задним числом занятия не порождаются.
        """
        if not any(student.is_active for student in series.students):
            return 0
        now = datetime.now(timezone.utc)
        existing = await self._lessons.existing_original_starts(series_id=series.id)
        starts = missing_occurrences(
            rule=series_rule(series=series),
            horizon_end=self._horizon_end(now=now),
            tz=settings.tz,
            existing=existing,
        )
        if from_moment is not None:
            starts = [item for item in starts if item >= from_moment]
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
        await self._lessons.add_many(lessons=lessons)
        return len(lessons)

    async def _trim_after(self, planned: Sequence[Lesson], from_date: date) -> None:
        """Запланированные с from_date: обычные удаляются, отделённые отменяются."""
        for lesson in planned:
            if local_date(moment=lesson.original_start, tz=settings.tz) < from_date:
                continue
            if lesson.detached:
                lesson.status = LessonStatus.CANCELLED
            else:
                await self._lessons.delete(lesson=lesson)

    # --- серия целиком -------------------------------------------------------------------

    async def create(self, data: schemas.SeriesCreate) -> schemas.Series:
        self._check_until(until=data.until, first_start=data.first_start)
        students = await self.load_students(student_ids=data.student_ids)
        series = LessonSeries(
            first_start=data.first_start,
            duration_minutes=data.duration_minutes,
            interval_weeks=data.interval_weeks,
            until=data.until,
            title=data.title,
        )
        series.students = students
        await self._series.add(series=series)
        # Занятия на горизонт появляются сразу; прошедшие вхождения рождаются «проведёнными»
        await self.generate(series=series, from_moment=None)
        await self._db.commit()
        return to_series_schema(series=series)

    async def update_all(self, series_id: int, data: schemas.SeriesUpdate) -> schemas.Series:
        series = await self.get_or_raise(series_id=series_id)
        await self.apply_all(series=series, data=data)
        await self._db.commit()
        return to_series_schema(series=series)

    async def apply_all(self, series: LessonSeries, data: schemas.SeriesUpdate) -> None:
        """Режим «все занятия»: меняет правило и все занятия, которые ему ещё следуют. Без commit.

        Проведённые не меняются. Отделённые сохраняют своё время, длительность и состав.
        """
        rows = await self._lessons.not_held_in_series(series_id=series.id)
        planned = [item for item in rows if _is_live_planned(lesson=item)]

        if data.first_start is not None and data.first_start != series.first_start:
            shift = local_shift(old_start=series.first_start, new_start=data.first_start, tz=settings.tz)
            if is_whole_periods(shift=shift, interval_weeks=series.interval_weeks):
                raise AppError(
                    'Сдвиг на целое число периодов серии накладывает занятия друг на друга. '
                    'Перенесите занятия по одному или остановите серию и создайте новую.'
                )
            for item in rows:
                # Отменённые и удалённые сдвигаются вместе с серией, иначе на их месте породится новое занятие
                item.original_start = shift_start(
                    original_start=item.original_start,
                    old_start=series.first_start,
                    new_start=data.first_start,
                    tz=settings.tz,
                )
                if _is_live_planned(lesson=item) and not item.detached:
                    item.scheduled_start = item.original_start
            series.first_start = data.first_start
        if data.duration_minutes is not None:
            series.duration_minutes = data.duration_minutes
            for item in planned:
                if not item.detached:
                    item.duration_minutes = data.duration_minutes
        if data.title is not None:
            series.title = data.title
        if data.student_ids is not None:
            students = await self.load_students(student_ids=data.student_ids)
            series.students = students
            for item in planned:
                if not item.detached:
                    sync_participants(lesson=item, students=students)
        if 'until' in data.model_fields_set:
            self._check_until(until=data.until, first_start=series.first_start)
            series.until = data.until
            if data.until is not None:
                await self._trim_after(planned=planned, from_date=data.until + timedelta(days=1))

        await self._db.flush()
        await self.generate(series=series, from_moment=datetime.now(timezone.utc))

    async def stop(self, series_id: int, from_date: date) -> schemas.Series:
        """Остановка серии: с from_date занятий больше нет, проведённые и отменённые остаются."""
        series = await self.get_or_raise(series_id=series_id)
        planned = await self._lessons.planned_in_series(series_id=series.id)
        series.until = from_date - timedelta(days=1)
        await self._trim_after(planned=planned, from_date=from_date)
        await self._db.commit()
        return to_series_schema(series=series)

    # --- «это и последующие» -------------------------------------------------------------

    async def _series_of(self, lesson: Lesson) -> LessonSeries:
        if lesson.series_id is None:
            raise AppError('Занятие не входит в серию')
        return await self.get_or_raise(series_id=lesson.series_id)

    async def cancel_following(self, lesson: Lesson) -> None:
        """Отмена «это и последующие»: серия заканчивается накануне, это занятие отменено."""
        series = await self._series_of(lesson=lesson)
        planned = await self._lessons.planned_in_series(series_id=series.id, from_original_start=lesson.original_start)
        series.until = day_before(moment=lesson.original_start, tz=settings.tz)
        for item in planned:
            if item.id == lesson.id:
                continue
            if item.detached:
                item.status = LessonStatus.CANCELLED
            else:
                await self._lessons.delete(lesson=item)
        lesson.status = LessonStatus.CANCELLED
        lesson.detached = True
        await self._db.flush()

    async def delete_following(self, lesson: Lesson, now: datetime) -> None:
        """Удаление «это и последующие»: серия заканчивается накануне, запланированные скрываются."""
        series = await self._series_of(lesson=lesson)
        planned = await self._lessons.planned_in_series(series_id=series.id, from_original_start=lesson.original_start)
        series.until = day_before(moment=lesson.original_start, tz=settings.tz)
        for item in planned:
            if item.id != lesson.id:
                await self._lessons.soft_delete(lesson=item, now=now)
        await self._lessons.soft_delete(lesson=lesson, now=now)

    async def split_from_lesson(
        self,
        lesson: Lesson,
        new_start: Optional[datetime],
        duration_minutes: Optional[int],
        student_ids: Optional[list[int]],
    ) -> LessonSeries:
        """Правка «это и последующие»: старая серия заканчивается накануне, с этого занятия идёт новая.

        Строка самого занятия переезжает в новую серию и сохраняет содержимое. Последующие
        обычные запланированные удаляются и порождаются заново по новому правилу; отделённые,
        отменённые и удалённые переезжают со сдвигом и продолжают занимать своё место.
        Проведённые остаются в старой серии.
        """
        old_series = await self._series_of(lesson=lesson)
        if student_ids is not None:
            students = await self.load_students(student_ids=student_ids)
        else:
            students = list(old_series.students)
        pivot = lesson.original_start
        first_start = new_start if new_start is not None else pivot

        new_series = LessonSeries(
            first_start=first_start,
            duration_minutes=duration_minutes if duration_minutes is not None else old_series.duration_minutes,
            interval_weeks=old_series.interval_weeks,
            until=old_series.until,
            title=old_series.title,
        )
        new_series.students = students
        await self._series.add(series=new_series)

        later = await self._lessons.not_held_in_series(series_id=old_series.id, from_original_start=pivot)
        old_series.until = day_before(moment=pivot, tz=settings.tz)
        for item in later:
            if item.id == lesson.id:
                continue
            if _is_live_planned(lesson=item) and not item.detached:
                await self._lessons.delete(lesson=item)
                continue
            item.series_id = new_series.id
            item.original_start = shift_start(
                original_start=item.original_start,
                old_start=pivot,
                new_start=first_start,
                tz=settings.tz,
            )

        lesson.series_id = new_series.id
        lesson.original_start = first_start
        if new_start is not None:
            lesson.scheduled_start = new_start
            lesson.detached = False
        if duration_minutes is not None:
            lesson.duration_minutes = duration_minutes
        sync_participants(lesson=lesson, students=students)
        await self._db.flush()
        # Только будущее: прошедшие места новой серии уже заняты проведёнными занятиями старой
        await self.generate(series=new_series, from_moment=datetime.now(timezone.utc))
        return new_series

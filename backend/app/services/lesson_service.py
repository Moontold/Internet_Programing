from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.errors import AppError
from app.core.lesson_factory import build_lesson, sync_participants
from app.core.schedule import shift_start
from app.models import Lesson, LessonStatus, LessonStudent
from app.repositories.lesson_repository import LessonRepository
from app.schemas import lesson as schemas
from app.schemas.series import SeriesUpdate
from app.services.series_service import SeriesService

MAX_RANGE = timedelta(days=366)


def to_participant(item: LessonStudent) -> schemas.LessonParticipant:
    return schemas.LessonParticipant(
        student_id=item.student_id,
        full_name=item.student.user.full_name,
        price=item.price,
    )


def to_lesson_short(lesson: Lesson, title: str) -> schemas.LessonShort:
    return schemas.LessonShort(
        id=lesson.id,
        series_id=lesson.series_id,
        scheduled_start=lesson.scheduled_start,
        duration_minutes=lesson.duration_minutes,
        status=lesson.status,
        detached=lesson.detached,
        topic=lesson.topic,
        title=title,
        participants=[to_participant(item=item) for item in lesson.participants],
    )


def to_lesson(lesson: Lesson, title: str) -> schemas.Lesson:
    return schemas.Lesson(
        **to_lesson_short(lesson=lesson, title=title).model_dump(),
        original_start=lesson.original_start,
    )


class LessonService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._lessons = LessonRepository(db=db)
        self._series_service = SeriesService(db=db)

    async def _get_or_raise(self, lesson_id: int) -> Lesson:
        lesson = await self._lessons.get(lesson_id=lesson_id)
        if lesson is None:
            raise AppError('Занятие не найдено')
        return lesson

    async def _titles(self, lessons: Sequence[Lesson]) -> dict[int, str]:
        ids = list({item.series_id for item in lessons if item.series_id is not None})
        return await self._lessons.series_titles(series_ids=ids)

    async def _reload(self, lesson_id: int) -> schemas.Lesson:
        """Перечитывает занятие из БД после правки: состав и связи могли поменяться."""
        self._db.expire_all()
        lesson = await self._get_or_raise(lesson_id=lesson_id)
        titles = await self._titles(lessons=[lesson])
        return to_lesson(lesson=lesson, title=titles.get(lesson.series_id or -1, ''))

    # --- чтение ------------------------------------------------------------------------

    async def list(self, start: datetime, end: datetime, student_id: Optional[int]) -> schemas.LessonsList:
        if end <= start:
            raise AppError('Конец периода должен быть позже начала')
        if end - start > MAX_RANGE:
            raise AppError('Период не может быть больше года')
        lessons = await self._lessons.list_between(start=start, end=end, student_id=student_id)
        titles = await self._titles(lessons=lessons)
        return schemas.LessonsList(lessons=[
            to_lesson_short(lesson=item, title=titles.get(item.series_id or -1, '')) for item in lessons
        ])

    async def get(self, lesson_id: int) -> schemas.Lesson:
        lesson = await self._get_or_raise(lesson_id=lesson_id)
        titles = await self._titles(lessons=[lesson])
        return to_lesson(lesson=lesson, title=titles.get(lesson.series_id or -1, ''))

    # --- правка ------------------------------------------------------------------------

    async def create_single(self, data: schemas.LessonCreate) -> schemas.Lesson:
        students = await self._series_service.load_students(student_ids=data.student_ids)
        lesson = build_lesson(
            series_id=None,
            start=data.scheduled_start,
            duration_minutes=data.duration_minutes,
            students=students,
            now=datetime.now(timezone.utc),
        )
        lesson.topic = data.title
        await self._lessons.add(lesson=lesson)
        await self._db.commit()
        return await self._reload(lesson_id=lesson.id)

    async def update(self, lesson_id: int, data: schemas.LessonUpdate) -> schemas.Lesson:
        lesson = await self._get_or_raise(lesson_id=lesson_id)
        if lesson.status == LessonStatus.CANCELLED:
            raise AppError('Отменённое занятие нельзя редактировать')

        # Тема правится только у этого занятия, область правки на неё не влияет
        if data.topic is not None:
            lesson.topic = data.topic

        schedule_touched = any(
            value is not None for value in (data.scheduled_start, data.duration_minutes, data.student_ids)
        )
        if schedule_touched:
            if lesson.status == LessonStatus.HELD and data.scheduled_start is not None:
                raise AppError('Проведённое занятие нельзя перенести')
            if lesson.series_id is None and data.scope != 'this':
                raise AppError('Занятие вне серии: доступен только режим «только это занятие»')
            if data.scope == 'this':
                await self._apply_this(lesson=lesson, data=data)
            elif data.scope == 'following':
                await self._series_service.split_from_lesson(
                    lesson=lesson,
                    new_start=data.scheduled_start,
                    duration_minutes=data.duration_minutes,
                    student_ids=data.student_ids,
                )
            else:
                await self._apply_all(lesson=lesson, data=data)

        await self._db.commit()
        return await self._reload(lesson_id=lesson_id)

    async def _apply_this(self, lesson: Lesson, data: schemas.LessonUpdate) -> None:
        """«Только это»: правится одна строка, занятие становится отделённым от серии."""
        if data.scheduled_start is not None:
            lesson.scheduled_start = data.scheduled_start
        if data.duration_minutes is not None:
            lesson.duration_minutes = data.duration_minutes
        if data.student_ids is not None:
            students = await self._series_service.load_students(student_ids=data.student_ids)
            sync_participants(lesson=lesson, students=students)
        lesson.detached = True

    async def _apply_all(self, lesson: Lesson, data: schemas.LessonUpdate) -> None:
        """«Все занятия»: перенос одного занятия двигает правило серии на ту же дельту."""
        series = await self._series_service.get_or_raise(series_id=lesson.series_id)
        new_first: Optional[datetime] = None
        if data.scheduled_start is not None:
            new_first = shift_start(
                original_start=series.first_start,
                old_start=lesson.original_start,
                new_start=data.scheduled_start,
                tz=settings.tz,
            )
        await self._series_service.apply_all(
            series=series,
            data=SeriesUpdate(
                first_start=new_first,
                duration_minutes=data.duration_minutes,
                student_ids=data.student_ids,
            ),
        )
        # Отделённое или проведённое занятие apply_all не трогает, но репетитор правил именно его
        if data.scheduled_start is not None:
            lesson.scheduled_start = data.scheduled_start
        if data.duration_minutes is not None:
            lesson.duration_minutes = data.duration_minutes
        if data.student_ids is not None:
            sync_participants(lesson=lesson, students=list(series.students))

    async def cancel(self, lesson_id: int, scope: str) -> schemas.Lesson:
        lesson = await self._get_or_raise(lesson_id=lesson_id)
        if lesson.status == LessonStatus.CANCELLED:
            raise AppError('Занятие уже отменено')
        if scope == 'following':
            await self._series_service.cancel_following(lesson=lesson)
        else:
            lesson.status = LessonStatus.CANCELLED
            lesson.detached = True
        await self._db.commit()
        return await self._reload(lesson_id=lesson_id)

    async def delete(self, lesson_id: int, scope: str) -> None:
        """Мягкое удаление: строка остаётся, чтобы worker не породил занятие заново."""
        lesson = await self._get_or_raise(lesson_id=lesson_id)
        if lesson.status == LessonStatus.HELD:
            raise AppError('Проведённое занятие нельзя удалить, только отменить')
        now = datetime.now(timezone.utc)
        if scope == 'following' and lesson.series_id is not None:
            await self._series_service.delete_following(lesson=lesson, now=now)
        else:
            await self._lessons.soft_delete(lesson=lesson, now=now)
        await self._db.commit()

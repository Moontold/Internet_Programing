from datetime import datetime, timedelta, timezone
from typing import Optional, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.errors import AppError
from app.core.lesson_factory import build_lesson, sync_participants
from app.core.projection import TUTOR_ACCESS, Access, project_full, project_short, visible_student_ids
from app.core.schedule import shift_start
from app.models import Lesson, LessonStatus, Role, User
from app.repositories.lesson_repository import LessonRepository
from app.repositories.parent_repository import ParentRepository
from app.repositories.student_repository import StudentRepository
from app.schemas import lesson as schemas
from app.schemas.series import SeriesUpdate
from app.services.series_service import SeriesService

MAX_RANGE = timedelta(days=366)


def check_range(start: datetime, end: datetime) -> None:
    if end <= start:
        raise AppError('Конец периода должен быть позже начала')
    if end - start > MAX_RANGE:
        raise AppError('Период не может быть больше года')


class LessonService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._lessons = LessonRepository(db=db)
        self._students = StudentRepository(db=db)
        self._parents = ParentRepository(db=db)
        self._series_service = SeriesService(db=db)

    # --- доступ ------------------------------------------------------------------------

    async def access_for(self, user: User) -> Access:
        """Каких учеников видит пользователь: репетитор — всех, родитель — детей, ученик — себя."""
        if user.role == Role.TUTOR:
            return TUTOR_ACCESS
        if user.role == Role.PARENT:
            parent = await self._parents.get_by_user_id(user_id=user.id)
            children = frozenset(child.id for child in parent.children) if parent is not None else frozenset()
            return Access(role=user.role, student_ids=children)
        student = await self._students.get_by_user_id(user_id=user.id)
        return Access(role=user.role, student_ids=frozenset({student.id}) if student is not None else frozenset())

    async def _get_or_raise(self, lesson_id: int) -> Lesson:
        lesson = await self._lessons.get(lesson_id=lesson_id)
        if lesson is None:
            raise AppError('Занятие не найдено')
        return lesson

    async def _titles(self, lessons: Sequence[Lesson]) -> dict[int, str]:
        ids = list({item.series_id for item in lessons if item.series_id is not None})
        return await self._lessons.series_titles(series_ids=ids)

    async def _full(self, lesson: Lesson, access: Access) -> schemas.Lesson:
        titles = await self._titles(lessons=[lesson])
        previous_grade: Optional[int] = None
        visible = visible_student_ids(lesson=lesson, access=access)
        if len(visible) == 1:
            previous_grade = await self._lessons.previous_grade(student_id=visible[0], before=lesson.scheduled_start)
        return project_full(
            lesson=lesson,
            access=access,
            title=titles.get(lesson.series_id or -1, ''),
            previous_grade=previous_grade,
        )

    async def _reload(self, lesson_id: int) -> schemas.Lesson:
        """Перечитывает занятие из БД после правки: состав и связи могли поменяться."""
        self._db.expire_all()
        return await self._full(lesson=await self._get_or_raise(lesson_id=lesson_id), access=TUTOR_ACCESS)

    async def project_list(self, lessons: Sequence[Lesson], access: Access) -> schemas.LessonsList:
        titles = await self._titles(lessons=lessons)
        return schemas.LessonsList(lessons=[
            project_short(lesson=item, access=access, title=titles.get(item.series_id or -1, '')) for item in lessons
        ])

    # --- чтение ------------------------------------------------------------------------

    async def list(self, start: datetime, end: datetime, student_id: Optional[int]) -> schemas.LessonsList:
        """Календарь репетитора."""
        check_range(start=start, end=end)
        lessons = await self._lessons.list_between(start=start, end=end, student_id=student_id)
        return await self.project_list(lessons=lessons, access=TUTOR_ACCESS)

    async def get(self, access: Access, lesson_id: int) -> schemas.Lesson:
        """Карточка занятия: чужое занятие не отдаётся, поля урезаются по роли."""
        lesson = await self._get_or_raise(lesson_id=lesson_id)
        if not access.allows(lesson=lesson):
            raise AppError('Нет доступа к этому занятию')
        return await self._full(lesson=lesson, access=access)

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
        lesson = await self._get_editable(lesson_id=lesson_id)

        # Содержание правится только у этого занятия, область правки на него не влияет
        if data.topic is not None:
            lesson.topic = data.topic
        if data.parent_comment is not None:
            lesson.parent_comment = data.parent_comment
        if data.tutor_notes is not None:
            lesson.tutor_notes = data.tutor_notes

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

    # --- домашка и оценки ----------------------------------------------------------------

    async def _get_editable(self, lesson_id: int) -> Lesson:
        lesson = await self._get_or_raise(lesson_id=lesson_id)
        if lesson.status == LessonStatus.CANCELLED:
            raise AppError('Отменённое занятие нельзя редактировать')
        return lesson

    async def save_homework(self, lesson_id: int, text: str) -> schemas.Lesson:
        lesson = await self._get_editable(lesson_id=lesson_id)
        lesson.homework_text = text
        lesson.homework_saved_at = datetime.now(timezone.utc)
        await self._db.commit()
        return await self._reload(lesson_id=lesson_id)

    async def update_participant(
        self,
        lesson_id: int,
        student_id: int,
        data: schemas.ParticipantUpdate,
    ) -> schemas.Lesson:
        """Статус домашки, оценка и ставка конкретного участника."""
        lesson = await self._get_editable(lesson_id=lesson_id)
        participant = next((item for item in lesson.participants if item.student_id == student_id), None)
        if participant is None:
            raise AppError('Ученик не участвует в этом занятии')
        if data.homework_status is not None:
            participant.homework_status = data.homework_status
        if data.clear_grade:
            participant.homework_grade = None
        elif data.homework_grade is not None:
            participant.homework_grade = data.homework_grade
        if data.price is not None:
            participant.price = data.price
        await self._db.commit()
        return await self._reload(lesson_id=lesson_id)

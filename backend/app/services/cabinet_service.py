from datetime import date, datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.errors import AppError
from app.core.stats import homework_stats
from app.models import Student, User
from app.repositories.lesson_repository import LessonRepository
from app.repositories.parent_repository import ParentRepository
from app.repositories.series_repository import SeriesRepository
from app.repositories.student_repository import StudentRepository
from app.schemas import cabinet as schemas
from app.schemas.lesson import LessonsList
from app.services.lesson_service import LessonService, check_range
from app.services.series_service import to_series_schema
from app.services.student_service import to_student_short


class CabinetService:
    """Кабинеты родителя и ученика: только свои дети и свои занятия."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._parents = ParentRepository(db=db)
        self._students = StudentRepository(db=db)
        self._series = SeriesRepository(db=db)
        self._lessons = LessonRepository(db=db)
        self._lesson_service = LessonService(db=db)

    @staticmethod
    def _today() -> date:
        return datetime.now(timezone.utc).astimezone(settings.tz).date()

    async def _child_card(self, student: Student) -> schemas.ChildCard:
        series = await self._series.list_active_for_student(student_id=student.id, today=self._today())
        counts = await self._lessons.homework_counts(student_id=student.id)
        return schemas.ChildCard(
            student=to_student_short(student=student),
            series=[to_series_schema(series=item) for item in series],
            stats=homework_stats(counts=counts),
        )

    async def children(self, user: User) -> schemas.ChildrenList:
        parent = await self._parents.get_by_user_id(user_id=user.id)
        if parent is None:
            raise AppError('Профиль родителя не найден')
        students = await self._students.list_for_parent(parent_id=parent.id)
        return schemas.ChildrenList(children=[await self._child_card(student=item) for item in students])

    async def child_lessons(self, user: User, student_id: int, start: datetime, end: datetime) -> LessonsList:
        check_range(start=start, end=end)
        access = await self._lesson_service.access_for(user=user)
        if not access.can_see(student_id=student_id):
            raise AppError('Нет доступа к этому ученику')
        lessons = await self._lessons.list_for_students(student_ids=[student_id], start=start, end=end)
        return await self._lesson_service.project_list(lessons=lessons, access=access)

    async def student_lessons(self, user: User, start: datetime, end: datetime) -> LessonsList:
        check_range(start=start, end=end)
        access = await self._lesson_service.access_for(user=user)
        lessons = await self._lessons.list_for_students(student_ids=list(access.student_ids or ()), start=start, end=end)
        return await self._lesson_service.project_list(lessons=lessons, access=access)

    async def student_series(self, user: User) -> schemas.SeriesList:
        student = await self._students.get_by_user_id(user_id=user.id)
        if student is None:
            raise AppError('Профиль ученика не найден')
        series = await self._series.list_active_for_student(student_id=student.id, today=self._today())
        return schemas.SeriesList(series=[to_series_schema(series=item) for item in series])

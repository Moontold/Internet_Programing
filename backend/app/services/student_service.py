from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.errors import AppError
from app.core.security import generate_temp_password, hash_password
from app.core.stats import homework_stats
from app.models import Role, Student, User
from app.repositories.lesson_repository import LessonRepository
from app.repositories.parent_repository import ParentRepository
from app.repositories.series_repository import SeriesRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.student_repository import StudentRepository
from app.repositories.user_repository import UserRepository
from app.schemas import student as schemas
from app.services.parent_service import to_parent_short
from app.services.series_service import to_series_schema


def to_student_short(student: Student) -> schemas.StudentShort:
    return schemas.StudentShort(
        id=student.id,
        full_name=student.user.full_name,
        grade=student.grade,
        grade_note=student.grade_note,
        format=student.format,
        is_active=student.is_active,
    )


def to_student_list_item(student: Student) -> schemas.StudentListItem:
    return schemas.StudentListItem(
        **to_student_short(student=student).model_dump(),
        parent=to_parent_short(parent=student.parent),
    )


class StudentService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._students = StudentRepository(db=db)
        self._parents = ParentRepository(db=db)
        self._users = UserRepository(db=db)
        self._sessions = SessionRepository(db=db)
        self._series = SeriesRepository(db=db)
        self._lessons = LessonRepository(db=db)

    async def _get_or_raise(self, student_id: int) -> Student:
        student = await self._students.get(student_id=student_id)
        if student is None:
            raise AppError('Ученик не найден')
        return student

    async def _check_parent(self, parent_id: int) -> None:
        if await self._parents.get(parent_id=parent_id) is None:
            raise AppError('Родитель не найден')

    async def build_card(self, student: Student) -> schemas.Student:
        today = datetime.now(timezone.utc).astimezone(settings.tz).date()
        series = await self._series.list_active_for_student(student_id=student.id, today=today)
        counts = await self._lessons.homework_counts(student_id=student.id)
        return schemas.Student(
            **to_student_list_item(student=student).model_dump(),
            login=student.user.login,
            price_per_lesson=student.price_per_lesson,
            series=[to_series_schema(series=item) for item in series],
            stats=homework_stats(counts=counts),
        )

    async def list(self, is_active: Optional[bool]) -> schemas.StudentsList:
        students = await self._students.list_all(is_active=is_active)
        return schemas.StudentsList(students=[to_student_list_item(student=item) for item in students])

    async def get(self, student_id: int) -> schemas.Student:
        return await self.build_card(student=await self._get_or_raise(student_id=student_id))

    async def create(self, data: schemas.StudentCreate) -> schemas.StudentCreated:
        if await self._users.login_exists(login=data.login):
            raise AppError('Такой логин уже занят')
        await self._check_parent(parent_id=data.parent_id)
        user = await self._users.add(user=User(
            login=data.login,
            password_hash=hash_password(password=data.password),
            role=Role.STUDENT,
            full_name=data.full_name,
        ))
        student = await self._students.add(student=Student(
            user_id=user.id,
            parent_id=data.parent_id,
            grade=data.grade,
            grade_note=data.grade_note,
            format=data.format,
            price_per_lesson=data.price_per_lesson,
        ))
        await self._db.commit()
        return schemas.StudentCreated(
            student=await self.get(student_id=student.id),
            password=data.password,
        )

    async def update(self, student_id: int, data: schemas.StudentUpdate) -> schemas.Student:
        student = await self._get_or_raise(student_id=student_id)
        if data.full_name is not None:
            student.user.full_name = data.full_name
        if data.parent_id is not None:
            await self._check_parent(parent_id=data.parent_id)
            student.parent_id = data.parent_id
        if 'grade' in data.model_fields_set:
            student.grade = data.grade
        if data.grade_note is not None:
            student.grade_note = data.grade_note
        if data.format is not None:
            student.format = data.format
        if data.price_per_lesson is not None:
            student.price_per_lesson = data.price_per_lesson
        if data.is_active is not None:
            student.is_active = data.is_active
            student.user.is_active = data.is_active
            if not data.is_active:
                await self._sessions.delete_for_user(user_id=student.user_id)
        await self._db.commit()
        # Смена parent_id не обновляет загруженную связь student.parent: перечитываем карточку
        self._db.expire_all()
        return await self.get(student_id=student_id)

    async def reset_password(self, student_id: int) -> str:
        """Генерирует новый пароль и завершает все сессии ученика."""
        student = await self._get_or_raise(student_id=student_id)
        password = generate_temp_password()
        student.user.password_hash = hash_password(password=password)
        await self._sessions.delete_for_user(user_id=student.user_id)
        await self._db.commit()
        return password

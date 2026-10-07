from typing import Optional, Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Parent, Student, User


class StudentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _base(self) -> Select:
        return (
            select(Student)
            .join(User, User.id == Student.user_id)
            .options(selectinload(Student.parent).selectinload(Parent.user))
        )

    async def get(self, student_id: int) -> Optional[Student]:
        result = await self._db.execute(self._base().where(Student.id == student_id))
        return result.scalar_one_or_none()

    async def list_all(self, is_active: Optional[bool] = None) -> Sequence[Student]:
        stmt = self._base().order_by(User.full_name, Student.id)
        if is_active is not None:
            stmt = stmt.where(Student.is_active.is_(is_active))
        result = await self._db.execute(stmt)
        return result.scalars().all()

    async def add(self, student: Student) -> Student:
        self._db.add(student)
        await self._db.flush()
        return student

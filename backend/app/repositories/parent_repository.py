from typing import Optional, Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Parent, Student, User


class ParentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _base(self) -> Select:
        return (
            select(Parent)
            .join(User, User.id == Parent.user_id)
            .options(selectinload(Parent.children).selectinload(Student.user))
        )

    async def get(self, parent_id: int) -> Optional[Parent]:
        result = await self._db.execute(self._base().where(Parent.id == parent_id))
        return result.scalar_one_or_none()

    async def list_all(self, is_active: Optional[bool] = None) -> Sequence[Parent]:
        stmt = self._base().order_by(User.full_name, Parent.id)
        if is_active is not None:
            stmt = stmt.where(User.is_active.is_(is_active))
        result = await self._db.execute(stmt)
        return result.scalars().all()

    async def add(self, parent: Parent) -> Parent:
        self._db.add(parent)
        await self._db.flush()
        return parent

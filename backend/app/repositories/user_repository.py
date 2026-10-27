from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Role, User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        return await self._db.get(User, user_id)

    async def get_by_login(self, login: str) -> Optional[User]:
        result = await self._db.execute(select(User).where(User.login == login))
        return result.scalar_one_or_none()

    async def get_tutor(self) -> Optional[User]:
        result = await self._db.execute(select(User).where(User.role == Role.TUTOR))
        return result.scalars().first()

    async def login_exists(self, login: str) -> bool:
        return await self.get_by_login(login=login) is not None

    async def add(self, user: User) -> User:
        self._db.add(user)
        await self._db.flush()
        return user

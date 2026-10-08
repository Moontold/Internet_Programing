from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Session


class SessionRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_token_hash(self, token_hash: str) -> Optional[Session]:
        result = await self._db.execute(select(Session).where(Session.token_hash == token_hash))
        return result.scalar_one_or_none()

    async def add(self, session: Session) -> Session:
        self._db.add(session)
        await self._db.flush()
        return session

    async def delete_by_token_hash(self, token_hash: str) -> None:
        await self._db.execute(delete(Session).where(Session.token_hash == token_hash))

    async def delete_for_user(self, user_id: int, keep_token_hash: Optional[str] = None) -> None:
        stmt = delete(Session).where(Session.user_id == user_id)
        if keep_token_hash is not None:
            stmt = stmt.where(Session.token_hash != keep_token_hash)
        await self._db.execute(stmt)

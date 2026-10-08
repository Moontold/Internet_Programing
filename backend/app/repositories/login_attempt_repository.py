from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import LoginAttempt


class LoginAttemptRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def count_failed_since(self, login: str, since: datetime) -> int:
        stmt = select(func.count()).select_from(LoginAttempt).where(
            LoginAttempt.login == login,
            LoginAttempt.success.is_(False),
            LoginAttempt.attempted_at >= since,
        )
        return int((await self._db.execute(stmt)).scalar_one())

    async def add(self, login: str, success: bool) -> None:
        self._db.add(LoginAttempt(login=login, success=success))
        await self._db.flush()

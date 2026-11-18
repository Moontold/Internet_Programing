from datetime import datetime
from typing import Sequence

from sqlalchemy import func, select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.notifications import Draft, drafts_to_rows
from app.models import Notification


class NotificationRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_for_user(self, user_id: int, limit: int) -> Sequence[Notification]:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .limit(limit)
        )
        result = await self._db.execute(stmt)
        return result.scalars().all()

    async def unread_count(self, user_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
        )
        return int((await self._db.execute(stmt)).scalar_one())

    async def mark_all_read(self, user_id: int, now: datetime) -> None:
        stmt = (
            update(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
            .values(read_at=now)
        )
        await self._db.execute(stmt)
        await self._db.commit()

    async def add_drafts(self, drafts: Sequence[Draft]) -> int:
        """Записывает новые; черновик с уже занятым dedupe_key молча отбрасывается."""
        rows = drafts_to_rows(drafts=drafts)
        if not rows:
            return 0
        stmt = (
            pg_insert(Notification)
            .values([{**row, 'vk_state': 'pending', 'vk_attempts': 0} for row in rows])
            .on_conflict_do_nothing(index_elements=['dedupe_key'])
        )
        result = await self._db.execute(stmt)
        await self._db.commit()
        return result.rowcount or 0

from typing import AsyncIterator
from uuid import uuid4

from asyncpg import Connection
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Базовый класс ORM-моделей. Сами модели появятся во втором спринте."""


class CConnection(Connection):
    def _get_unique_id(self, prefix: str) -> str:
        return f'__asyncpg_{prefix}_{uuid4()}__'


CONNECT_ARGS = {
    'statement_cache_size': 0,
    'prepared_statement_cache_size': 0,
    'connection_class': CConnection,
}

engine = create_async_engine(url=settings.database_url, connect_args=CONNECT_ARGS)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

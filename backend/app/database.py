import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Optional, Sequence, Type, TypeVar
from uuid import uuid4

from asyncpg import Connection
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.config import settings


class Base(DeclarativeBase):
    """Базовый класс ORM-моделей: модели лежат в app/models, схема БД — в миграциях Alembic."""


class CConnection(Connection):
    def _get_unique_id(self, prefix: str) -> str:
        return f'__asyncpg_{prefix}_{uuid4()}__'


CONNECT_ARGS = {
    'statement_cache_size': 0,
    'prepared_statement_cache_size': 0,
    'connection_class': CConnection,
}

# --- FastAPI: engine, фабрика сессий и зависимость ---------------------------------------

engine = create_async_engine(url=settings.database_url, connect_args=CONNECT_ARGS)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


# --- Прочие модули (worker): DataBaseWorker со своим подключением -----------------------

T = TypeVar('T')


class DataBaseWorker:
    def __init__(self, user: str, password: str, host: str, port: int, database: str) -> None:
        self.log = logging.getLogger('DataBaseWorker')
        self.log.info('Connecting to database')
        self.engine = create_async_engine(
            url=f'postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}',
            connect_args=CONNECT_ARGS,
        )
        self.session = async_sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)

    async def initialize_connection(self) -> None:
        async with self.engine.begin() as conn:
            await conn.run_sync(lambda sync_conn: None)
        # create_db() выполняет это в отдельном цикле asyncio.run(): соединение из пула
        # закрываем, чтобы рабочий цикл владельца открыл свои.
        await self.engine.dispose()
        self.log.info('Connected')

    @asynccontextmanager
    async def create_session(self) -> AsyncIterator[AsyncSession]:
        async with self.session() as db:
            try:
                yield db
            except Exception:
                await db.rollback()
                raise
            finally:
                await db.close()

    async def new_objs(self, objs: list, batch_size: int = 1000) -> None:
        async with self.create_session() as session:
            counter = 0
            for obj in objs:
                session.add(obj)
                counter += 1
                if counter == batch_size:
                    await session.commit()
                    counter = 0
            if counter != 0:
                await session.commit()

    async def filter(
        self,
        model: Type[T],
        *conditions: Any,
        order_by: Optional[Any] = None,
    ) -> Sequence[T]:
        async with self.create_session() as session:
            stmt = select(model).where(*conditions)
            if order_by is not None:
                stmt = stmt.order_by(order_by)
            result = await session.execute(stmt)
            return result.scalars().unique().all()

    async def column(self, column: Any, *conditions: Any) -> list[Any]:
        """Значения одной колонки без загрузки объектов целиком."""
        async with self.create_session() as session:
            result = await session.execute(select(column).where(*conditions))
            return list(result.scalars().all())

    async def update_where(self, model: Type[T], *conditions: Any, values: dict[str, Any]) -> int:
        async with self.create_session() as session:
            result = await session.execute(update(model).where(*conditions).values(**values))
            await session.commit()
            return result.rowcount or 0

    async def delete_where(self, model: Type[T], *conditions: Any) -> int:
        async with self.create_session() as session:
            result = await session.execute(delete(model).where(*conditions))
            await session.commit()
            return result.rowcount or 0


def create_db() -> DataBaseWorker:
    """Создаёт DataBaseWorker и проверяет подключение.

    Каждый владелец (Scheduler) вызывает её в __init__ и держит экземпляр в self.db.
    """
    db = DataBaseWorker(
        user=settings.postgres_user,
        password=settings.postgres_password,
        host=settings.db_host,
        port=settings.db_port,
        database=settings.postgres_db,
    )
    asyncio.run(db.initialize_connection())
    return db

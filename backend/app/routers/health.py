import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.schemas.base import OkResponse
from app.schemas.health import HealthResponse, HealthStatus

VERSION = '0.1.0'

log = logging.getLogger('health')
router = APIRouter(tags=['health'])


async def _database_status(db: AsyncSession) -> str:
    try:
        await db.execute(text('SELECT 1'))
        return 'ok'
    except Exception as error:
        log.error('Database is unavailable: %s', error)
        return f'ошибка подключения: {error.__class__.__name__}'


@router.get('/health', response_model=HealthResponse, summary='Состояние сервиса и БД')
async def health(db: AsyncSession = Depends(get_session)) -> HealthResponse:
    status = HealthStatus(
        service='tutor-backend',
        version=VERSION,
        database=await _database_status(db=db),
        timezone=settings.app_timezone,
    )
    return HealthResponse(payload=status)


@router.get('/ping', response_model=OkResponse, summary='Проверка доступности API')
async def ping() -> OkResponse:
    return OkResponse(message='pong')

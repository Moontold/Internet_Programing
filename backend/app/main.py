import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors import AppError
from app.database import async_session_maker
from app.middleware import csrf_middleware
from app.routers import auth, health, lessons, parents, series, students
from app.services.auth_service import AuthService

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
log = logging.getLogger('main')


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    async with async_session_maker() as db:
        await AuthService(db=db).ensure_tutor_exists()
    yield


app = FastAPI(
    title='Сайт репетитора — API',
    version='0.1.0',
    lifespan=lifespan,
    docs_url='/api/docs',
    openapi_url='/api/openapi.json',
)
app.middleware('http')(csrf_middleware)


@app.exception_handler(AppError)
async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    log.warning('AppError: %s', exc.message)
    return JSONResponse(status_code=200, content={'error': True, 'message': exc.message, 'payload': None})


@app.exception_handler(StarletteHTTPException)
async def http_error_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    """401/403/404 остаются стандартными кодами HTTP, но тело — тот же конверт."""
    return JSONResponse(
        status_code=exc.status_code,
        content={'error': True, 'message': str(exc.detail), 'payload': None},
        headers=getattr(exc, 'headers', None),
    )


@app.exception_handler(Exception)
async def unexpected_error_handler(_: Request, exc: Exception) -> JSONResponse:
    log.exception('Unhandled error: %s', exc)
    return JSONResponse(status_code=200, content={'error': True, 'message': 'Внутренняя ошибка', 'payload': None})


API_PREFIX = '/api'
app.include_router(health.router, prefix=API_PREFIX)
app.include_router(auth.router, prefix=API_PREFIX)
app.include_router(parents.router, prefix=API_PREFIX)
app.include_router(students.router, prefix=API_PREFIX)
app.include_router(series.router, prefix=API_PREFIX)
app.include_router(lessons.router, prefix=API_PREFIX)

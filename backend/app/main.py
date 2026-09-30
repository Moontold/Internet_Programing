import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.routers import health

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(name)s: %(message)s')
log = logging.getLogger('main')

app = FastAPI(
    title='Сайт репетитора — API',
    version='0.1.0',
    docs_url='/api/docs',
    openapi_url='/api/openapi.json',
)


@app.exception_handler(Exception)
async def unexpected_error_handler(_: Request, exc: Exception) -> JSONResponse:
    log.exception('Unhandled error: %s', exc)
    return JSONResponse(status_code=200, content={'error': True, 'message': 'Внутренняя ошибка', 'payload': None})


API_PREFIX = '/api'
app.include_router(health.router, prefix=API_PREFIX)

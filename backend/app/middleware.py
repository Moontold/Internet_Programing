from typing import Awaitable, Callable, Optional
from urllib.parse import urlsplit

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.config import settings

UNSAFE_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}


def _origin_of(url: str) -> Optional[str]:
    """Схема и хост адреса без пути: 'https://site.ru/a/b' → 'https://site.ru'."""
    parts = urlsplit(url)
    if not parts.scheme or not parts.netloc:
        return None
    return f'{parts.scheme}://{parts.netloc}'.lower()


def origin_allowed(origin: Optional[str], referer: Optional[str]) -> bool:
    """Изменяющий запрос пришёл со своего сайта: Origin (или Referer) совпадает с APP_ORIGIN."""
    expected = _origin_of(settings.app_origin)
    if origin is not None:
        return _origin_of(origin) == expected
    if referer is not None:
        return _origin_of(referer) == expected
    # Браузер всегда шлёт Origin с изменяющими запросами; без обоих заголовков приходят
    # только небраузерные клиенты (curl, скрипты), у которых нет чужой cookie для подделки.
    return True


async def csrf_middleware(request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
    if request.method in UNSAFE_METHODS and not origin_allowed(
        origin=request.headers.get('origin'),
        referer=request.headers.get('referer'),
    ):
        return JSONResponse(
            status_code=403,
            content={'error': True, 'message': 'Запрос отклонён: чужой источник (защита от CSRF)', 'payload': None},
        )
    return await call_next(request)

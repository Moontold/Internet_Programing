from typing import Awaitable, Callable, Optional

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_session
from app.models import Role, User
from app.services.auth_service import AuthService
from app.services.lesson_service import LessonService
from app.services.parent_service import ParentService
from app.services.series_service import SeriesService
from app.services.student_service import StudentService

SESSION_COOKIE = 'session'

ROLE_ADDRESSEE = {
    Role.TUTOR: 'репетитору',
    Role.PARENT: 'родителю',
    Role.STUDENT: 'ученику',
}


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        max_age=settings.session_days * 24 * 3600,
        httponly=True,
        secure=settings.cookie_secure,
        samesite='lax',
        path='/',
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE,
        path='/',
        httponly=True,
        secure=settings.cookie_secure,
        samesite='lax',
    )


def get_auth_service(db: AsyncSession = Depends(get_session)) -> AuthService:
    return AuthService(db=db)


def get_parent_service(db: AsyncSession = Depends(get_session)) -> ParentService:
    return ParentService(db=db)


def get_student_service(db: AsyncSession = Depends(get_session)) -> StudentService:
    return StudentService(db=db)


def get_series_service(db: AsyncSession = Depends(get_session)) -> SeriesService:
    return SeriesService(db=db)


def get_lesson_service(db: AsyncSession = Depends(get_session)) -> LessonService:
    return LessonService(db=db)


def get_session_token(request: Request) -> Optional[str]:
    return request.cookies.get(SESSION_COOKIE)


async def get_current_user(
    response: Response,
    token: Optional[str] = Depends(get_session_token),
    auth: AuthService = Depends(get_auth_service),
) -> User:
    """Пользователь по cookie сессии; без входа или с истёкшей сессией — 401."""
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Требуется вход')
    resolved = await auth.resolve_session(token=token)
    if resolved is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Сессия истекла, войдите заново')
    if resolved.extended:
        set_session_cookie(response=response, token=token)
    return resolved.user


def require_role(*roles: Role) -> Callable[..., Awaitable[User]]:
    """Зависимость «раздел только для этих ролей»: чужая роль получает 403."""
    detail = 'Раздел доступен только ' + ' и '.join(ROLE_ADDRESSEE[role] for role in roles)

    async def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
        return user

    return dependency


require_tutor = require_role(Role.TUTOR)
require_parent = require_role(Role.PARENT)
require_student = require_role(Role.STUDENT)

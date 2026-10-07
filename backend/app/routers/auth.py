from typing import Optional

from fastapi import APIRouter, Depends, Response

from app.models import User
from app.routers.deps import (
    clear_session_cookie,
    get_auth_service,
    get_current_user,
    get_session_token,
    set_session_cookie,
)
from app.schemas.auth import ChangePasswordRequest, LoginRequest, Profile, ProfileResponse
from app.schemas.base import OkResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix='/auth', tags=['auth'])


def to_profile(user: User) -> Profile:
    return Profile(id=user.id, role=user.role, full_name=user.full_name, login=user.login)


@router.post('/login', response_model=ProfileResponse, summary='Вход по логину и паролю')
async def login(
    body: LoginRequest,
    response: Response,
    auth: AuthService = Depends(get_auth_service),
) -> ProfileResponse:
    result = await auth.login(login=body.login, password=body.password)
    set_session_cookie(response=response, token=result.token)
    return ProfileResponse(payload=to_profile(user=result.user))


@router.post('/logout', response_model=OkResponse, summary='Выход: сессия завершается')
async def logout(
    response: Response,
    token: Optional[str] = Depends(get_session_token),
    auth: AuthService = Depends(get_auth_service),
) -> OkResponse:
    if token:
        await auth.logout(token=token)
    clear_session_cookie(response=response)
    return OkResponse()


@router.get('/me', response_model=ProfileResponse, summary='Текущий пользователь')
async def me(user: User = Depends(get_current_user)) -> ProfileResponse:
    return ProfileResponse(payload=to_profile(user=user))


@router.post('/change-password', response_model=OkResponse, summary='Смена своего пароля')
async def change_password(
    body: ChangePasswordRequest,
    user: User = Depends(get_current_user),
    token: str = Depends(get_session_token),
    auth: AuthService = Depends(get_auth_service),
) -> OkResponse:
    await auth.change_password(
        user=user,
        old_password=body.old_password,
        new_password=body.new_password,
        current_token=token,
    )
    return OkResponse()

from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse


class LoginRequest(BaseModel):
    login: str = Field(..., min_length=1, max_length=64, description='Логин')
    password: str = Field(..., min_length=1, max_length=128, description='Пароль')


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=1, max_length=128, description='Текущий пароль')
    new_password: str = Field(..., min_length=8, max_length=128, description='Новый пароль, не короче 8 символов')


class Profile(BaseModel):
    id: int = Field(..., description='ID пользователя')
    role: Literal['tutor', 'parent', 'student'] = Field(..., description='Роль')
    full_name: str = Field(..., description='ФИО')
    login: str = Field(..., description='Логин')


class ProfileResponse(BaseResponse):
    payload: Profile | None = Field(default=None, description='Профиль текущего пользователя')

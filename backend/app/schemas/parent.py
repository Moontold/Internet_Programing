from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse

LOGIN_PATTERN = r'^[a-zA-Z0-9_.-]+$'


class ParentShort(BaseModel):
    id: int = Field(..., description='ID родителя')
    full_name: str = Field(..., description='ФИО')
    phone: str = Field(default='', description='Телефон')


class ChildShort(BaseModel):
    id: int = Field(..., description='ID ученика')
    full_name: str = Field(..., description='ФИО')
    grade: Optional[int] = Field(default=None, description='Класс 1..11')
    is_active: bool = Field(..., description='Ученик активен')


class Parent(ParentShort):
    login: str = Field(..., description='Логин')
    contacts_note: str = Field(default='', description='Прочие контакты в свободной форме')
    is_active: bool = Field(..., description='Учётка активна: неактивный не может войти')
    children: list[ChildShort] = Field(default_factory=list, description='Дети')


class ParentsList(BaseModel):
    parents: list[Parent] = Field(default_factory=list, description='Родители')


class ParentsResponse(BaseResponse):
    payload: ParentsList = Field(default_factory=ParentsList, description='Список родителей')


class ParentResponse(BaseResponse):
    payload: Parent | None = Field(default=None, description='Карточка родителя')


class ParentCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200, description='ФИО')
    login: str = Field(..., min_length=3, max_length=64, pattern=LOGIN_PATTERN, description='Логин: латиница, цифры, _ . -')
    password: str = Field(..., min_length=8, max_length=128, description='Пароль, не короче 8 символов')
    phone: str = Field(default='', max_length=32, description='Телефон')
    contacts_note: str = Field(default='', max_length=2000, description='Прочие контакты')


class ParentUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=200, description='ФИО')
    phone: Optional[str] = Field(default=None, max_length=32, description='Телефон')
    contacts_note: Optional[str] = Field(default=None, max_length=2000, description='Прочие контакты')
    is_active: Optional[bool] = Field(default=None, description='Активировать / деактивировать учётку')


class ParentCreated(BaseModel):
    parent: Parent = Field(..., description='Созданный родитель')
    password: str = Field(..., description='Пароль: показывается один раз')


class ParentCreatedResponse(BaseResponse):
    payload: ParentCreated | None = Field(default=None, description='Созданный родитель и его пароль')

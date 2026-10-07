from typing import Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse
from app.schemas.parent import LOGIN_PATTERN, ParentShort

Format = Literal['offline', 'online']


class StudentShort(BaseModel):
    id: int = Field(..., description='ID ученика')
    full_name: str = Field(..., description='ФИО')
    grade: Optional[int] = Field(default=None, description='Класс 1..11')
    grade_note: str = Field(default='', description='Пометка к классу в свободной форме')
    format: Format = Field(..., description='Формат занятий')
    is_active: bool = Field(..., description='Ученик активен')


class StudentListItem(StudentShort):
    parent: ParentShort = Field(..., description='Родитель')


class Student(StudentListItem):
    login: str = Field(..., description='Логин')
    price_per_lesson: int = Field(..., description='Ставка за занятие, руб.')


class StudentsList(BaseModel):
    students: list[StudentListItem] = Field(default_factory=list, description='Ученики')


class StudentsResponse(BaseResponse):
    payload: StudentsList = Field(default_factory=StudentsList, description='Список учеников')


class StudentResponse(BaseResponse):
    payload: Student | None = Field(default=None, description='Карточка ученика')


class StudentCreate(BaseModel):
    full_name: str = Field(..., min_length=1, max_length=200, description='ФИО')
    login: str = Field(..., min_length=3, max_length=64, pattern=LOGIN_PATTERN, description='Логин: латиница, цифры, _ . -')
    password: str = Field(..., min_length=8, max_length=128, description='Пароль, не короче 8 символов')
    parent_id: int = Field(..., description='ID родителя')
    grade: Optional[int] = Field(default=None, ge=1, le=11, description='Класс 1..11')
    grade_note: str = Field(default='', max_length=100, description='Пометка к классу')
    format: Format = Field(..., description='Формат занятий')
    price_per_lesson: int = Field(default=0, ge=0, description='Ставка за занятие, руб.')


class StudentUpdate(BaseModel):
    full_name: Optional[str] = Field(default=None, min_length=1, max_length=200, description='ФИО')
    parent_id: Optional[int] = Field(default=None, description='ID родителя: перепривязка к другому родителю')
    grade: Optional[int] = Field(default=None, ge=1, le=11, description='Класс 1..11; явный null сбрасывает класс')
    grade_note: Optional[str] = Field(default=None, max_length=100, description='Пометка к классу')
    format: Optional[Format] = Field(default=None, description='Формат занятий')
    price_per_lesson: Optional[int] = Field(default=None, ge=0, description='Ставка за занятие, руб.')
    is_active: Optional[bool] = Field(default=None, description='Активировать / деактивировать')


class StudentCreated(BaseModel):
    student: Student = Field(..., description='Созданный ученик')
    password: str = Field(..., description='Пароль: показывается один раз')


class StudentCreatedResponse(BaseResponse):
    payload: StudentCreated | None = Field(default=None, description='Созданный ученик и его пароль')

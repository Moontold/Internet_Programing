from datetime import date, datetime
from typing import Optional

from pydantic import AwareDatetime, BaseModel, Field

from app.schemas.base import BaseResponse


class SeriesStudent(BaseModel):
    id: int = Field(..., description='ID ученика')
    full_name: str = Field(..., description='ФИО')


class Series(BaseModel):
    id: int = Field(..., description='ID серии')
    first_start: datetime = Field(..., description='Начало первого занятия (UTC)')
    duration_minutes: int = Field(..., description='Длительность, минут')
    interval_weeks: int = Field(..., description='Повтор каждые N недель')
    until: Optional[date] = Field(default=None, description='Последняя дата включительно; null — бессрочно')
    title: str = Field(default='', description='Название серии')
    students: list[SeriesStudent] = Field(default_factory=list, description='Ученики серии')


class SeriesResponse(BaseResponse):
    payload: Series | None = Field(default=None, description='Серия занятий')


class SeriesCreate(BaseModel):
    first_start: AwareDatetime = Field(..., description='Начало первого занятия, ISO 8601 с часовым поясом')
    duration_minutes: int = Field(..., ge=15, le=480, description='Длительность, минут')
    interval_weeks: int = Field(default=1, ge=1, le=8, description='Повтор каждые N недель')
    until: Optional[date] = Field(default=None, description='Последняя дата включительно; null — бессрочно')
    title: str = Field(default='', max_length=200, description='Название серии')
    student_ids: list[int] = Field(..., min_length=1, description='Ученики (одно занятие может быть групповым)')


class SeriesUpdate(BaseModel):
    """Правка серии в режиме «все занятия»: проведённые, отменённые и отделённые не меняются."""

    first_start: Optional[AwareDatetime] = Field(default=None, description='Новое начало: сдвигает все запланированные')
    duration_minutes: Optional[int] = Field(default=None, ge=15, le=480, description='Длительность, минут')
    until: Optional[date] = Field(default=None, description='Последняя дата; явный null делает серию бессрочной')
    title: Optional[str] = Field(default=None, max_length=200, description='Название серии')
    student_ids: Optional[list[int]] = Field(default=None, min_length=1, description='Ученики')


class SeriesStop(BaseModel):
    from_date: date = Field(..., description='Первая дата, с которой занятий больше нет')

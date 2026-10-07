from datetime import datetime
from typing import Literal, Optional

from pydantic import AwareDatetime, BaseModel, Field

from app.schemas.base import BaseResponse

Scope = Literal['this', 'following', 'all']
Status = Literal['planned', 'held', 'cancelled']


class LessonParticipant(BaseModel):
    student_id: int = Field(..., description='ID ученика')
    full_name: str = Field(..., description='ФИО ученика')
    price: Optional[int] = Field(default=None, description='Ставка за это занятие, руб.')


class LessonShort(BaseModel):
    id: int = Field(..., description='ID занятия')
    series_id: Optional[int] = Field(default=None, description='ID серии; null — разовое занятие')
    scheduled_start: datetime = Field(..., description='Начало (UTC)')
    duration_minutes: int = Field(..., description='Длительность, минут')
    status: Status = Field(..., description='planned — запланировано, held — проведено, cancelled — отменено')
    detached: bool = Field(..., description='Изменено отдельно от серии')
    topic: str = Field(default='', description='Тема занятия')
    title: str = Field(default='', description='Название серии или пусто')
    participants: list[LessonParticipant] = Field(default_factory=list, description='Участники')


class Lesson(LessonShort):
    original_start: datetime = Field(..., description='Исходное место занятия в серии (UTC)')


class LessonsList(BaseModel):
    lessons: list[LessonShort] = Field(default_factory=list, description='Занятия')


class LessonsResponse(BaseResponse):
    payload: LessonsList = Field(default_factory=LessonsList, description='Список занятий')


class LessonResponse(BaseResponse):
    payload: Lesson | None = Field(default=None, description='Занятие')


class LessonCreate(BaseModel):
    scheduled_start: AwareDatetime = Field(..., description='Начало, ISO 8601 с часовым поясом')
    duration_minutes: int = Field(..., ge=15, le=480, description='Длительность, минут')
    title: str = Field(default='', max_length=200, description='Тема разового занятия')
    student_ids: list[int] = Field(..., min_length=1, description='Ученики')


class LessonUpdate(BaseModel):
    scope: Scope = Field(default='this', description='Область правки полей расписания: только это / это и последующие / все')
    scheduled_start: Optional[AwareDatetime] = Field(default=None, description='Новое начало (перенос)')
    duration_minutes: Optional[int] = Field(default=None, ge=15, le=480, description='Длительность, минут')
    student_ids: Optional[list[int]] = Field(default=None, min_length=1, description='Состав участников')
    topic: Optional[str] = Field(default=None, max_length=300, description='Тема: правится только у этого занятия')


class LessonCancel(BaseModel):
    scope: Literal['this', 'following'] = Field(default='this', description='Отменить только это или это и последующие')

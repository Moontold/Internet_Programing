from datetime import datetime
from typing import Literal, Optional

from pydantic import AwareDatetime, BaseModel, Field

from app.schemas.base import BaseResponse
from app.schemas.file import FileInfo

Scope = Literal['this', 'following', 'all']
Status = Literal['planned', 'held', 'cancelled']
HomeworkStatus = Literal['not_checked', 'done', 'not_done']


class LessonParticipant(BaseModel):
    """Участник глазами смотрящего: чужим детям видно только имя, ученику — не видна ставка."""

    student_id: int = Field(..., description='ID ученика')
    full_name: str = Field(..., description='ФИО ученика')
    price: Optional[int] = Field(default=None, description='Ставка за это занятие, руб.; скрыта от ученика и для чужих')
    homework_status: Optional[HomeworkStatus] = Field(
        default=None, description='Статус домашки: не проверено / сделано / не сделано; скрыт для чужих'
    )
    homework_grade: Optional[int] = Field(default=None, description='Оценка 2..5; скрыта для чужих')


class LessonShort(BaseModel):
    id: int = Field(..., description='ID занятия')
    series_id: Optional[int] = Field(default=None, description='ID серии; null — разовое занятие')
    scheduled_start: datetime = Field(..., description='Начало (UTC)')
    duration_minutes: int = Field(..., description='Длительность, минут')
    status: Status = Field(..., description='planned — запланировано, held — проведено, cancelled — отменено')
    detached: bool = Field(..., description='Изменено отдельно от серии')
    topic: str = Field(default='', description='Тема занятия')
    title: str = Field(default='', description='Название серии или пусто')
    format: Optional[Literal['offline', 'online']] = Field(
        default=None, description='Формат занятия по участникам; null — участники с разным форматом'
    )
    participants: list[LessonParticipant] = Field(default_factory=list, description='Участники')
    homework_pending: bool = Field(
        default=False, description='Родителю и ученику: занятие проведено, а домашка своего ребёнка не отмечена сделанной'
    )
    has_homework: bool = Field(default=False, description='Есть текст домашки или файлы')


class Lesson(LessonShort):
    original_start: datetime = Field(..., description='Исходное место занятия в серии (UTC)')
    homework_text: str = Field(default='', description='Текст домашнего задания')
    homework_saved_at: Optional[datetime] = Field(default=None, description='Когда домашку сохранили последний раз')
    parent_comment: Optional[str] = Field(default=None, description='Комментарий для родителя; ученику не отдаётся')
    tutor_notes: Optional[str] = Field(default=None, description='Заметки репетитора; видны только ему')
    files: list[FileInfo] = Field(default_factory=list, description='Файлы домашнего задания')
    previous_grade: Optional[int] = Field(
        default=None, description='Оценка за предыдущую домашку, если в занятии виден один ученик'
    )


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
    parent_comment: Optional[str] = Field(default=None, max_length=5000, description='Комментарий для родителя')
    tutor_notes: Optional[str] = Field(default=None, max_length=5000, description='Заметки репетитора')


class LessonCancel(BaseModel):
    scope: Literal['this', 'following'] = Field(default='this', description='Отменить только это или это и последующие')


class HomeworkUpdate(BaseModel):
    homework_text: str = Field(default='', max_length=20000, description='Текст домашнего задания')


class ParticipantUpdate(BaseModel):
    homework_status: Optional[HomeworkStatus] = Field(default=None, description='Статус домашки')
    homework_grade: Optional[int] = Field(default=None, ge=2, le=5, description='Оценка 2..5')
    clear_grade: bool = Field(default=False, description='Снять оценку')
    price: Optional[int] = Field(default=None, ge=0, description='Ставка за это занятие, руб.')

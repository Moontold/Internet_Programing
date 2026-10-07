from typing import Literal, Optional

from fastapi import APIRouter, Depends
from pydantic import AwareDatetime

from app.routers.deps import get_lesson_service, require_tutor
from app.schemas.base import OkResponse
from app.schemas.lesson import LessonCancel, LessonCreate, LessonResponse, LessonsResponse, LessonUpdate
from app.services.lesson_service import LessonService

router = APIRouter(prefix='/lessons', tags=['lessons'], dependencies=[Depends(require_tutor)])


@router.get('', response_model=LessonsResponse, summary='Занятия за период (календарь репетитора)')
async def list_lessons(
    start: AwareDatetime,
    end: AwareDatetime,
    student_id: Optional[int] = None,
    service: LessonService = Depends(get_lesson_service),
) -> LessonsResponse:
    return LessonsResponse(payload=await service.list(start=start, end=end, student_id=student_id))


@router.post('', response_model=LessonResponse, summary='Создать разовое занятие')
async def create_lesson(body: LessonCreate, service: LessonService = Depends(get_lesson_service)) -> LessonResponse:
    return LessonResponse(payload=await service.create_single(data=body))


@router.get('/{lesson_id}', response_model=LessonResponse, summary='Занятие')
async def get_lesson(lesson_id: int, service: LessonService = Depends(get_lesson_service)) -> LessonResponse:
    return LessonResponse(payload=await service.get(lesson_id=lesson_id))


@router.patch('/{lesson_id}', response_model=LessonResponse, summary='Перенести или изменить занятие с областью правки')
async def update_lesson(
    lesson_id: int,
    body: LessonUpdate,
    service: LessonService = Depends(get_lesson_service),
) -> LessonResponse:
    return LessonResponse(payload=await service.update(lesson_id=lesson_id, data=body))


@router.post('/{lesson_id}/cancel', response_model=LessonResponse, summary='Отменить занятие')
async def cancel_lesson(
    lesson_id: int,
    body: LessonCancel,
    service: LessonService = Depends(get_lesson_service),
) -> LessonResponse:
    return LessonResponse(payload=await service.cancel(lesson_id=lesson_id, scope=body.scope))


@router.delete('/{lesson_id}', response_model=OkResponse, summary='Удалить занятие')
async def delete_lesson(
    lesson_id: int,
    scope: Literal['this', 'following'] = 'this',
    service: LessonService = Depends(get_lesson_service),
) -> OkResponse:
    await service.delete(lesson_id=lesson_id, scope=scope)
    return OkResponse()

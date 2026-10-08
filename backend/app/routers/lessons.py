from typing import Literal, Optional

from fastapi import APIRouter, Depends, UploadFile
from fastapi import File as FormFile
from pydantic import AwareDatetime

from app.models import User
from app.routers.deps import get_current_user, get_file_service, get_lesson_service, require_tutor
from app.schemas.base import OkResponse
from app.schemas.file import FileResponse
from app.schemas.lesson import (
    HomeworkUpdate,
    LessonCancel,
    LessonCreate,
    LessonResponse,
    LessonsResponse,
    LessonUpdate,
    ParticipantUpdate,
)
from app.services.file_service import FileService
from app.services.lesson_service import LessonService

router = APIRouter(prefix='/lessons', tags=['lessons'])


@router.get('', response_model=LessonsResponse, summary='Занятия за период (календарь репетитора)',
            dependencies=[Depends(require_tutor)])
async def list_lessons(
    start: AwareDatetime,
    end: AwareDatetime,
    student_id: Optional[int] = None,
    service: LessonService = Depends(get_lesson_service),
) -> LessonsResponse:
    return LessonsResponse(payload=await service.list(start=start, end=end, student_id=student_id))


@router.post('', response_model=LessonResponse, summary='Создать разовое занятие', dependencies=[Depends(require_tutor)])
async def create_lesson(body: LessonCreate, service: LessonService = Depends(get_lesson_service)) -> LessonResponse:
    return LessonResponse(payload=await service.create_single(data=body))


@router.get('/{lesson_id}', response_model=LessonResponse, summary='Карточка занятия: поля по роли смотрящего')
async def get_lesson(
    lesson_id: int,
    user: User = Depends(get_current_user),
    service: LessonService = Depends(get_lesson_service),
) -> LessonResponse:
    access = await service.access_for(user=user)
    return LessonResponse(payload=await service.get(access=access, lesson_id=lesson_id))


@router.patch('/{lesson_id}', response_model=LessonResponse, summary='Перенести или изменить занятие с областью правки',
              dependencies=[Depends(require_tutor)])
async def update_lesson(
    lesson_id: int,
    body: LessonUpdate,
    service: LessonService = Depends(get_lesson_service),
) -> LessonResponse:
    return LessonResponse(payload=await service.update(lesson_id=lesson_id, data=body))


@router.post('/{lesson_id}/cancel', response_model=LessonResponse, summary='Отменить занятие',
             dependencies=[Depends(require_tutor)])
async def cancel_lesson(
    lesson_id: int,
    body: LessonCancel,
    service: LessonService = Depends(get_lesson_service),
) -> LessonResponse:
    return LessonResponse(payload=await service.cancel(lesson_id=lesson_id, scope=body.scope))


@router.delete('/{lesson_id}', response_model=OkResponse, summary='Удалить занятие', dependencies=[Depends(require_tutor)])
async def delete_lesson(
    lesson_id: int,
    scope: Literal['this', 'following'] = 'this',
    service: LessonService = Depends(get_lesson_service),
) -> OkResponse:
    await service.delete(lesson_id=lesson_id, scope=scope)
    return OkResponse()


@router.patch('/{lesson_id}/homework', response_model=LessonResponse, summary='Сохранить домашнее задание',
              dependencies=[Depends(require_tutor)])
async def save_homework(
    lesson_id: int,
    body: HomeworkUpdate,
    service: LessonService = Depends(get_lesson_service),
) -> LessonResponse:
    return LessonResponse(payload=await service.save_homework(lesson_id=lesson_id, text=body.homework_text))


@router.patch('/{lesson_id}/students/{student_id}', response_model=LessonResponse,
              summary='Статус домашки, оценка и ставка участника', dependencies=[Depends(require_tutor)])
async def update_participant(
    lesson_id: int,
    student_id: int,
    body: ParticipantUpdate,
    service: LessonService = Depends(get_lesson_service),
) -> LessonResponse:
    return LessonResponse(
        payload=await service.update_participant(lesson_id=lesson_id, student_id=student_id, data=body)
    )


@router.post('/{lesson_id}/files', response_model=FileResponse, summary='Прикрепить файл к домашке')
async def upload_lesson_file(
    lesson_id: int,
    file: UploadFile = FormFile(..., description='Файл, не больше MAX_UPLOAD_MB'),
    user: User = Depends(require_tutor),
    service: FileService = Depends(get_file_service),
) -> FileResponse:
    return FileResponse(payload=await service.upload_to_lesson(lesson_id=lesson_id, upload=file, user_id=user.id))


@router.delete('/{lesson_id}/files/{file_id}', response_model=OkResponse, summary='Открепить и удалить файл',
               dependencies=[Depends(require_tutor)])
async def delete_lesson_file(
    lesson_id: int,
    file_id: int,
    service: FileService = Depends(get_file_service),
) -> OkResponse:
    await service.remove_from_lesson(lesson_id=lesson_id, file_id=file_id)
    return OkResponse()

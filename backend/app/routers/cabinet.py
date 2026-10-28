from fastapi import APIRouter, Depends
from pydantic import AwareDatetime

from app.models import User
from app.routers.deps import get_cabinet_service, require_parent, require_student
from app.schemas.cabinet import ChildrenResponse, SeriesListResponse
from app.schemas.lesson import LessonsResponse
from app.services.cabinet_service import CabinetService

router = APIRouter(tags=['cabinet'])


@router.get('/parent/children', response_model=ChildrenResponse, summary='Кабинет родителя: дети со статистикой')
async def parent_children(
    user: User = Depends(require_parent),
    service: CabinetService = Depends(get_cabinet_service),
) -> ChildrenResponse:
    return ChildrenResponse(payload=await service.children(user=user))


@router.get('/parent/children/{student_id}/lessons', response_model=LessonsResponse, summary='Занятия своего ребёнка')
async def parent_child_lessons(
    student_id: int,
    start: AwareDatetime,
    end: AwareDatetime,
    user: User = Depends(require_parent),
    service: CabinetService = Depends(get_cabinet_service),
) -> LessonsResponse:
    return LessonsResponse(payload=await service.child_lessons(user=user, student_id=student_id, start=start, end=end))


@router.get('/student/lessons', response_model=LessonsResponse, summary='Кабинет ученика: свои занятия и домашки')
async def student_lessons(
    start: AwareDatetime,
    end: AwareDatetime,
    user: User = Depends(require_student),
    service: CabinetService = Depends(get_cabinet_service),
) -> LessonsResponse:
    return LessonsResponse(payload=await service.student_lessons(user=user, start=start, end=end))


@router.get('/student/series', response_model=SeriesListResponse, summary='Кабинет ученика: регулярное расписание')
async def student_series(
    user: User = Depends(require_student),
    service: CabinetService = Depends(get_cabinet_service),
) -> SeriesListResponse:
    return SeriesListResponse(payload=await service.student_series(user=user))

from typing import Optional

from fastapi import APIRouter, Depends

from app.routers.deps import get_student_service, require_tutor
from app.schemas.auth import PasswordPayload, PasswordResponse
from app.schemas.student import (
    StudentCreate,
    StudentCreatedResponse,
    StudentResponse,
    StudentsResponse,
    StudentUpdate,
)
from app.services.student_service import StudentService

router = APIRouter(prefix='/students', tags=['students'], dependencies=[Depends(require_tutor)])


@router.get('', response_model=StudentsResponse, summary='Список учеников')
async def list_students(
    is_active: Optional[bool] = None,
    service: StudentService = Depends(get_student_service),
) -> StudentsResponse:
    return StudentsResponse(payload=await service.list(is_active=is_active))


@router.post('', response_model=StudentCreatedResponse, summary='Создать ученика с учёткой')
async def create_student(
    body: StudentCreate,
    service: StudentService = Depends(get_student_service),
) -> StudentCreatedResponse:
    return StudentCreatedResponse(payload=await service.create(data=body))


@router.get('/{student_id}', response_model=StudentResponse, summary='Карточка ученика')
async def get_student(student_id: int, service: StudentService = Depends(get_student_service)) -> StudentResponse:
    return StudentResponse(payload=await service.get(student_id=student_id))


@router.patch('/{student_id}', response_model=StudentResponse, summary='Изменить, перепривязать или деактивировать ученика')
async def update_student(
    student_id: int,
    body: StudentUpdate,
    service: StudentService = Depends(get_student_service),
) -> StudentResponse:
    return StudentResponse(payload=await service.update(student_id=student_id, data=body))


@router.post('/{student_id}/reset-password', response_model=PasswordResponse, summary='Сбросить пароль ученика')
async def reset_student_password(
    student_id: int,
    service: StudentService = Depends(get_student_service),
) -> PasswordResponse:
    password = await service.reset_password(student_id=student_id)
    return PasswordResponse(payload=PasswordPayload(password=password))

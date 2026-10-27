from typing import Optional

from fastapi import APIRouter, Depends

from app.routers.deps import get_parent_service, require_tutor
from app.schemas.auth import PasswordPayload, PasswordResponse
from app.schemas.parent import ParentCreate, ParentCreatedResponse, ParentResponse, ParentsResponse, ParentUpdate
from app.services.parent_service import ParentService

router = APIRouter(prefix='/parents', tags=['parents'], dependencies=[Depends(require_tutor)])


@router.get('', response_model=ParentsResponse, summary='Список родителей')
async def list_parents(
    is_active: Optional[bool] = None,
    service: ParentService = Depends(get_parent_service),
) -> ParentsResponse:
    return ParentsResponse(payload=await service.list(is_active=is_active))


@router.post('', response_model=ParentCreatedResponse, summary='Создать родителя с учёткой')
async def create_parent(
    body: ParentCreate,
    service: ParentService = Depends(get_parent_service),
) -> ParentCreatedResponse:
    return ParentCreatedResponse(payload=await service.create(data=body))


@router.get('/{parent_id}', response_model=ParentResponse, summary='Карточка родителя с детьми')
async def get_parent(parent_id: int, service: ParentService = Depends(get_parent_service)) -> ParentResponse:
    return ParentResponse(payload=await service.get(parent_id=parent_id))


@router.patch('/{parent_id}', response_model=ParentResponse, summary='Изменить или деактивировать родителя')
async def update_parent(
    parent_id: int,
    body: ParentUpdate,
    service: ParentService = Depends(get_parent_service),
) -> ParentResponse:
    return ParentResponse(payload=await service.update(parent_id=parent_id, data=body))


@router.post('/{parent_id}/reset-password', response_model=PasswordResponse, summary='Сбросить пароль родителя')
async def reset_parent_password(
    parent_id: int,
    service: ParentService = Depends(get_parent_service),
) -> PasswordResponse:
    password = await service.reset_password(parent_id=parent_id)
    return PasswordResponse(payload=PasswordPayload(password=password))

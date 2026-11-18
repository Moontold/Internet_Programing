from typing import Optional

from fastapi import APIRouter, Depends

from app.routers.deps import get_finance_service, get_notification_service, get_parent_service, require_tutor
from app.schemas.auth import PasswordPayload, PasswordResponse
from app.schemas.base import OkResponse
from app.schemas.finance import ParentFinanceResponse, PaymentCreate, PaymentResponse
from app.schemas.parent import ParentCreate, ParentCreatedResponse, ParentResponse, ParentsResponse, ParentUpdate
from app.services.finance_service import FinanceService
from app.services.notification_service import NotificationService
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


@router.get('/{parent_id}/finance', response_model=ParentFinanceResponse, summary='Финансы родителя: баланс, неоплаченные, платежи')
async def parent_finance(
    parent_id: int,
    service: FinanceService = Depends(get_finance_service),
) -> ParentFinanceResponse:
    return ParentFinanceResponse(payload=await service.parent_finance(parent_id=parent_id))


@router.post('/{parent_id}/payments', response_model=PaymentResponse, summary='Внести платёж')
async def add_payment(
    parent_id: int,
    body: PaymentCreate,
    service: FinanceService = Depends(get_finance_service),
) -> PaymentResponse:
    return PaymentResponse(payload=await service.add_payment(parent_id=parent_id, data=body))


@router.post('/{parent_id}/remind-payment', response_model=OkResponse, summary='Напомнить родителю об оплате')
async def remind_payment(
    parent_id: int,
    service: NotificationService = Depends(get_notification_service),
) -> OkResponse:
    await service.remind_payment(parent_id=parent_id)
    return OkResponse()

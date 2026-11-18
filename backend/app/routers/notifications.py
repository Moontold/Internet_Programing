from fastapi import APIRouter, Depends, Query

from app.models import User
from app.routers.deps import get_current_user, get_notification_service
from app.schemas.base import OkResponse
from app.schemas.notification import NotificationsResponse
from app.services.notification_service import NotificationService

router = APIRouter(prefix='/notifications', tags=['notifications'])


@router.get('', response_model=NotificationsResponse, summary='Колокольчик: последние уведомления и счётчик')
async def list_notifications(
    limit: int = Query(default=20, ge=1, le=100, description='Сколько последних уведомлений вернуть'),
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> NotificationsResponse:
    return NotificationsResponse(payload=await service.feed(user_id=user.id, limit=limit))


@router.post('/read', response_model=OkResponse, summary='Отметить все уведомления прочитанными')
async def mark_read(
    user: User = Depends(get_current_user),
    service: NotificationService = Depends(get_notification_service),
) -> OkResponse:
    await service.mark_read(user_id=user.id)
    return OkResponse()

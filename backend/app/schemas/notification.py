from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse


class NotificationItem(BaseModel):
    id: int = Field(..., description='ID уведомления')
    kind: str = Field(..., description='Вид: lesson_soon, lesson_soon_tutor, homework, debt, lesson_cancelled, '
                                        'lesson_moved, schedule_changed, homework_missing, payment_reminder')
    title: str = Field(..., description='Текст уведомления')
    body: str = Field(default='', description='Подробности, обычно пусто')
    lesson_id: Optional[int] = Field(default=None, description='Связанное занятие, если есть')
    created_at: datetime = Field(..., description='Когда создано (UTC)')
    read: bool = Field(default=False, description='Уже прочитано')


class NotificationsList(BaseModel):
    items: list[NotificationItem] = Field(default_factory=list, description='Последние уведомления, новые первыми')
    unread_count: int = Field(default=0, description='Число непрочитанных')


class NotificationsResponse(BaseResponse):
    payload: NotificationsList = Field(default_factory=NotificationsList, description='Уведомления')

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Notification(Base):
    """Уведомление — единый источник правды для колокольчика на сайте и бота ВКонтакте.

    dedupe_key уникален: повторное событие с тем же ключом новой записи не создаёт;
    у намеренно повторяемых видов ключа нет. Поля vk_* — состояние доставки во ВКонтакте.
    """

    __tablename__ = 'notifications'
    __table_args__ = (UniqueConstraint('dedupe_key', name='uq_notifications_dedupe_key'),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False, default='')
    lesson_id: Mapped[Optional[int]] = mapped_column(ForeignKey('lessons.id', ondelete='SET NULL'), nullable=True)
    dedupe_key: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    vk_state: Mapped[str] = mapped_column(String(16), nullable=False, default='pending', index=True)
    vk_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    vk_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

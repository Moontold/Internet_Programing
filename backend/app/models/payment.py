from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Payment(Base):
    """Платёж родителя в целых рублях: плюс — оплата, минус — возврат или исправление.

    Баланс и признак «оплачено» не хранятся — их считает app.core.finance при каждом запросе.
    """

    __tablename__ = 'payments'

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int] = mapped_column(
        ForeignKey('parents.id', ondelete='CASCADE'), nullable=False, index=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    paid_on: Mapped[date] = mapped_column(Date, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False, default='')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

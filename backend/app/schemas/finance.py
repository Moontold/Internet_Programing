from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse
from app.schemas.parent import ParentShort


class Payment(BaseModel):
    id: int = Field(..., description='ID платежа')
    amount: int = Field(..., description='Сумма, руб.; минус — возврат или исправление')
    paid_on: date = Field(..., description='Дата платежа')
    comment: str = Field(default='', description='Комментарий')
    created_at: datetime = Field(..., description='Когда внесён (UTC)')


class PaymentCreate(BaseModel):
    amount: int = Field(..., description='Сумма, целые рубли: не 0, по модулю не больше 1 000 000')
    paid_on: date = Field(..., description='Дата платежа, не позже сегодняшнего дня')
    comment: str = Field(default='', max_length=500, description='Комментарий')


class PaymentUpdate(BaseModel):
    amount: Optional[int] = Field(default=None, description='Сумма, целые рубли: не 0, по модулю не больше 1 000 000')
    paid_on: Optional[date] = Field(default=None, description='Дата платежа, не позже сегодняшнего дня')
    comment: Optional[str] = Field(default=None, max_length=500, description='Комментарий')


class UnpaidCharge(BaseModel):
    lesson_id: int = Field(..., description='ID занятия')
    student_id: int = Field(..., description='ID ученика')
    student_name: str = Field(..., description='ФИО ученика')
    held_at: datetime = Field(..., description='Начало занятия (UTC)')
    price: int = Field(..., description='Ставка, руб.')


class ParentBalance(BaseModel):
    balance: int = Field(default=0, description='Платежи минус начисления, руб.: минус — долг, плюс — предоплата')
    debt: int = Field(default=0, description='Долг = max(0, −balance)')


class ParentFinance(ParentBalance):
    unpaid: list[UnpaidCharge] = Field(default_factory=list, description='Неоплаченные проведённые занятия, ранние первыми')
    payments: list[Payment] = Field(default_factory=list, description='Платежи, новые первыми')


class ParentAccountRow(ParentBalance):
    parent: ParentShort = Field(..., description='Родитель')
    unpaid_count: int = Field(default=0, description='Число неоплаченных участий в занятиях')


class FinanceSummary(BaseModel):
    parents: list[ParentAccountRow] = Field(default_factory=list, description='Родители: должники первыми')
    total_debt: int = Field(default=0, description='Σ долгов')
    total_prepaid: int = Field(default=0, description='Σ предоплат (положительных балансов)')


class MonthStatsItem(BaseModel):
    month: str = Field(..., description='YYYY-MM')
    lessons_count: int = Field(default=0, description='Проведено занятий; групповое — один раз')
    earned: int = Field(default=0, description='Наработано: Σ ставок участников проведённых занятий, руб.')
    received: int = Field(default=0, description='Получено: Σ платежей по дате платежа, руб.')


class MonthlyStats(BaseModel):
    year: int = Field(..., description='Год')
    months: list[MonthStatsItem] = Field(default_factory=list, description='Двенадцать месяцев')


class PaymentResponse(BaseResponse):
    payload: Payment | None = Field(default=None, description='Платёж')


class ParentFinanceResponse(BaseResponse):
    payload: ParentFinance = Field(default_factory=ParentFinance, description='Финансы родителя')


class ParentBalanceResponse(BaseResponse):
    payload: ParentBalance = Field(default_factory=ParentBalance, description='Свой баланс')


class FinanceSummaryResponse(BaseResponse):
    payload: FinanceSummary = Field(default_factory=FinanceSummary, description='Сводка')


class MonthlyStatsResponse(BaseResponse):
    payload: MonthlyStats | None = Field(default=None, description='Заработок по месяцам')

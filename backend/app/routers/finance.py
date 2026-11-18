from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends

from app.config import settings
from app.routers.deps import get_finance_service, require_tutor
from app.schemas.base import OkResponse
from app.schemas.finance import FinanceSummaryResponse, MonthlyStatsResponse, PaymentResponse, PaymentUpdate
from app.services.finance_service import FinanceService

router = APIRouter(tags=['finance'], dependencies=[Depends(require_tutor)])


@router.get('/finance/summary', response_model=FinanceSummaryResponse, summary='Итоги: долги, предоплаты, родители')
async def finance_summary(service: FinanceService = Depends(get_finance_service)) -> FinanceSummaryResponse:
    return FinanceSummaryResponse(payload=await service.summary())


@router.get('/finance/stats', response_model=MonthlyStatsResponse, summary='Заработок по месяцам года')
async def finance_stats(
    year: Optional[int] = None,
    service: FinanceService = Depends(get_finance_service),
) -> MonthlyStatsResponse:
    current = year or datetime.now(timezone.utc).astimezone(settings.tz).year
    return MonthlyStatsResponse(payload=await service.stats(year=current))


@router.patch('/payments/{payment_id}', response_model=PaymentResponse, summary='Изменить платёж')
async def update_payment(
    payment_id: int,
    body: PaymentUpdate,
    service: FinanceService = Depends(get_finance_service),
) -> PaymentResponse:
    return PaymentResponse(payload=await service.update_payment(payment_id=payment_id, data=body))


@router.delete('/payments/{payment_id}', response_model=OkResponse, summary='Удалить платёж')
async def delete_payment(payment_id: int, service: FinanceService = Depends(get_finance_service)) -> OkResponse:
    await service.delete_payment(payment_id=payment_id)
    return OkResponse()

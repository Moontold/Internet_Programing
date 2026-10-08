from fastapi import APIRouter, Depends

from app.routers.deps import get_series_service, require_tutor
from app.schemas.series import SeriesCreate, SeriesResponse, SeriesStop, SeriesUpdate
from app.services.series_service import SeriesService

router = APIRouter(prefix='/series', tags=['series'], dependencies=[Depends(require_tutor)])


@router.post('', response_model=SeriesResponse, summary='Создать серию: занятия на горизонт порождаются сразу')
async def create_series(body: SeriesCreate, service: SeriesService = Depends(get_series_service)) -> SeriesResponse:
    return SeriesResponse(payload=await service.create(data=body))


@router.patch('/{series_id}', response_model=SeriesResponse, summary='Изменить серию (режим «все занятия»)')
async def update_series(
    series_id: int,
    body: SeriesUpdate,
    service: SeriesService = Depends(get_series_service),
) -> SeriesResponse:
    return SeriesResponse(payload=await service.update_all(series_id=series_id, data=body))


@router.post('/{series_id}/stop', response_model=SeriesResponse, summary='Остановить серию с даты')
async def stop_series(
    series_id: int,
    body: SeriesStop,
    service: SeriesService = Depends(get_series_service),
) -> SeriesResponse:
    return SeriesResponse(payload=await service.stop(series_id=series_id, from_date=body.from_date))

from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse


class HealthStatus(BaseModel):
    service: str = Field(..., description='Имя сервиса')
    version: str = Field(..., description='Версия приложения')
    database: str = Field(..., description='Состояние подключения к БД: ok или сообщение об ошибке')
    timezone: str = Field(..., description='Часовой пояс установки')


class HealthResponse(BaseResponse):
    payload: HealthStatus = Field(..., description='Состояние сервиса')

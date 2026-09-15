from typing import Any, Optional

from pydantic import BaseModel, Field


class BaseResponse(BaseModel):
    """Единый конверт ответа API: все роутеры отвечают только им."""

    error: bool = Field(default=False, description='Произошла ли ошибка')
    message: str = Field(default='OK', description='Описание ошибки, если она произошла')
    payload: Optional[Any] | None = Field(default=None, description='Полезная нагрузка ответа')


class OkResponse(BaseResponse):
    payload: None = Field(default=None, description='Пустая нагрузка')

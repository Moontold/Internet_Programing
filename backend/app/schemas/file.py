from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.base import BaseResponse


class FileInfo(BaseModel):
    id: int = Field(..., description='ID файла: скачивание по GET /api/files/{id}')
    original_name: str = Field(..., description='Исходное имя файла')
    size: int = Field(..., description='Размер, байт')
    mime: str = Field(..., description='MIME-тип')
    created_at: datetime = Field(..., description='Когда загружен')


class FileResponse(BaseResponse):
    payload: FileInfo | None = Field(default=None, description='Загруженный файл')

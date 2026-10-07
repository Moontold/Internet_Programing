import re
import uuid
from dataclasses import dataclass
from pathlib import Path

import aiofiles
import aiofiles.os
from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.errors import AppError
from app.core.projection import Access, to_file_info
from app.models import File, LessonStatus
from app.repositories.file_repository import FileRepository
from app.repositories.lesson_repository import LessonRepository
from app.schemas.file import FileInfo

CHUNK = 1024 * 1024
# Открывать прямо в браузере можно только то, что не исполняет скриптов на нашем домене
INLINE_SAFE_MIME = {'application/pdf', 'image/png', 'image/jpeg', 'image/gif', 'image/webp', 'text/plain'}


@dataclass(frozen=True)
class Download:
    path: Path
    filename: str
    mime: str
    inline: bool


def _display_name(filename: str | None) -> str:
    """Имя для показа: без пути, который может прислать браузер."""
    name = re.split(r'[\\/]', filename or '')[-1].strip()
    return (name or 'file')[:255]


def _safe_suffix(name: str) -> str:
    suffix = Path(name).suffix
    return suffix.lower() if re.fullmatch(r'\.[A-Za-z0-9]{1,10}', suffix) else ''


class FileService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._files = FileRepository(db=db)
        self._lessons = LessonRepository(db=db)
        self._root = Path(settings.upload_dir)

    def _path(self, stored_name: str) -> Path:
        return self._root / stored_name

    async def _write(self, upload: UploadFile, stored_name: str) -> int:
        """Пишет загрузку на диск кусками и обрывает её на превышении лимита."""
        limit = settings.max_upload_mb * 1024 * 1024
        self._root.mkdir(parents=True, exist_ok=True)
        path = self._path(stored_name=stored_name)
        size = 0
        async with aiofiles.open(path, 'wb') as target:
            while chunk := await upload.read(CHUNK):
                size += len(chunk)
                if size > limit:
                    break
                await target.write(chunk)
        if size > limit:
            await aiofiles.os.remove(path)
            raise AppError(f'Файл больше {settings.max_upload_mb} МБ')
        return size

    async def _remove_from_disk(self, stored_name: str) -> None:
        path = self._path(stored_name=stored_name)
        if path.exists():
            await aiofiles.os.remove(path)

    async def upload_to_lesson(self, lesson_id: int, upload: UploadFile, user_id: int) -> FileInfo:
        lesson = await self._lessons.get(lesson_id=lesson_id)
        if lesson is None:
            raise AppError('Занятие не найдено')
        if lesson.status == LessonStatus.CANCELLED:
            raise AppError('Отменённое занятие нельзя редактировать')
        original = _display_name(filename=upload.filename)
        stored_name = uuid.uuid4().hex + _safe_suffix(name=original)
        size = await self._write(upload=upload, stored_name=stored_name)
        try:
            file = await self._files.add(file=File(
                original_name=original,
                stored_name=stored_name,
                size=size,
                mime=(upload.content_type or 'application/octet-stream')[:100],
                uploaded_by=user_id,
            ))
            lesson.files.append(file)
            await self._db.commit()
        except Exception:
            await self._remove_from_disk(stored_name=stored_name)
            raise
        return to_file_info(file=file)

    async def remove_from_lesson(self, lesson_id: int, file_id: int) -> None:
        lesson = await self._lessons.get(lesson_id=lesson_id)
        if lesson is None:
            raise AppError('Занятие не найдено')
        file = next((item for item in lesson.files if item.id == file_id), None)
        if file is None:
            raise AppError('Файл не прикреплён к этому занятию')
        lesson.files.remove(file)
        await self._files.delete(file=file)
        await self._db.commit()
        await self._remove_from_disk(stored_name=file.stored_name)

    async def open_for_download(self, access: Access, file_id: int, inline: bool) -> Download:
        """Файл домашки отдаётся репетитору и тем, кому доступно занятие: участнику и его родителю."""
        file = await self._files.get(file_id=file_id)
        lesson = await self._lessons.get_by_file_id(file_id=file_id) if file is not None else None
        if file is None or lesson is None:
            raise AppError('Файл не найден', status_code=404)
        if not access.allows(lesson=lesson):
            raise AppError('Нет доступа к файлу', status_code=403)
        path = self._path(stored_name=file.stored_name)
        if not path.exists():
            raise AppError('Файл отсутствует в хранилище', status_code=404)
        return Download(
            path=path,
            filename=file.original_name,
            mime=file.mime,
            inline=inline and file.mime in INLINE_SAFE_MIME,
        )

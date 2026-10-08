from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import File


class FileRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get(self, file_id: int) -> Optional[File]:
        return await self._db.get(File, file_id)

    async def add(self, file: File) -> File:
        self._db.add(file)
        await self._db.flush()
        return file

    async def delete(self, file: File) -> None:
        await self._db.delete(file)
        await self._db.flush()

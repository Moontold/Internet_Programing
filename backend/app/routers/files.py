from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse as StarletteFileResponse

from app.models import User
from app.routers.deps import get_current_user, get_file_service, get_lesson_service
from app.services.file_service import FileService
from app.services.lesson_service import LessonService

router = APIRouter(prefix='/files', tags=['files'])


@router.get('/{file_id}', summary='Скачать файл: только тем, кому доступно занятие')
async def download_file(
    file_id: int,
    inline: bool = False,
    user: User = Depends(get_current_user),
    files: FileService = Depends(get_file_service),
    lessons: LessonService = Depends(get_lesson_service),
) -> StarletteFileResponse:
    access = await lessons.access_for(user=user)
    download = await files.open_for_download(access=access, file_id=file_id, inline=inline)
    return StarletteFileResponse(
        path=download.path,
        media_type=download.mime if download.inline else 'application/octet-stream',
        filename=download.filename,
        content_disposition_type='inline' if download.inline else 'attachment',
        headers={'X-Content-Type-Options': 'nosniff', 'Cache-Control': 'private, no-store'},
    )

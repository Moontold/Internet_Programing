from datetime import datetime

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String, Table, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

lesson_files = Table(
    'lesson_files',
    Base.metadata,
    Column('lesson_id', ForeignKey('lessons.id', ondelete='CASCADE'), primary_key=True),
    Column('file_id', ForeignKey('files.id', ondelete='CASCADE'), primary_key=True),
)


class File(Base):
    """Загруженный файл: байты лежат в томе UPLOAD_DIR под именем stored_name."""

    __tablename__ = 'files'

    id: Mapped[int] = mapped_column(primary_key=True)
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_name: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    mime: Mapped[str] = mapped_column(String(100), nullable=False, default='application/octet-stream')
    uploaded_by: Mapped[int] = mapped_column(ForeignKey('users.id'), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

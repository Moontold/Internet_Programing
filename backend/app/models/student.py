from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.parent import Parent
    from app.models.user import User


class Student(Base):
    """Ученик: всегда привязан к одному родителю, ставка за занятие в целых рублях."""

    __tablename__ = 'students'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), unique=True, nullable=False)
    parent_id: Mapped[int] = mapped_column(ForeignKey('parents.id'), nullable=False, index=True)
    grade: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    grade_note: Mapped[str] = mapped_column(String(100), nullable=False, default='')
    format: Mapped[str] = mapped_column(String(16), nullable=False)
    price_per_lesson: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped['User'] = relationship(lazy='joined')
    parent: Mapped['Parent'] = relationship(back_populates='children')

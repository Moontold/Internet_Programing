from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.student import Student
    from app.models.user import User


class Parent(Base):
    """Родитель-плательщик: учётка в users плюс контакты. Детей может быть несколько."""

    __tablename__ = 'parents'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), unique=True, nullable=False)
    phone: Mapped[str] = mapped_column(String(32), nullable=False, default='')
    contacts_note: Mapped[str] = mapped_column(Text, nullable=False, default='')

    user: Mapped['User'] = relationship(lazy='joined')
    children: Mapped[list['Student']] = relationship(back_populates='parent', order_by='Student.id')

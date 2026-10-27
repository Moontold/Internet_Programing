from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import AppError
from app.core.security import generate_temp_password, hash_password
from app.models import Parent, Role, User
from app.repositories.parent_repository import ParentRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository
from app.schemas import parent as schemas


def to_parent_short(parent: Parent) -> schemas.ParentShort:
    return schemas.ParentShort(id=parent.id, full_name=parent.user.full_name, phone=parent.phone)


def to_parent_schema(parent: Parent) -> schemas.Parent:
    return schemas.Parent(
        id=parent.id,
        full_name=parent.user.full_name,
        phone=parent.phone,
        login=parent.user.login,
        contacts_note=parent.contacts_note,
        is_active=parent.user.is_active,
        children=[
            schemas.ChildShort(
                id=child.id,
                full_name=child.user.full_name,
                grade=child.grade,
                is_active=child.is_active,
            )
            for child in parent.children
        ],
    )


class ParentService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._parents = ParentRepository(db=db)
        self._users = UserRepository(db=db)
        self._sessions = SessionRepository(db=db)

    async def _get_or_raise(self, parent_id: int) -> Parent:
        parent = await self._parents.get(parent_id=parent_id)
        if parent is None:
            raise AppError('Родитель не найден')
        return parent

    async def list(self, is_active: Optional[bool]) -> schemas.ParentsList:
        parents = await self._parents.list_all(is_active=is_active)
        return schemas.ParentsList(parents=[to_parent_schema(parent=item) for item in parents])

    async def get(self, parent_id: int) -> schemas.Parent:
        return to_parent_schema(parent=await self._get_or_raise(parent_id=parent_id))

    async def create(self, data: schemas.ParentCreate) -> schemas.ParentCreated:
        if await self._users.login_exists(login=data.login):
            raise AppError('Такой логин уже занят')
        user = await self._users.add(user=User(
            login=data.login,
            password_hash=hash_password(password=data.password),
            role=Role.PARENT,
            full_name=data.full_name,
        ))
        parent = await self._parents.add(parent=Parent(
            user_id=user.id,
            phone=data.phone,
            contacts_note=data.contacts_note,
        ))
        await self._db.commit()
        return schemas.ParentCreated(
            parent=await self.get(parent_id=parent.id),
            password=data.password,
        )

    async def update(self, parent_id: int, data: schemas.ParentUpdate) -> schemas.Parent:
        parent = await self._get_or_raise(parent_id=parent_id)
        if data.full_name is not None:
            parent.user.full_name = data.full_name
        if data.phone is not None:
            parent.phone = data.phone
        if data.contacts_note is not None:
            parent.contacts_note = data.contacts_note
        if data.is_active is not None:
            parent.user.is_active = data.is_active
            if not data.is_active:
                await self._sessions.delete_for_user(user_id=parent.user_id)
        await self._db.commit()
        return to_parent_schema(parent=parent)

    async def reset_password(self, parent_id: int) -> str:
        """Генерирует новый пароль и завершает все сессии родителя."""
        parent = await self._get_or_raise(parent_id=parent_id)
        password = generate_temp_password()
        parent.user.password_hash = hash_password(password=password)
        await self._sessions.delete_for_user(user_id=parent.user_id)
        await self._db.commit()
        return password

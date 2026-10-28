import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.core.errors import AppError
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    generate_session_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models import Role, Session, User
from app.repositories.login_attempt_repository import LoginAttemptRepository
from app.repositories.session_repository import SessionRepository
from app.repositories.user_repository import UserRepository

MAX_FAILED_ATTEMPTS = 10
FAILED_WINDOW = timedelta(minutes=15)
# Срок сессии продлевается не чаще раза в час, чтобы не писать в БД на каждый запрос
EXTEND_THRESHOLD = timedelta(hours=1)


@dataclass(frozen=True)
class LoginResult:
    user: User
    token: str


@dataclass(frozen=True)
class ResolvedSession:
    user: User
    extended: bool  # срок сессии продлён: cookie нужно выставить заново


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._log = logging.getLogger('AuthService')
        self._users = UserRepository(db=db)
        self._sessions = SessionRepository(db=db)
        self._attempts = LoginAttemptRepository(db=db)

    async def login(self, login: str, password: str) -> LoginResult:
        now = datetime.now(timezone.utc)
        failed = await self._attempts.count_failed_since(login=login, since=now - FAILED_WINDOW)
        if failed >= MAX_FAILED_ATTEMPTS:
            raise AppError('Слишком много неудачных попыток входа. Попробуйте через 15 минут.')

        user = await self._users.get_by_login(login=login)
        password_ok = verify_password(
            password=password,
            password_hash=user.password_hash if user is not None else DUMMY_PASSWORD_HASH,
        )
        if user is None or not password_ok:
            await self._fail(login=login)
            raise AppError('Неверный логин или пароль')
        if not user.is_active:
            await self._fail(login=login)
            raise AppError('Учётная запись отключена. Обратитесь к репетитору.')

        await self._attempts.add(login=login, success=True)
        token = generate_session_token()
        await self._sessions.add(session=Session(
            user_id=user.id,
            token_hash=hash_token(token=token),
            expires_at=now + timedelta(days=settings.session_days),
        ))
        await self._db.commit()
        return LoginResult(user=user, token=token)

    async def _fail(self, login: str) -> None:
        await self._attempts.add(login=login, success=False)
        await self._db.commit()

    async def logout(self, token: str) -> None:
        await self._sessions.delete_by_token_hash(token_hash=hash_token(token=token))
        await self._db.commit()

    async def resolve_session(self, token: str) -> Optional[ResolvedSession]:
        session = await self._sessions.get_by_token_hash(token_hash=hash_token(token=token))
        if session is None:
            return None
        now = datetime.now(timezone.utc)
        if session.expires_at <= now:
            await self._sessions.delete_by_token_hash(token_hash=session.token_hash)
            await self._db.commit()
            return None
        user = await self._users.get_by_id(user_id=session.user_id)
        if user is None or not user.is_active:
            return None

        full_life = timedelta(days=settings.session_days)
        if session.expires_at - now >= full_life - EXTEND_THRESHOLD:
            return ResolvedSession(user=user, extended=False)
        session.expires_at = now + full_life
        await self._db.commit()
        return ResolvedSession(user=user, extended=True)

    async def change_password(self, user: User, old_password: str, new_password: str, current_token: str) -> None:
        """Меняет пароль и завершает все сессии пользователя, кроме текущей."""
        if not verify_password(password=old_password, password_hash=user.password_hash):
            raise AppError('Текущий пароль указан неверно')
        user.password_hash = hash_password(password=new_password)
        await self._sessions.delete_for_user(user_id=user.id, keep_token_hash=hash_token(token=current_token))
        await self._db.commit()

    async def ensure_tutor_exists(self) -> None:
        """Первый старт: создаёт учётку репетитора из TUTOR_LOGIN / TUTOR_PASSWORD / TUTOR_NAME."""
        if await self._users.get_tutor() is not None:
            return
        taken = await self._users.get_by_login(login=settings.tutor_login)
        if taken is not None:
            raise RuntimeError(
                f'Логин {settings.tutor_login} уже занят пользователем с ролью {taken.role}: '
                f'задайте в .env другой TUTOR_LOGIN'
            )
        await self._users.add(user=User(
            login=settings.tutor_login,
            password_hash=hash_password(password=settings.tutor_password),
            role=Role.TUTOR,
            full_name=settings.tutor_name,
            is_active=True,
        ))
        await self._db.commit()
        self._log.info('Tutor account created: %s', settings.tutor_login)

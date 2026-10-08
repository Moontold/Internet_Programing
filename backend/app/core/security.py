"""Хеши паролей и токены сессий. Чистые функции: без БД и сети."""
import hashlib
import secrets

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()
_TEMP_ALPHABET = 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'

# Хеш случайной строки: с ним сверяется пароль, когда логина нет, чтобы ответ
# по несуществующему логину занимал столько же времени, сколько по существующему.
DUMMY_PASSWORD_HASH = _hasher.hash(secrets.token_urlsafe(16))


def hash_password(password: str) -> str:
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False


def generate_session_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode('utf-8')).hexdigest()


def generate_temp_password(length: int = 10) -> str:
    """Разовый пароль при сбросе: буквы и цифры без похожих символов (0/O, 1/l/I)."""
    return ''.join(secrets.choice(_TEMP_ALPHABET) for _ in range(length))

from zoneinfo import ZoneInfo

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения: читаются из .env, в коде значений по умолчанию для секретов нет."""

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    postgres_db: str
    postgres_user: str
    postgres_password: str
    db_host: str = 'postgres'
    db_port: int = 5432

    # Учётка репетитора создаётся из этих значений при первом старте backend
    tutor_login: str = Field(min_length=3, max_length=64)
    tutor_password: str = Field(min_length=8)
    tutor_name: str = 'Репетитор'

    app_origin: str = 'http://localhost'
    app_timezone: str = 'Europe/Moscow'
    session_days: int = 30

    @property
    def database_url(self) -> str:
        return (
            f'postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}'
            f'@{self.db_host}:{self.db_port}/{self.postgres_db}'
        )

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.app_timezone)

    @property
    def cookie_secure(self) -> bool:
        """Cookie сессии получает флаг Secure, когда сайт открыт по HTTPS."""
        return self.app_origin.startswith('https://')


settings = Settings()

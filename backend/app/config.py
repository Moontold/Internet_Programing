from zoneinfo import ZoneInfo

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения: читаются из .env, в коде значений по умолчанию для секретов нет."""

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

    postgres_db: str
    postgres_user: str
    postgres_password: str
    db_host: str = 'postgres'
    db_port: int = 5432

    app_origin: str = 'http://localhost'
    app_timezone: str = 'Europe/Moscow'

    @property
    def database_url(self) -> str:
        return (
            f'postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}'
            f'@{self.db_host}:{self.db_port}/{self.postgres_db}'
        )

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.app_timezone)


settings = Settings()

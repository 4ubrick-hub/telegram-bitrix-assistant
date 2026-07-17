"""
Конфигурация проекта.

Все настройки загружаются из .env файла с помощью Pydantic Settings.
"""

from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ==========================
    # Telegram
    # ==========================
    bot_token: SecretStr = Field(alias="TELEGRAM_BOT_TOKEN")
    telegram_admin_id: int = Field(alias="TELEGRAM_ADMIN_ID")

    # ==========================
    # Yandex Cloud
    # ==========================
    yandex_api_key: SecretStr = Field(alias="YANDEX_API_KEY")
    yandex_folder_id: str = Field(alias="YANDEX_FOLDER_ID")
    yandex_assistant_id: str = Field(alias="YANDEX_ASSISTANT_ID")
    yandex_thread_id: str = Field(alias="YANDEX_THREAD_ID")

    # ==========================
    # PostgreSQL
    # ==========================
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(alias="POSTGRES_DB")
    postgres_user: str = Field(alias="POSTGRES_USER")
    postgres_password: SecretStr = Field(alias="POSTGRES_PASSWORD")

    # ==========================
    # Parser Settings
    # ==========================
    enable_parser: bool = Field(default=False, alias="ENABLE_PARSER")
    parser_interval_hours: int = Field(default=24, alias="PARSER_INTERVAL_HOURS")
    bitrix24_docs_url: str = Field(
        default="https://apidocs.bitrix24.ru/",
        alias="BITRIX24_DOCS_URL"
    )

    # ==========================
    # Logging
    # ==========================
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    debug: bool = Field(default=False, alias="DEBUG")

    @property
    def database_url(self) -> str:
        """
        Возвращает строку подключения SQLAlchemy для синхронного драйвера.
        """
        return (
            "postgresql+psycopg2://"
            f"{self.postgres_user}:"
            f"{self.postgres_password.get_secret_value()}@"
            f"{self.postgres_host}:"
            f"{self.postgres_port}/"
            f"{self.postgres_db}"
        )

    @property
    def async_database_url(self) -> str:
        """
        Возвращает строку подключения SQLAlchemy для асинхронного драйвера.
        """
        return (
            "postgresql+asyncpg://"
            f"{self.postgres_user}:"
            f"{self.postgres_password.get_secret_value()}@"
            f"{self.postgres_host}:"
            f"{self.postgres_port}/"
            f"{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """
    Возвращает единственный экземпляр настроек.

    Благодаря lru_cache настройки загружаются
    только один раз за время работы программы.
    """
    return Settings()


settings = get_settings()

"""
Модуль конфигурации приложения.
Экспортирует функции для инициализации логирования и доступа к настройкам.
"""

from app.config.logging_config import setup_logging
from app.config.settings import settings

__all__ = ["setup_logging", "settings"]

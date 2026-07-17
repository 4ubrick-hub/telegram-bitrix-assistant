"""
Конфигурация логирования приложения.

Используется структурированное логирование с ротацией файлов.
"""

import logging
import logging.config
from pathlib import Path

from app.config.settings import settings
from app.core.constants import LOG_FORMAT, LOG_DATE_FORMAT

# Создаём папку для логов если её нет
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)


def setup_logging():
    """
    Настраивает логирование приложения.
    
    Логирует в:
    - Консоль (все уровни выше LOG_LEVEL)
    - Файл logs/bot.log (с ротацией по размеру)
    """

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": LOG_FORMAT,
                    "datefmt": LOG_DATE_FORMAT,
                },
                "detailed": {
                    "format": (
                        "%(asctime)s | %(levelname)-8s | %(name)s | "
                        "%(funcName)s:%(lineno)d | %(message)s"
                    ),
                    "datefmt": LOG_DATE_FORMAT,
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                },
                "file": {
                    "class": "logging.handlers.RotatingFileHandler",
                    "formatter": "default",
                    "filename": str(LOG_DIR / "bot.log"),  # ✅ ИСПРАВЛЕНО: ДОБАВЛЕНА ЗАПЯТАЯ
                    "maxBytes": 5 * 1024 * 1024,
                    "backupCount": 5,
                    "encoding": "utf-8",
                },
            },
            "root": {
                "handlers": ["console", "file"],
                "level": settings.log_level.upper(),
            },
        }
    )

    logger = logging.getLogger(__name__)
    logger.info("✅ Логирование инициализировано")

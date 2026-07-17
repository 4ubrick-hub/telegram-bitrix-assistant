"""
Модуль интеграции с Telegram.
Экспортирует основные компоненты для работы с ботом.
"""

from app.bot.bot import create_application

__all__ = ["create_application"]

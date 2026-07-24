"""
Инициализация Telegram-бота.
"""

from __future__ import annotations

import logging

from telegram.ext import Application

from app.bot.commands import register_commands
from app.bot.handlers import register_handlers
from app.config.settings import settings
from app.services.assistant_service import AssistantService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


def create_application() -> Application:
    """
    Создает и настраивает экземпляр Telegram Application.

    Returns:
        Готовый к запуску объект Application.
    """

    application = (
        Application.builder()
        .token(settings.bot_token.get_secret_value())
        .build()
    )

    register_commands(application)
    register_handlers(application)

    logger.info("Telegram Bot успешно инициализирован.")

    return application


class TelegramBot:
    """
    Обёртка над Telegram Application для управления ботом.
    """

    def __init__(self):
        """Инициализирует Telegram бота и сервисы."""
        self.app = create_application()

        self.assistant_service = AssistantService()
        self.user_service = UserService()

        self.app.bot_data["assistant_service"] = self.assistant_service
        self.app.bot_data["user_service"] = self.user_service

        logger.info("TelegramBot инициализирован со всеми сервисами")

    async def start(self) -> None:
        """
        Запускает Telegram-бота в асинхронном режиме.
        """
        logger.info("🚀 Запуск Telegram бота (polling mode)...")

        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling()

        logger.info("✅ Telegram бот успешно запущен")

        import asyncio
        await asyncio.Event().wait()

    async def stop(self) -> None:
        """
        Корректно останавливает Telegram-бота.
        """
        logger.info("🛑 Остановка Telegram бота...")

        if self.app.updater.running:
            await self.app.updater.stop()

        if self.app.running:
            await self.app.stop()

        await self.app.shutdown()

        logger.info("✅ Telegram бот остановлен")
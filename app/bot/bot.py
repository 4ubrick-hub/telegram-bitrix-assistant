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
    Инкапсулирует логику запуска и остановки бота.
    """

    def __init__(self):
        """Инициализирует Telegram бота и сервисы."""
        self.app = create_application()
        
        # 🆕 Инициализируем сервисы
        self.assistant_service = AssistantService()
        self.user_service = UserService()
        
        # 🆕 Передаём сервисы в контекст приложения
        self.app.bot_data['assistant_service'] = self.assistant_service
        self.app.bot_data['user_service'] = self.user_service
        
        logger.info("TelegramBot инициализирован со всеми сервисами")

    async def start(self) -> None:
        """
        Запускает бота в режиме polling.
        
        Blocking operation - блокирует event loop до остановки.
        """
        logger.info("🚀 Запуск Telegram бота (polling mode)...")
        self.app.run_polling()

    async def stop(self) -> None:
        """
        Останавливает бота корректно.
        
        Приостанавливает обработку сообщений и закрывает соединения.
        """
        logger.info("🛑 Остановка Telegram бота...")
        await self.app.shutdown()

"""
Middleware для обработки сообщений и управления пользователем.
Промежуточные слои обработки запросов в Telegram боте.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict

from telegram import Update
from telegram.ext import ContextTypes

from app.database.repositories import UserRepository
from app.database.session import get_session

logger = logging.getLogger(__name__)


class UserMiddleware:
    """
    Middleware для автоматического получения/создания пользователя
    перед обработкой сообщения.
    """

    @staticmethod
    async def process_update(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """
        Обрабатывает обновление и загружает/создает пользователя.

        Args:
            update: Обновление от Telegram.
            context: Контекст обработчика.
        """
        if update.effective_user is None:
            logger.warning("Получено обновление без пользователя")
            return

        try:
            user = update.effective_user
            async with get_session() as session:
                user_repo = UserRepository(session)

                # Получаем или создаем пользователя
                db_user = await user_repo.get_by_telegram_id(user.id)

                if db_user is None:
                    db_user = await user_repo.create(
                        telegram_id=user.id,
                        username=user.username,
                        first_name=user.first_name,
                        last_name=user.last_name,
                    )
                    logger.info(f"Создан новый пользователь: {user.id}")
                else:
                    # Обновляем информацию о пользователе
                    await user_repo.update(
                        db_user.id,
                        username=user.username,
                        first_name=user.first_name,
                        last_name=user.last_name,
                    )

                # Сохраняем пользователя в контексте для дальнейшего использования
                context.user_data["db_user"] = db_user

        except Exception as e:
            logger.exception(f"Ошибка в UserMiddleware: {e}")


class LoggingMiddleware:
    """
    Middleware для логирования всех входящих сообщений и команд.
    """

    @staticmethod
    async def process_update(
        update: Update,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> None:
        """
        Логирует информацию об обновлении.

        Args:
            update: Обновление от Telegram.
            context: Контекст обработчика.
        """
        if update.message:
            user = update.effective_user
            logger.info(
                f"Входящее сообщение от {user.id} (@{user.username}): "
                f"{update.message.text[:100]}"
            )

        elif update.callback_query:
            user = update.effective_user
            logger.info(
                f"Callback query от {user.id} (@{user.username}): "
                f"{update.callback_query.data}"
            )


class RateLimitMiddleware:
    """
    Middleware для ограничения частоты запросов от пользователей.
    Предотвращает спам и перегрузку сервера.
    """

    MAX_MESSAGES_PER_MINUTE = 10
    MAX_MESSAGES_PER_HOUR = 100

    @staticmethod
    async def check_rate_limit(
        user_id: int,
        context: ContextTypes.DEFAULT_TYPE,
    ) -> bool:
        """
        Проверяет, не превышен ли лимит на сообщения.

        Args:
            user_id: ID пользователя Telegram.
            context: Контекст обработчика.

        Returns:
            True если лимит не превышен, False если превышен.
        """
        from datetime import datetime, timedelta

        now = datetime.now()

        # Инициализируем счетчик для пользователя
        if "message_counts" not in context.bot_data:
            context.bot_data["message_counts"] = {}

        if user_id not in context.bot_data["message_counts"]:
            context.bot_data["message_counts"][user_id] = {
                "count_minute": 0,
                "count_hour": 0,
                "last_minute_reset": now,
                "last_hour_reset": now,
            }

        stats = context.bot_data["message_counts"][user_id]

        # Сбрасываем счетчик по минутам если прошла минута
        if now - stats["last_minute_reset"] > timedelta(minutes=1):
            stats["count_minute"] = 0
            stats["last_minute_reset"] = now

        # Сбрасываем счетчик по часам если прошел час
        if now - stats["last_hour_reset"] > timedelta(hours=1):
            stats["count_hour"] = 0
            stats["last_hour_reset"] = now

        # Увеличиваем счетчики
        stats["count_minute"] += 1
        stats["count_hour"] += 1

        # Проверяем лимиты
        if stats["count_minute"] > RateLimitMiddleware.MAX_MESSAGES_PER_MINUTE:
            logger.warning(f"Rate limit (минута) превышен для пользователя {user_id}")
            return False

        if stats["count_hour"] > RateLimitMiddleware.MAX_MESSAGES_PER_HOUR:
            logger.warning(f"Rate limit (час) превышен для пользователя {user_id}")
            return False

        return True

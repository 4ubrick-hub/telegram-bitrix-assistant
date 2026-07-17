"""
Обработчики текстовых сообщений Telegram-бота.
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application
from telegram.ext import ContextTypes
from telegram.ext import MessageHandler
from telegram.ext import filters

from app.services.assistant_service import AssistantService

logger = logging.getLogger(__name__)


async def message_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Обрабатывает входящие текстовые сообщения.
    
    Использует singleton экземпляр AssistantService из context.bot_data
    вместо создания нового на каждое сообщение.
    """

    if update.effective_user is None:
        logger.warning("Получено сообщение без пользователя")
        return

    if update.effective_message is None:
        logger.warning("Получено пустое сообщение")
        return

    text = update.effective_message.text

    if not text:
        return

    logger.info(
        "Получено сообщение от пользователя %s: %s",
        update.effective_user.id,
        text[:50],
    )

    try:
        # Получить singleton сервис из контекста бота
        service: AssistantService = context.bot_data.get('assistant_service')
        
        if service is None:
            logger.error("AssistantService не инициализирован в bot_data")
            await update.effective_message.reply_text(
                "❌ Ошибка: сервис ассистента не инициализирован."
            )
            return

        # Обработать сообщение
        answer = await service.process_message(
            telegram_user=update.effective_user,
            message=text,
        )

        # Отправить ответ (разбить на части если слишком длинный)
        max_message_length = 4096
        if len(answer) <= max_message_length:
            await update.effective_message.reply_text(answer)
        else:
            # Разбить на части
            for i in range(0, len(answer), max_message_length):
                chunk = answer[i:i + max_message_length]
                await update.effective_message.reply_text(chunk)

        logger.info(
            "Ответ отправлен пользователю %s",
            update.effective_user.id,
        )

    except Exception as e:
        logger.exception(
            f"Ошибка обработки сообщения от пользователя {update.effective_user.id}: {e}"
        )

        try:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка при обработке запроса.\n"
                "Попробуйте ещё раз позже или свяжитесь с администратором."
            )
        except Exception as send_error:
            logger.error(f"Не удалось отправить сообщение об ошибке: {send_error}")


def register_handlers(application: Application) -> None:
    """
    Регистрирует обработчики сообщений.
    """

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler,
        )
    )

    logger.info("Обработчики сообщений зарегистрированы.")

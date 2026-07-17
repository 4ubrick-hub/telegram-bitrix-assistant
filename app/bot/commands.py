"""
Команды Telegram-бота.

Реализует основные команды: /start, /help, /history, /clear, /stats
"""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import Application
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes

from app.services.assistant_service import AssistantService
from app.services.user_service import UserService

logger = logging.getLogger(__name__)


# ============================
# Command Handlers
# ============================


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Команда /start - начало работы с ботом.
    
    Приветствует пользователя и показывает краткую справку.
    """
    if update.effective_user is None:
        return

    logger.info(f"Команда /start от пользователя {update.effective_user.id}")

    welcome_message = (
        "👋 <b>Добро пожаловать!</b>\n\n"
        "Я ассистент по документации API <b>Bitrix24</b>.\n"
        "Просто задай мне вопрос о работе с API, и я помогу тебе найти ответ!\n\n"
        "<b>💡 Примеры вопросов:</b>\n"
        "• Как создать контакт через API?\n"
        "• Какой метод используется для получения списка сделок?\n"
        "• Как настроить webhook в Bitrix24?\n\n"
        "<b>📚 Доступные команды:</b>\n"
        "  /help - справка по командам\n"
        "  /history - история диалога\n"
        "  /clear - очистить историю\n"
        "  /stats - статистика\n\n"
        "⚡ Начни с любого вопроса!"
    )

    await update.message.reply_html(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Команда /help - справка по командам и возможностям.
    """
    if update.effective_user is None:
        return

    logger.info(f"Команда /help от пользователя {update.effective_user.id}")

    help_text = (
        "<b>📖 Справка по командам</b>\n\n"
        "<b>📝 Основные команды:</b>\n"
        "  /start - начать работу с ботом\n"
        "  /help - показать эту справку\n"
        "  /history - показать историю диалога\n"
        "  /clear - очистить историю сообщений\n"
        "  /stats - показать статистику использования\n\n"
        "<b>🔍 Как использовать бота:</b>\n"
        "1️⃣ Просто напиши вопрос на русском языке\n"
        "2️⃣ Бот найдёт ответ в документации API Bitrix24\n"
        "3️⃣ Получишь точный и структурированный ответ\n\n"
        "<b>📌 Примеры вопросов:</b>\n"
        "  • Как добавить новый контакт?\n"
        "  • Метод для обновления сделки\n"
        "  • Как получить список компаний?\n"
        "  • Что такое REST API?\n\n"
        "<b>💬 Советы:</b>\n"
        "  • Чем конкретнее вопрос, тем лучше ответ\n"
        "  • Историю можно очистить командой /clear\n"
        "  • Используйте /stats для просмотра статистики\n\n"
        "❓ Если нужна дополнительная помощь, /start запустит бота заново."
    )

    await update.message.reply_html(help_text)


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Команда /history - показать историю диалога пользователя.
    """
    if update.effective_user is None:
        return

    user_id = update.effective_user.id
    logger.info(f"Команда /history от пользователя {user_id}")

    try:
        service: AssistantService = context.bot_data.get('assistant_service')
        
        if service is None:
            await update.message.reply_text("❌ Сервис не инициализирован")
            return

        # Получить историю
        messages = await service.get_user_history(user_id, limit=10)

        if not messages:
            await update.message.reply_text(
                "📭 История диалога пуста.\n"
                "Задай мне вопрос о API Bitrix24!"
            )
            return

        # Форматировать историю
        history_text = "<b>📜 История диалога (последние 10 сообщений)</b>\n\n"
        
        for i, msg in enumerate(messages, 1):
            role = "👤 Ты" if msg['role'] == 'user' else "🤖 Я"
            text = msg['text'][:100]  # Сокращение до 100 символов
            time = msg.get('created_at', '?')
            
            history_text += f"{i}. <b>{role}</b> ({time})\n"
            history_text += f"   {text}...\n\n"

        # Отправить, но разбить если слишком длинно
        if len(history_text) > 4096:
            await update.message.reply_html(history_text[:4096])
            await update.message.reply_text(
                f"(и ещё {len(messages) - 5} сообщений...)"
            )
        else:
            await update.message.reply_html(history_text)

    except Exception as e:
        logger.exception(f"Ошибка при получении истории: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при получении истории: {e}"
        )


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Команда /clear - очистить историю диалога пользователя.
    """
    if update.effective_user is None:
        return

    user_id = update.effective_user.id
    logger.info(f"Команда /clear от пользователя {user_id}")

    try:
        service: AssistantService = context.bot_data.get('assistant_service')
        
        if service is None:
            await update.message.reply_text("❌ Сервис не инициализирован")
            return

        # Очистить историю
        success = await service.clear_history(user_id)

        if success:
            await update.message.reply_text(
                "✅ История диалога успешно очищена!\n"
                "Ты можешь начать с нового вопроса."
            )
        else:
            await update.message.reply_text(
                "ℹ️ Вероятно, история была уже пуста."
            )

    except Exception as e:
        logger.exception(f"Ошибка при очистке истории: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при очистке истории: {e}"
        )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Команда /stats - показать статистику использования.
    """
    if update.effective_user is None:
        return

    user_id = update.effective_user.id
    logger.info(f"Команда /stats от пользователя {user_id}")

    try:
        user_service: UserService = context.bot_data.get('user_service')
        
        if user_service is None:
            await update.message.reply_text("❌ Сервис не инициализирован")
            return

        # Получить статистику
        stats = await user_service.get_user_stats(user_id)

        stats_text = (
            "<b>📊 Ваша статистика</b>\n\n"
            f"👤 <b>Telegram ID:</b> {stats.get('telegram_id', '?')}\n"
            f"💬 <b>Всего сообщений:</b> {stats.get('total_messages', 0)}\n"
            f"📝 <b>Вопросов задано:</b> {stats.get('user_messages', 0)}\n"
            f"🤖 <b>Ответов получено:</b> {stats.get('assistant_messages', 0)}\n"
            f"📅 <b>Дата присоединения:</b> {stats.get('joined_date', '?')}\n"
            f"⏱️ <b>Последняя активность:</b> {stats.get('last_activity', '?')}\n\n"
            "Продолжай задавать вопросы! 💪"
        )

        await update.message.reply_html(stats_text)

    except Exception as e:
        logger.exception(f"Ошибка при получении статистики: {e}")
        await update.message.reply_text(
            f"❌ Ошибка при получении статистики: {e}"
        )


# ============================
# Register Commands
# ============================


def register_commands(application: Application) -> None:
    """
    Регистрирует все команды бота.
    """

    # Основные команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("clear", clear_command))
    application.add_handler(CommandHandler("stats", stats_command))

    logger.info("✅ Все команды зарегистрированы успешно")

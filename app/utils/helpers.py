"""
Вспомогательные функции приложения.
"""
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


def truncate_text(text: str, max_length: int = 4096) -> str:
    """
    Обрезает текст до максимальной длины.

    Args:
        text: Исходный текст.
        max_length: Максимальная длина.

    Returns:
        Обрезанный текст.
    """
    if len(text) <= max_length:
        return text

    truncated = text[: max_length - 3] + "..."
    logger.debug(
        f"Текст обрезан с {len(text)} до {len(truncated)} символов"
    )
    return truncated


def format_message(
    role: str,
    text: str,
    timestamp: datetime | None = None,
) -> str:
    """
    Форматирует сообщение для вывода.

    Args:
        role: Роль (user, assistant).
        text: Текст сообщения.
        timestamp: Время сообщения.

    Returns:
        Отформатированное сообщение.
    """
    time_str = ""
    if timestamp:
        time_str = f" [{timestamp.strftime('%H:%M:%S')}]"

    role_display = "👤 Вы" if role == "user" else "🤖 Ассистент"

    return f"{role_display}{time_str}:\n{text}"


def parse_error_message(error: Exception) -> str:
    """
    Преобразует исключение в читаемое сообщение об ошибке.

    Args:
        error: Исключение.

    Returns:
        Сообщение об ошибке для пользователя.
    """
    error_msg = str(error)

    if "AssistantConnectionError" in str(type(error)):
        return (
            "❌ Ошибка подключения к ассистенту. "
            "Пожалуйста, попробуйте позже."
        )

    if "AssistantProcessError" in str(type(error)):
        return (
            "❌ Ошибка обработки запроса. "
            "Попробуйте сформулировать вопрос иначе."
        )

    if "ParserError" in str(type(error)):
        return (
            "❌ Ошибка при получении информации из базы знаний. "
            "Попробуйте позже."
        )

    return "❌ Произошла неожиданная ошибка. Попробуйте позже."


def get_timestamp_str(dt: datetime | None = None) -> str:
    """
    Возвращает отформатированное время.

    Args:
        dt: Объект datetime (если None, используется текущее время).

    Returns:
        Отформатированная строка времени.
    """
    if dt is None:
        dt = datetime.now()
    return dt.strftime("%d.%m.%Y %H:%M:%S")


def safe_dict_get(data: dict[str, Any], key: str, default: Any = None) -> Any:
    """
    Безопасно получает значение из словаря.

    Args:
        data: Словарь.
        key: Ключ.
        default: Значение по умолчанию.

    Returns:
        Значение из словаря или default.
    """
    try:
        return data.get(key, default)
    except (AttributeError, TypeError):
        logger.warning(f"Ошибка при доступе к ключу {key}")
        return default


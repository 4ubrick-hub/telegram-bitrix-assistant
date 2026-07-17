"""
Валидаторы для проверки входных данных.
"""
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)


def validate_telegram_id(telegram_id: int | str) -> bool:
    """
    Проверяет корректность Telegram ID.

    Args:
        telegram_id: ID для проверки.

    Returns:
        True если валидный ID, False иначе.
    """
    try:
        tid = int(telegram_id)
        # Telegram IDs обычно положительные числа
        return tid > 0
    except (ValueError, TypeError):
        logger.warning(f"Невалидный Telegram ID: {telegram_id}")
        return False


def validate_url(url: str) -> bool:
    """
    Проверяет корректность URL.

    Args:
        url: URL для проверки.

    Returns:
        True если валидный URL, False иначе.
    """
    if not isinstance(url, str):
        return False

    url_pattern = re.compile(
        r"^https?://"  # http:// or https://
        r"(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|"  # domain
        r"localhost|"  # localhost
        r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # or IP
        r"(?::\d+)?"  # optional port
        r"(?:/?|[/?]\S+)$",
        re.IGNORECASE,
    )

    return bool(url_pattern.match(url))


def validate_message_text(text: str, min_length: int = 1, max_length: int = 4096) -> bool:
    """
    Проверяет корректность текста сообщения.

    Args:
        text: Текст для проверки.
        min_length: Минимальная длина.
        max_length: Максимальная длина.

    Returns:
        True если валидный текст, False иначе.
    """
    if not isinstance(text, str):
        return False

    text_len = len(text.strip())
    return min_length <= text_len <= max_length


def validate_username(username: Optional[str]) -> bool:
    """
    Проверяет корректность Telegram username.

    Args:
        username: Username для проверки.

    Returns:
        True если валидный username или None, False иначе.
    """
    if username is None:
        return True

    if not isinstance(username, str):
        return False

    # Telegram username: буквы, цифры, подчеркивание, 5-32 символа
    username_pattern = re.compile(r"^[A-Za-z0-9_]{5,32}$")
    return bool(username_pattern.match(username))

"""
Исключения модуля Yandex Assistant.
"""

from app.core.exceptions import YandexAssistantError


class AssistantConnectionError(YandexAssistantError):
    """Ошибка подключения к Yandex Assistant."""

    pass


class AssistantProcessError(YandexAssistantError):
    """Ошибка обработки сообщения в Yandex Assistant."""

    pass


class KnowledgeBaseError(YandexAssistantError):
    """Ошибка при работе с базой знаний."""

    pass

"""
Пользовательские исключения приложения.
"""


class ApplicationError(Exception):
    """
    Базовое исключение для ошибок приложения.
    """

    pass


class YandexAssistantError(ApplicationError):
    """
    Ошибка при работе с Yandex Assistant.
    """

    pass


class ParserError(ApplicationError):
    """
    Ошибка при парсинге документации.
    """

    pass


class DatabaseError(ApplicationError):
    """
    Ошибка при работе с базой данных.
    """

    pass


class ValidationError(ApplicationError):
    """
    Ошибка валидации данных.
    """

    pass

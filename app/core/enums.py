"""
Перечисления (Enum) для проекта.
"""

from enum import Enum


class ParserStatus(str, Enum):
    """
    Статусы парсера документации.
    """

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


class DocumentType(str, Enum):
    """
    Типы документов Bitrix24.
    """

    API_METHOD = "api_method"
    REST_API = "rest_api"
    WEBHOOK = "webhook"
    PARAMETER = "parameter"
    EXAMPLE = "example"

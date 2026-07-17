"""
Основной модуль с константами, перечислениями и исключениями проекта.
"""

from app.core.constants import BITRIX_API_DOCS_URL
from app.core.exceptions import ApplicationError
from app.core.enums import ParserStatus

__all__ = ["BITRIX_API_DOCS_URL", "ApplicationError", "ParserStatus"]

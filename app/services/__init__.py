"""
Модуль бизнес-логики приложения.
Содержит сервисы для работы с ассистентом, парсером и пользователями.
"""
from app.services.assistant_service import AssistantService
from app.services.parser_service import ParserService
from app.services.user_service import UserService

__all__ = ["AssistantService", "ParserService", "UserService"]

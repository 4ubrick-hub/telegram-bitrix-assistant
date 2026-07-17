"""
Сервис для работы с пользователями.
"""

from __future__ import annotations

import logging

from app.database.repositories import UserRepository
from app.database.session import get_session

logger = logging.getLogger(__name__)


class UserService:
    """
    Бизнес-логика работы с пользователями.
    """

    # 🆕 Сделали методы асинхронными!
    async def get_user_by_telegram_id(
        self,
        telegram_id: int,
    ) -> dict | None:
        """
        Возвращает информацию о пользователе.
        """

        with get_session() as session:

            repository = UserRepository(session)

            user = repository.get_by_telegram_id(
                telegram_id
            )

            if user is None:
                return None

            return {
                "id": user.id,
                "telegram_id": user.telegram_id,
                "username": user.username,
                "first_name": user.first_name,
                "created_at": user.created_at,
                "message_count": len(user.messages),
            }

    async def exists(
        self,
        telegram_id: int,
    ) -> bool:
        """
        Проверяет существование пользователя.
        """

        with get_session() as session:

            repository = UserRepository(session)

            return (
                repository.get_by_telegram_id(
                    telegram_id
                )
                is not None
            )

    async def get_user_stats(
        self,
        telegram_id: int,
    ) -> dict:
        """
        Возвращает статистику пользователя.
        
        Returns:
            Словарь со статистикой пользователя включая:
            - telegram_id: ID пользователя
            - total_messages: Всего сообщений
            - user_messages: Вопросов пользователя
            - assistant_messages: Ответов ассистента
            - joined_date: Дата присоединения
            - last_activity: Последняя активность
        """

        with get_session() as session:

            repository = UserRepository(session)

            user = repository.get_by_telegram_id(
                telegram_id
            )

            if user is None:
                return {
                    "telegram_id": telegram_id,
                    "total_messages": 0,
                    "user_messages": 0,
                    "assistant_messages": 0,
                    "joined_date": None,
                    "last_activity": None,
                }

            total_messages = len(user.messages)

            user_messages = sum(
                1 for message in user.messages
                if message.role.value == "user"
            )

            assistant_messages = (
                total_messages - user_messages
            )

            # 🆕 Найти последнее сообщение
            last_activity = None
            if user.messages:
                last_activity = max(
                    msg.created_at for msg in user.messages
                )

            return {
                "telegram_id": user.telegram_id,
                "total_messages": total_messages,
                "user_messages": user_messages,
                "assistant_messages": assistant_messages,
                "joined_date": user.created_at,  # 🆕 Исправлено с 'joined_at' на 'joined_date'
                "last_activity": last_activity,  # 🆕 Добавлено поле
            }

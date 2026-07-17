"""
Сервис для работы с Yandex Assistant.

Отвечает за:
- обработку пользовательских сообщений;
- сохранение истории диалога;
- взаимодействие с Yandex Assistant.
"""

from __future__ import annotations

import logging

from telegram import User as TelegramUser

from app.assistant.client import YandexAssistantClient
from app.database.models import MessageRole, User
from app.database.repositories import MessageRepository, UserRepository
from app.database.session import get_session

logger = logging.getLogger(__name__)


class AssistantService:
    """
    Сервис взаимодействия с Yandex Assistant.
    """

    def __init__(self) -> None:
        self._client = YandexAssistantClient()
        logger.info("AssistantService initialized")

    # ==========================================================
    # Внутренние методы
    # ==========================================================

    @staticmethod
    def _get_or_create_user(
        user_repo: UserRepository,
        telegram_user: TelegramUser,
    ) -> User:
        """
        Получает пользователя из БД или создаёт нового.
        """

        user = user_repo.get_by_telegram_id(telegram_user.id)

        if user is None:
            user = user_repo.create(
                telegram_id=telegram_user.id,
                first_name=telegram_user.first_name,
                username=telegram_user.username,
            )

            logger.info(
                "Создан новый пользователь %s",
                telegram_user.id,
            )

        return user

    @staticmethod
    def _save_message(
        repository: MessageRepository,
        user: User,
        role: MessageRole,
        text: str,
    ) -> None:
        """
        Сохраняет сообщение в историю.
        """

        repository.create(
            user=user,
            role=role,
            text=text,
        )

    @staticmethod
    def _get_history(
        repository: MessageRepository,
        user: User,
        limit: int = 20,
    ):
        """
        Возвращает историю сообщений пользователя.
        Пока используется только для будущего расширения.
        """

        return repository.get_history(
            user=user,
            limit=limit,
        )

    # ==========================================================
    # Публичный API
    # ==========================================================

    async def process_message(
        self,
        telegram_user: TelegramUser,
        message: str,
    ) -> str:
        """
        Обрабатывает сообщение пользователя.
        """

        logger.info(
            "Получено сообщение от пользователя %s",
            telegram_user.id,
        )

        with get_session() as session:

            user_repo = UserRepository(session)
            message_repo = MessageRepository(session)

            user = self._get_or_create_user(
                user_repo,
                telegram_user,
            )

            self._save_message(
                message_repo,
                user,
                MessageRole.USER,
                message,
            )

            # Пока история нигде не используется,
            # но позже её можно будет передавать Assistant.
            history = self._get_history(
                message_repo,
                user,
            )

            response = await self._client.send_message(
                message,
                # history=history
            )

            self._save_message(
                message_repo,
                user,
                MessageRole.ASSISTANT,
                response,
            )

        logger.info(
            "Ответ пользователю %s успешно сформирован",
            telegram_user.id,
        )

        return response

    async def get_user_history(
        self,
        telegram_id: int,
        limit: int = 20,
    ) -> list[dict]:
        """
        Возвращает историю сообщений пользователя.
        """

        with get_session() as session:

            user_repo = UserRepository(session)
            user = user_repo.get_by_telegram_id(
                telegram_id,
            )

            if user is None:
                return []

            repository = MessageRepository(session)

            messages = repository.get_history(
                user,
                limit=limit,
            )

            return [
                {
                    "role": msg.role.value,
                    "text": msg.text,
                    "created_at": msg.created_at,
                }
                for msg in messages
            ]

    async def clear_history(
        self,
        telegram_id: int,
    ) -> bool:
        """
        Очищает историю сообщений пользователя.
        """

        with get_session() as session:

            user_repo = UserRepository(session)

            user = user_repo.get_by_telegram_id(
                telegram_id,
            )

            if user is None:
                return False

            repository = MessageRepository(session)

            repository.clear_history(user)

        logger.info(
            "История пользователя %s очищена",
            telegram_id,
        )

        return True

    async def update_knowledge_base(
        self,
        documents: list[dict],
    ) -> bool:
        """
        Обновляет базу знаний Assistant.
        """

        logger.info(
            "Обновление базы знаний (%d документов)",
            len(documents),
        )

        return self._client.update_knowledge_base(
            documents
        )
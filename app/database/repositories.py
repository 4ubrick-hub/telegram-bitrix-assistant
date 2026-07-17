"""
Repositories для работы с ORM моделями.

Репозиторий - это абстракция над БД, которая инкапсулирует
всю логику работы с таблицами.
"""

from __future__ import annotations

import logging
from typing import Optional

from sqlalchemy import select, desc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.database.models import Message, MessageRole, User

logger = logging.getLogger(__name__)


class UserRepository:
    """Репозиторий для работы с пользователями."""

    def __init__(self, session: Session):
        self._session = session

    def get(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID."""
        try:
            return self._session.query(User).filter_by(id=user_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении пользователя {user_id}: {e}")
            raise

    def get_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Получить пользователя по Telegram ID."""
        try:
            return self._session.query(User).filter_by(
                telegram_id=telegram_id
            ).first()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении пользователя {telegram_id}: {e}")
            raise

    def create(
        self,
        telegram_id: int,
        first_name: str,
        username: str | None = None,
    ) -> User:
        """Создать нового пользователя с обработкой ошибок."""
        try:
            # Проверить не существует ли уже
            existing = self.get_by_telegram_id(telegram_id)
            if existing:
                logger.info(f"Пользователь {telegram_id} уже существует")
                return existing

            user = User(
                telegram_id=telegram_id,
                first_name=first_name,
                username=username,
            )
            self._session.add(user)
            self._session.flush()

            logger.info(f"✅ Создан новый пользователь: {telegram_id}")
            return user

        except IntegrityError as e:
            self._session.rollback()
            logger.error(f"Ошибка при создании пользователя {telegram_id}: {e}")
            
            # Попробовать получить существующего
            existing = self.get_by_telegram_id(telegram_id)
            if existing:
                return existing
            raise
        except SQLAlchemyError as e:
            self._session.rollback()
            logger.error(f"Критическая ошибка БД: {e}")
            raise

    def get_all(self, limit: int = 100) -> list[User]:
        """Получить всех пользователей."""
        try:
            return self._session.query(User).limit(limit).all()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении пользователей: {e}")
            raise

    def delete(self, user_id: int) -> bool:
        """Удалить пользователя."""
        try:
            user = self.get(user_id)
            if not user:
                return False
            self._session.delete(user)
            self._session.flush()
            logger.info(f"Удален пользователь: {user_id}")
            return True
        except SQLAlchemyError as e:
            self._session.rollback()
            logger.error(f"Ошибка при удалении пользователя {user_id}: {e}")
            raise


class MessageRepository:
    """Репозиторий для работы с сообщениями."""

    def __init__(self, session: Session):
        self._session = session

    def create(
        self,
        user: User,
        role: MessageRole,
        text: str,
    ) -> Message:
        """Создать новое сообщение с валидацией."""
        try:
            # Валидация
            if not user:
                raise ValueError("user не может быть None")
            if not text or not text.strip():
                raise ValueError("text не может быть пустым")
            if len(text) > 10000:
                raise ValueError("text слишком длинный (макс 10000 символов)")

            message = Message(
                user=user,
                role=role,
                text=text,
            )
            self._session.add(message)
            self._session.flush()

            logger.debug(f"✅ Создано сообщение: {message.id}")
            return message

        except ValueError as e:
            logger.error(f"Ошибка валидации сообщения: {e}")
            raise
        except IntegrityError as e:
            self._session.rollback()
            logger.error(f"Ошибка целостности БД: {e}")
            raise
        except SQLAlchemyError as e:
            self._session.rollback()
            logger.error(f"Ошибка БД при создании сообщения: {e}")
            raise

    def get(self, message_id: int) -> Optional[Message]:
        """Получить сообщение по ID."""
        try:
            return self._session.query(Message).filter_by(id=message_id).first()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении сообщения: {e}")
            raise

    def get_history(
        self,
        user: User,
        limit: int = 20,
    ) -> list[Message]:
        """Получить историю сообщений пользователя."""
        try:
            return (
                self._session.query(Message)
                .filter_by(user_id=user.id)
                .order_by(desc(Message.created_at))
                .limit(limit)
                .all()
            )
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при получении истории: {e}")
            raise

    def clear_history(self, user: User) -> int:
        """Очистить историю сообщений пользователя. Возвращает количество удалённых."""
        try:
            count = self._session.query(Message).filter_by(
                user_id=user.id
            ).delete()
            self._session.flush()
            logger.info(f"Очищена история пользователя {user.id}: {count} сообщений")
            return count
        except SQLAlchemyError as e:
            self._session.rollback()
            logger.error(f"Ошибка при очистке истории: {e}")
            raise

    def get_count(self, user: User) -> int:
        """Получить количество сообщений пользователя."""
        try:
            return self._session.query(Message).filter_by(
                user_id=user.id
            ).count()
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при подсчёте сообщений: {e}")
            raise

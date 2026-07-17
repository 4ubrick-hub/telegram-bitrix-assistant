"""
ORM-модели базы данных.

В данном модуле описаны все таблицы PostgreSQL,
используемые приложением.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger
from sqlalchemy import DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Text
from sqlalchemy import func
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

from app.database.base import Base


class MessageRole(str, Enum):
    """
    Роль сообщения в истории диалога.
    """

    USER = "user"
    ASSISTANT = "assistant"


class User(Base):
    """
    Пользователь Telegram.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False,
        index=True,
    )

    username: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    messages: Mapped[list["Message"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"User("
            f"id={self.id}, "
            f"telegram_id={self.telegram_id}, "
            f"username={self.username!r})"
        )


class Message(Base):
    """
    Сообщение пользователя или Assistant.
    """

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    role: Mapped[MessageRole] = mapped_column(
        SqlEnum(MessageRole),
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="messages",
    )

    def __repr__(self) -> str:
        return (
            f"Message("
            f"id={self.id}, "
            f"role={self.role}, "
            f"user_id={self.user_id})"
        )
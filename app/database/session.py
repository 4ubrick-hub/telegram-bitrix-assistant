"""
Настройка подключения к PostgreSQL.

Модуль предоставляет:
- создание SQLAlchemy Engine;
- фабрику сессий;
- контекстный менеджер для работы с БД;
- создание таблиц;
- проверку соединения.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from app.config.settings import settings
from app.database.base import Base

logger = logging.getLogger(__name__)

# Создаем Engine
engine = create_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)

# Создаем фабрику сессий
SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Контекстный менеджер для работы с сессией базы данных.

    Example:
        with get_session() as session:
            ...
    """
    session = SessionLocal()

    try:
        yield session
        session.commit()

    except Exception:
        session.rollback()
        raise

    finally:
        session.close()


def create_database() -> None:
    """
    Создает все таблицы, описанные в ORM-моделях.
    """
    logger.info("Создание структуры базы данных...")

    Base.metadata.create_all(bind=engine)

    logger.info("Структура базы данных успешно создана.")


def check_connection() -> bool:
    """
    Проверяет соединение с PostgreSQL.

    Returns:
        True, если соединение успешно.
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        logger.info("Соединение с PostgreSQL установлено.")
        return True

    except SQLAlchemyError as error:
        logger.exception(
            "Ошибка подключения к PostgreSQL: %s",
            error,
        )
        return False

def init_db() -> None:
    """
    Проверяет подключение и создаёт таблицы.
    """

    if not check_connection():
        raise RuntimeError(
            "Не удалось подключиться к PostgreSQL."
        )

    create_database()
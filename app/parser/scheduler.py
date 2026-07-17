"""
Планировщик для периодического парсинга документации Bitrix24.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

from app.core.enums import ParserStatus
from app.parser.crawler import DocumentCrawler
from app.parser.parser import DocumentParser

logger = logging.getLogger(__name__)


class ParsingScheduler:
    """
    Планировщик для автоматического парсинга документации.
    Запускает парсер по расписанию.
    """

    def __init__(
        self,
        crawler: DocumentCrawler,
        parser: DocumentParser,
        interval_hours: int = 24,
    ):
        """
        Инициализирует планировщик.

        Args:
            crawler: Экземпляр DocumentCrawler.
            parser: Экземпляр DocumentParser.
            interval_hours: Интервал между запусками (в часах).
        """
        self._crawler = crawler
        self._parser = parser
        self._interval = timedelta(hours=interval_hours)
        self._is_running = False
        self._status = ParserStatus.IDLE
        self._last_run: Optional[datetime] = None
        self._next_run: Optional[datetime] = None

        logger.info(
            f"ParsingScheduler инициализирован (интервал: {interval_hours} часов)"
        )

    async def start(self):
        """Запускает планировщик."""
        if self._is_running:
            logger.warning("Планировщик уже запущен")
            return

        self._is_running = True
        logger.info("Планировщик парсинга запущен")

        try:
            while self._is_running:
                await self._run_parsing_cycle()
                await asyncio.sleep(60)  # Проверяем каждую минуту

        except Exception as e:
            logger.exception(f"Ошибка в планировщике: {e}")
            self._status = ParserStatus.ERROR

    async def stop(self):
        """Останавливает планировщик."""
        self._is_running = False
        logger.info("Планировщик парсинга остановлен")

    async def _run_parsing_cycle(self):
        """Выполняет цикл парсинга, если пришло время."""
        now = datetime.now()

        # Определяем время следующего запуска
        if self._next_run is None:
            self._next_run = now + self._interval

        # Проверяем, пришло ли время парсить
        if now >= self._next_run:
            await self._parse_documentation()
            self._last_run = now
            self._next_run = now + self._interval

    async def _parse_documentation(self):
        """Основной метод парсинга документации."""
        try:
            self._status = ParserStatus.RUNNING
            logger.info("Начало парсинга документации...")

            # Список основных URL для парсинга
            urls_to_parse = [
                "/",  # Главная страница
                "/api/",  # API документация
                "/rest/",  # REST API
            ]

            # Загружаем страницы
            pages = await self._crawler.fetch_multiple_pages(urls_to_parse)

            if not pages:
                logger.warning("Не удалось загрузить страницы")
                self._status = ParserStatus.ERROR
                return

            # Парсим загруженные страницы
            documents = self._parser.parse_batch(pages)

            logger.info(
                f"Парсинг завершен успешно. "
                f"Обработано {len(documents)} документов"
            )

            self._status = ParserStatus.COMPLETED

        except Exception as e:
            logger.exception(f"Ошибка во время парсинга: {e}")
            self._status = ParserStatus.ERROR

    @property
    def status(self) -> ParserStatus:
        """Возвращает текущий статус парсера."""
        return self._status

    @property
    def is_running(self) -> bool:
        """Проверяет, запущен ли планировщик."""
        return self._is_running

    @property
    def last_run(self) -> Optional[datetime]:
        """Возвращает время последнего запуска."""
        return self._last_run

    @property
    def next_run(self) -> Optional[datetime]:
        """Возвращает время следующего запуска."""
        return self._next_run

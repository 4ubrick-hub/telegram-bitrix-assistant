"""
Сервис для парсинга и обновления базы знаний.
"""
from __future__ import annotations

import logging

from app.parser.crawler import DocumentCrawler
from app.parser.parser import DocumentParser
from app.parser.scheduler import ParsingScheduler

logger = logging.getLogger(__name__)


class ParserService:
    """
    Сервис для управления парсингом документации Bitrix24.
    """

    def __init__(self):
        """Инициализирует сервис парсинга."""
        self._crawler = DocumentCrawler()
        self._parser = DocumentParser()
        self._scheduler = ParsingScheduler(
            self._crawler,
            self._parser,
            interval_hours=24,
        )
        logger.info("ParserService инициализирован")

    async def start_scheduler(self):
        """Запускает автоматический парсинг."""
        await self._scheduler.start()
        logger.info("Планировщик парсинга запущен")

    async def stop_scheduler(self):
        """Останавливает планировщик парсинга."""
        await self._scheduler.stop()
        logger.info("Планировщик парсинга остановлен")

    async def parse_documentation(self, urls: list[str]) -> list[dict]:
        """
        Парсит документацию по указанным URL.

        Args:
            urls: Список URL для парсинга.

        Returns:
            Список распарсенных документов.
        """
        logger.info(f"Начало парсинга {len(urls)} страниц...")

        # Загружаем страницы
        pages = await self._crawler.fetch_multiple_pages(urls)
        if not pages:
            logger.warning("Не удалось загрузить страницы")
            return []

        # Парсим загруженные страницы
        documents = self._parser.parse_batch(pages)
        logger.info(f"Успешно распарсено {len(documents)} документов")

        return documents

    def get_scheduler_status(self) -> dict:
        """Получает статус планировщика."""
        return {
            "is_running": self._scheduler.is_running,
            "status": self._scheduler.status.value,
            "last_run": self._scheduler.last_run,
            "next_run": self._scheduler.next_run,
        }

    def close(self):
        """Закрывает краулер и освобождает ресурсы."""
        self._crawler.close()
        logger.info("ParserService завершен")

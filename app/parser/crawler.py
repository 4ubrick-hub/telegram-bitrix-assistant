"""
Краулер для загрузки страниц документации Bitrix24.
Использует Selenium для работы с JavaScript-контентом.
"""

from __future__ import annotations

import logging
from typing import Optional
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from app.core.constants import BITRIX_API_DOCS_URL, PARSER_TIMEOUT
from app.core.exceptions import ParserError

logger = logging.getLogger(__name__)


class DocumentCrawler:
    """
    Краулер для загрузки документации Bitrix24 API.
    Использует Selenium для обработки динамического контента.
    """

    def __init__(self):
        """Инициализирует краулер."""
        self._base_url = BITRIX_API_DOCS_URL
        self._timeout = PARSER_TIMEOUT
        self._driver: Optional[webdriver.Chrome] = None

        logger.info("DocumentCrawler инициализирован")

    def _init_driver(self) -> webdriver.Chrome:
        """
        Инициализирует Selenium WebDriver.

        Returns:
            Экземпляр Chrome WebDriver.
        """
        if self._driver is not None:
            return self._driver

        try:
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")

            self._driver = webdriver.Chrome(options=options)
            logger.info("Selenium WebDriver инициализирован")

            return self._driver

        except Exception as e:
            logger.exception("Ошибка инициализации WebDriver")
            raise ParserError(f"Не удалось инициализировать WebDriver: {e}") from e

    async def fetch_page(self, url: str) -> str:
        """
        Загружает содержимое страницы.

        Args:
            url: URL страницы.

        Returns:
            HTML содержимое страницы.

        Raises:
            ParserError: При ошибке загрузки страницы.
        """
        try:
            full_url = urljoin(self._base_url, url)
            logger.debug(f"Загрузка страницы: {full_url}")

            driver = self._init_driver()
            driver.get(full_url)

            # Ожидаем загрузки основного контента
            WebDriverWait(driver, self._timeout).until(
                EC.presence_of_all_elements_located((By.CLASS_NAME, "content"))
            )

            html_content = driver.page_source
            logger.info(f"Страница успешно загружена: {full_url}")

            return html_content

        except Exception as e:
            logger.exception(f"Ошибка загрузки страницы {url}: {e}")
            raise ParserError(f"Не удалось загрузить страницу {url}: {e}") from e

    async def fetch_multiple_pages(self, urls: list[str]) -> dict[str, str]:
        """
        Загружает несколько страниц параллельно.

        Args:
            urls: Список URL страниц.

        Returns:
            Словарь {url: html_content}.
        """
        results = {}

        for url in urls:
            try:
                content = await self.fetch_page(url)
                results[url] = content
            except ParserError as e:
                logger.warning(f"Пропуск страницы {url}: {e}")
                continue

        logger.info(f"Загружено страниц: {len(results)}/{len(urls)}")
        return results

    def close(self):
        """Закрывает WebDriver."""
        if self._driver is not None:
            self._driver.quit()
            self._driver = None
            logger.info("WebDriver закрыт")

    def __enter__(self):
        """Контекстный менеджер - вход."""
        self._init_driver()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер - выход."""
        self.close()


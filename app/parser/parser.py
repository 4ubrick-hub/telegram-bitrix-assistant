"""
Парсер документации Bitrix24 API.
Извлекает структурированную информацию из HTML-контента.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

from bs4 import BeautifulSoup

from app.core.exceptions import ParserError

logger = logging.getLogger(__name__)


class DocumentParser:
    """
    Парсер для извлечения информации из HTML документации Bitrix24.
    """

    def __init__(self):
        """Инициализирует парсер."""
        logger.info("DocumentParser инициализирован")

    def parse_page(self, html_content: str, url: str) -> dict:
        """
        Парсит HTML страницу и извлекает структурированные данные.

        Args:
            html_content: HTML содержимое страницы.
            url: URL исходной страницы.

        Returns:
            Словарь с извлеченной информацией.

        Raises:
            ParserError: При ошибке парсинга.
        """
        try:
            soup = BeautifulSoup(html_content, "html.parser")

            # Извлекаем основную информацию
            title = self._extract_title(soup)
            description = self._extract_description(soup)
            sections = self._extract_sections(soup)
            code_examples = self._extract_code_examples(soup)
            parameters = self._extract_parameters(soup)

            document = {
                "url": url,
                "title": title,
                "description": description,
                "sections": sections,
                "parameters": parameters,
                "code_examples": code_examples,
                "content": html_content[:1000],  # Первые 1000 символов
            }

            logger.info(f"Страница успешно спарсена: {title}")
            return document

        except Exception as e:
            logger.exception(f"Ошибка парсинга страницы {url}: {e}")
            raise ParserError(f"Не удалось спарсить страницу: {e}") from e

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Извлекает заголовок страницы."""
        title_tag = soup.find("h1") or soup.find("title")

        if title_tag:
            return title_tag.get_text(strip=True)

        return "Без названия"

    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Извлекает описание (мета-tag или первый абзац)."""
        meta_desc = soup.find("meta", attrs={"name": "description"})

        if meta_desc and meta_desc.get("content"):
            return meta_desc.get("content")

        paragraph = soup.find("p")

        if paragraph:
            return paragraph.get_text(strip=True)[:500]

        return ""

    def _extract_sections(self, soup: BeautifulSoup) -> list[dict]:
        """Извлекает разделы (headings и их содержимое)."""
        sections = []
        current_section = None

        for element in soup.find_all(["h2", "h3", "p", "ul", "ol"]):
            if element.name in ["h2", "h3"]:
                if current_section:
                    sections.append(current_section)

                current_section = {
                    "level": element.name,
                    "title": element.get_text(strip=True),
                    "content": [],
                }

            elif current_section and element.name in ["p", "ul", "ol"]:
                current_section["content"].append(element.get_text(strip=True))

        if current_section:
            sections.append(current_section)

        return sections

    def _extract_parameters(self, soup: BeautifulSoup) -> list[dict]:
        """Извлекает параметры API методов."""
        parameters = []

        # Ищем таблицы с параметрами
        tables = soup.find_all("table")

        for table in tables:
            rows = table.find_all("tr")

            if len(rows) < 2:
                continue

            # Первая строка - заголовки
            headers = [th.get_text(strip=True) for th in rows[0].find_all(["th", "td"])]

            # Проверяем, является ли это таблицей параметров
            if not any(
                keyword in header.lower()
                for header in headers
                for keyword in ["параметр", "parameter", "name", "тип", "type"]
            ):
                continue

            # Обрабатываем строки данных
            for row in rows[1:]:
                cols = row.find_all("td")

                if len(cols) >= 2:
                    param = {
                        "name": cols[0].get_text(strip=True),
                        "type": cols[1].get_text(strip=True) if len(cols) > 1 else "",
                        "description": cols[2].get_text(strip=True) if len(cols) > 2 else "",
                    }

                    parameters.append(param)

        return parameters

    def _extract_code_examples(self, soup: BeautifulSoup) -> list[dict]:
        """Извлекает примеры кода."""
        examples = []

        # Ищем блоки кода
        code_blocks = soup.find_all("pre")

        for idx, block in enumerate(code_blocks):
            code = block.get_text(strip=True)

            # Определяем язык кода
            language = "unknown"

            if "<?php" in code:
                language = "php"
            elif "#!/bin/bash" in code or "curl" in code:
                language = "bash"
            elif "{" in code and "[" in code:
                language = "json"

            example = {
                "index": idx,
                "language": language,
                "code": code[:500],  # Первые 500 символов
            }

            examples.append(example)

        return examples

    def parse_batch(self, pages: dict[str, str]) -> list[dict]:
        """
        Парсит батч страниц.

        Args:
            pages: Словарь {url: html_content}.

        Returns:
            Список распарсенных документов.
        """
        documents = []

        for url, html_content in pages.items():
            try:
                document = self.parse_page(html_content, url)
                documents.append(document)
            except ParserError as e:
                logger.warning(f"Пропуск документа {url}: {e}")
                continue

        logger.info(f"Батч успешно спарсен: {len(documents)} документов")
        return documents

"""
Парсер документации Bitrix24 (Diplodoc).

Извлекает информацию не из HTML-тегов, а из объекта
window.__DATA__, в котором хранится вся документация.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.core.exceptions import ParserError

logger = logging.getLogger(__name__)


class DocumentParser:
    """
    Парсер документации Bitrix24.

    Поддерживает новую документацию,
    построенную на Diplodoc.
    """

    def __init__(self):
        logger.info("DocumentParser initialized")

    def parse_page(
        self,
        html_content: str,
        url: str,
    ) -> dict:

        try:

            data = self._extract_data(html_content)

            title = (
                data.get("title")
                or data.get("meta", {}).get("title")
                or url
            )

            content = self._collect_text(data)

            return {
                "url": url,
                "title": title,
                "description": "",
                "sections": [],
                "parameters": [],
                "code_examples": [],
                "content": content,
            }

        except Exception as e:
            logger.exception("Ошибка парсинга %s", url)
            raise ParserError(str(e)) from e

    def parse_batch(
        self,
        pages: dict[str, str],
    ) -> list[dict]:

        documents = []

        for url, html in pages.items():

            try:
                documents.append(
                    self.parse_page(html, url)
                )

            except Exception as e:
                logger.warning(
                    "Не удалось обработать %s: %s",
                    url,
                    e,
                )

        logger.info(
            "Обработано %d документов",
            len(documents),
        )

        return documents

    # ---------------------------------------------------------
    # Diplodoc
    # ---------------------------------------------------------

    def _extract_data(
        self,
        html: str,
    ) -> dict[str, Any]:
        """
        Извлекает объект window.__DATA__
        из HTML страницы.
        """

        patterns = [

            r"window\.__DATA__\s*=\s*(\{.*?\})\s*;</script>",

            r"window\.__DATA__\s*=\s*JSON\.parse\(\s*'(.+?)'\s*\)",

            r'window\.__DATA__\s*=\s*JSON\.parse\(\s*"(.+?)"\s*\)',
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                html,
                re.DOTALL,
            )

            if not match:
                continue

            raw = match.group(1)

            try:

                if raw.startswith("{"):

                    return json.loads(raw)

                decoded = bytes(
                    raw,
                    "utf-8",
                ).decode("unicode_escape")

                return json.loads(decoded)

            except Exception:
                continue

        raise ParserError(
            "Не найден window.__DATA__"
        )

    # ---------------------------------------------------------
    # Извлечение текста из JSON
    # ---------------------------------------------------------

    def _collect_text(
        self,
        obj: Any,
    ) -> str:
        """
        Собирает весь текст из объекта Diplodoc.
        """

        result: list[str] = []

        self._walk(obj, result)

        # удаляем дубликаты,
        # сохраняя порядок

        unique = []

        seen = set()

        for line in result:

            line = self._normalize(line)

            if not line:
                continue

            if line in seen:
                continue

            seen.add(line)
            unique.append(line)

        return "\n".join(unique)

    def _walk(
        self,
        obj: Any,
        result: list[str],
    ) -> None:

        if obj is None:
            return

        if isinstance(obj, str):

            text = self._normalize(obj)

            if text:
                result.append(text)

            return

        if isinstance(obj, list):

            for item in obj:
                self._walk(item, result)

            return

        if not isinstance(obj, dict):
            return

        if "mdast" in obj:
            self._extract_markdown_ast(
                obj["mdast"],
                result,
            )

        for value in obj.values():
            self._walk(value, result)

    def _normalize(
        self,
        text: str,
    ) -> str:
        """
        Нормализует текст.
        """

        if not text:
            return ""

        text = text.replace("\xa0", " ")

        text = re.sub(
            r"<[^>]+>",
            " ",
            text,
        )

        text = text.replace("&nbsp;", " ")
        text = text.replace("&lt;", "<")
        text = text.replace("&gt;", ">")
        text = text.replace("&amp;", "&")

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text.strip()

    # ---------------------------------------------------------
    # Diplodoc Markdown AST
    # ---------------------------------------------------------

    def _extract_data(
        self,
        html: str,
    ) -> dict[str, Any]:
        """
        Извлекает JSON документации Bitrix24.

        Поддерживает несколько вариантов,
        используемых Diplodoc.
        """

        patterns = [

            r"window\.__DATA__\s*=\s*(\{.*?\})\s*;</script>",

            r"window\.__DATA__\s*=\s*JSON\.parse\(\s*'(.*?)'\s*\)",

            r'window\.__DATA__\s*=\s*JSON\.parse\(\s*"(.*?)"\s*\)',

            r"window\.__PRELOADED_STATE__\s*=\s*(\{.*?\})\s*;</script>",

            r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>',
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                html,
                re.DOTALL,
            )

            if not match:
                continue

            raw = match.group(1)

            try:

                raw = raw.strip()

                if raw.startswith("{"):
                    return json.loads(raw)

                raw = bytes(
                    raw,
                    "utf-8",
                ).decode("unicode_escape")

                return json.loads(raw)

            except Exception:
                continue

        raise ParserError(
            "Не удалось найти JSON документации."
        )
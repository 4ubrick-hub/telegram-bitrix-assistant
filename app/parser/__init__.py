"""
Модуль парсинга документации Bitrix24.
"""

from app.parser.crawler import DocumentCrawler
from app.parser.parser import DocumentParser
from app.parser.scheduler import ParsingScheduler

__all__ = ["DocumentCrawler", "DocumentParser", "ParsingScheduler"]

"""
Константы приложения.
"""

# API документация Bitrix24
BITRIX_API_DOCS_URL = "https://apidocs.bitrix24.ru/"

# Yandex Assistant
YANDEX_ASSISTANT_MODEL = "yandexgpt-latest"

# Парсер
PARSER_TIMEOUT = 30  # секунды
PARSER_BATCH_SIZE = 5  # одновременно обрабатываемые страницы

# Диалоговая история
MAX_HISTORY_LENGTH = 20  # последних сообщений в контексте
MESSAGE_MAX_LENGTH = 4096  # максимальная длина сообщения Telegram

# Логирование
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
LOG_DATE_FORMAT = "%d.%m.%Y %H:%M:%S"
LOG_MAX_BYTES = 5 * 1024 * 1024  # 5 МБ
LOG_BACKUP_COUNT = 5

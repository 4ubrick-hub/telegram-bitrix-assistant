"""
Главная точка входа приложения.
Инициализирует и запускает Telegram бота.
"""
import asyncio
import logging

from app.bot.bot import TelegramBot
from app.config.logging_config import setup_logging
from app.config.settings import settings
from app.database.session import init_db
from app.services.parser_service import ParserService

# Настройка логирования
setup_logging()
logger = logging.getLogger(__name__)


class Application:
    """
    Основной класс приложения.
    Управляет инициализацией и жизненным циклом.
    """

    def __init__(self):
        """Инициализирует приложение."""
        self.bot: TelegramBot | None = None
        self.parser_service: ParserService | None = None
        self._running = False

    async def startup(self):
        """Стартовые процедуры приложения."""
        logger.info("🚀 Запуск приложения...")

        # Инициализируем БД
        logger.info("Инициализация базы данных...")
        init_db()
        logger.info("✅ База данных инициализирована")

        # Инициализируем парсер документации
        logger.info("Инициализация сервиса парсинга...")
        self.parser_service = ParserService()

        # Запускаем планировщик парсинга, если включено в настройках
        # if settings.ENABLE_PARSER:
        #     await self.parser_service.start_scheduler()
        #     logger.info("✅ Планировщик парсинга запущен")

        # Инициализируем Telegram бота
        logger.info("Инициализация Telegram бота...")
        self.bot = TelegramBot()
        logger.info("✅ Telegram бот инициализирован")

        self._running = True
        logger.info("✅ Приложение успешно запущено")

    async def shutdown(self):
        """Процедуры завершения приложения."""
        logger.info("🛑 Завершение приложения...")

        if self.bot:
            logger.info("Остановка Telegram бота...")
            await self.bot.stop()

        if self.parser_service:
            logger.info("Остановка сервиса парсинга...")
            await self.parser_service.stop_scheduler()
            self.parser_service.close()

        self._running = False
        logger.info("✅ Приложение завершено")

    async def run(self):
        """Запускает приложение."""
        try:
            await self.startup()

            if self.bot:
                logger.info("Запуск обработчика сообщений бота...")
                await self.bot.start()

        except KeyboardInterrupt:
            logger.info("Получен сигнал прерывания (Ctrl+C)")
        except Exception as e:
            logger.exception(f"Ошибка при запуске приложения: {e}")
            raise
        finally:
            await self.shutdown()

    @property
    def is_running(self) -> bool:
        """Проверяет, запущено ли приложение."""
        return self._running


async def main():
    """Основная функция."""
    app = Application()
    await app.run()


if __name__ == "__main__":
    asyncio.run(main())

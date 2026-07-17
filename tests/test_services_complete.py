"""
Unit-тесты для Telegram-Bitrix Assistant проекта.

Требуемые зависимости:
- pytest>=7.0.0
- pytest-asyncio>=0.23.0
- pytest-mock>=3.10.0
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime

# ============================================================
# ТЕСТЫ UserService
# ============================================================

pytestmark = pytest.mark.asyncio


class TestUserService:
    """Тесты для UserService."""

    @pytest.fixture
    async def user_service(self):
        """Инициализация UserService для тестов."""
        from app.services.user_service import UserService
        return UserService()

    async def test_get_user_stats_nonexistent_user(self, user_service):
        """
        Тест получения статистики несуществующего пользователя.
        Должен вернуть нулевые значения.
        """
        stats = await user_service.get_user_stats(999999)

        assert stats is not None
        assert stats['telegram_id'] == 999999
        assert stats['total_messages'] == 0
        assert stats['user_messages'] == 0
        assert stats['assistant_messages'] == 0
        assert stats['joined_date'] is None
        assert stats['last_activity'] is None

    async def test_user_exists_nonexistent(self, user_service):
        """Тест проверки существования несуществующего пользователя."""
        exists = await user_service.exists(999999)
        assert exists is False

    @patch('app.services.user_service.get_session')
    async def test_get_user_by_telegram_id_nonexistent(self, mock_get_session, user_service):
        """Тест получения информации о несуществующем пользователе."""
        # Мокировать сессию
        mock_session = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=mock_session)
        mock_context.__exit__ = MagicMock(return_value=None)
        mock_get_session.return_value = mock_context

        # Мокировать репозиторий - пользователь не найден
        with patch('app.services.user_service.UserRepository') as mock_repo_class:
            mock_repo = MagicMock()
            mock_repo.get_by_telegram_id.return_value = None
            mock_repo_class.return_value = mock_repo

            result = await user_service.get_user_by_telegram_id(999999)
            assert result is None


# ============================================================
# ТЕСТЫ AssistantService
# ============================================================

class TestAssistantService:
    """Тесты для AssistantService."""

    @pytest.fixture
    async def assistant_service(self):
        """Инициализация AssistantService для тестов."""
        with patch('app.services.assistant_service.YandexAssistantClient'):
            from app.services.assistant_service import AssistantService
            return AssistantService()

    @patch('app.services.assistant_service.get_session')
    async def test_process_message_new_user(self, mock_get_session, assistant_service):
        """Тест обработки сообщения от нового пользователя."""
        # Мокировать сессию
        mock_session = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__ = MagicMock(return_value=mock_session)
        mock_context.__exit__ = MagicMock(return_value=None)
        mock_get_session.return_value = mock_context

        # Мокировать репозитории
        with patch('app.services.assistant_service.UserRepository') as mock_user_repo_class, \
             patch('app.services.assistant_service.MessageRepository') as mock_msg_repo_class:

            mock_user_repo = MagicMock()
            mock_msg_repo = MagicMock()
            mock_user_repo_class.return_value = mock_user_repo
            mock_msg_repo_class.return_value = mock_msg_repo

            # Первый вызов - пользователь не найден, второй - создан
            mock_user = MagicMock()
            mock_user.id = 1
            mock_user_repo.get_by_telegram_id.return_value = None
            mock_user_repo.create.return_value = mock_user

            # Мокировать Telegram User
            mock_telegram_user = MagicMock()
            mock_telegram_user.id = 12345
            mock_telegram_user.first_name = "Test"
            mock_telegram_user.username = "testuser"

            # Мокировать клиент
            assistant_service._client.send_message = AsyncMock(
                return_value="Ответ на тестовый вопрос"
            )

            # Вызов
            response = await assistant_service.process_message(
                telegram_user=mock_telegram_user,
                message="Тестовый вопрос"
            )

            # Проверки
            assert response == "Ответ на тестовый вопрос"
            mock_user_repo.create.assert_called_once()
            assert mock_msg_repo.create.call_count == 2  # Вопрос + ответ

    async def test_get_user_history_empty(self, assistant_service):
        """Тест получения истории несуществующего пользователя."""
        with patch('app.services.assistant_service.get_session'):
            with patch('app.services.assistant_service.UserRepository') as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.get_by_telegram_id.return_value = None
                mock_repo_class.return_value = mock_repo

                history = await assistant_service.get_user_history(999999)
                assert history == []

    async def test_clear_history_nonexistent_user(self, assistant_service):
        """Тест очистки истории несуществующего пользователя."""
        with patch('app.services.assistant_service.get_session'):
            with patch('app.services.assistant_service.UserRepository') as mock_repo_class:
                mock_repo = MagicMock()
                mock_repo.get_by_telegram_id.return_value = None
                mock_repo_class.return_value = mock_repo

                result = await assistant_service.clear_history(999999)
                assert result is False


# ============================================================
# ТЕСТЫ YandexAssistantClient
# ============================================================

class TestYandexAssistantClient:
    """Тесты для YandexAssistantClient."""

    @pytest.fixture
    async def assistant_client(self):
        """Инициализация клиента."""
        with patch('app.assistant.client.YandexAssistantClient.__init__', return_value=None):
            from app.assistant.client import YandexAssistantClient
            client = YandexAssistantClient()
            client._api_key = "test-key"
            client._folder_id = "test-folder"
            client._assistant_id = "test-assistant"
            client._thread_id = "test-thread"
            return client

    async def test_send_message_success(self, assistant_client):
        """Тест успешной отправки сообщения."""
        assistant_client._call_assistant_api = AsyncMock(
            return_value="Успешный ответ"
        )

        response = await assistant_client.send_message("Тестовый вопрос")

        assert response == "Успешный ответ"
        assistant_client._call_assistant_api.assert_called_once()

    async def test_send_message_with_custom_thread_id(self, assistant_client):
        """Тест отправки сообщения с кастомным thread_id."""
        assistant_client._call_assistant_api = AsyncMock(
            return_value="Ответ"
        )

        response = await assistant_client.send_message(
            "Вопрос",
            thread_id="custom-thread"
        )

        assert response == "Ответ"
        # Проверить что был передан правильный thread_id
        call_args = assistant_client._call_assistant_api.call_args
        assert call_args.kwargs['thread_id'] == "custom-thread"

    @patch('aiohttp.ClientSession.post')
    async def test_make_api_request_success(self, mock_post, assistant_client):
        """Тест успешного API запроса."""
        # Мокировать ответ
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.text = AsyncMock(return_value='{"response": "API ответ"}')

        mock_post.return_value.__aenter__.return_value = mock_resp

        response = await assistant_client._make_api_request(
            "Вопрос",
            "thread-id"
        )

        assert "API ответ" in response

    @patch('aiohttp.ClientSession.post')
    async def test_make_api_request_timeout(self, mock_post, assistant_client):
        """Тест timeout при API запросе."""
        from app.assistant.exceptions import AssistantProcessError

        mock_post.side_effect = asyncio.TimeoutError()

        with pytest.raises(asyncio.TimeoutError):
            await assistant_client._make_api_request("Вопрос", "thread-id")

    @patch('aiohttp.ClientSession.post')
    async def test_make_api_request_rate_limit(self, mock_post, assistant_client):
        """Тест обработки rate limit (429)."""
        from app.assistant.exceptions import AssistantProcessError

        mock_resp = AsyncMock()
        mock_resp.status = 429
        mock_resp.text = AsyncMock(return_value='Rate limit exceeded')

        mock_post.return_value.__aenter__.return_value = mock_resp

        with pytest.raises(AssistantProcessError) as exc_info:
            await assistant_client._make_api_request("Вопрос", "thread-id")

        assert "rate limit" in str(exc_info.value).lower() or "429" in str(exc_info.value)

    @patch('aiohttp.ClientSession.post')
    async def test_make_api_request_auth_error(self, mock_post, assistant_client):
        """Тест обработки ошибки аутентификации (401)."""
        from app.assistant.exceptions import AssistantProcessError

        mock_resp = AsyncMock()
        mock_resp.status = 401
        mock_resp.text = AsyncMock(return_value='Unauthorized')

        mock_post.return_value.__aenter__.return_value = mock_resp

        with pytest.raises(AssistantProcessError) as exc_info:
            await assistant_client._make_api_request("Вопрос", "thread-id")

        assert "401" in str(exc_info.value) or "аутентификация" in str(exc_info.value).lower()


# ============================================================
# ТЕСТЫ TelegramBot
# ============================================================

class TestTelegramBot:
    """Тесты для TelegramBot."""

    @patch('app.bot.bot.create_application')
    @patch('app.bot.bot.AssistantService')
    @patch('app.bot.bot.UserService')
    def test_telegram_bot_initialization(self, mock_user_service, mock_assistant_service, mock_app):
        """Тест инициализации TelegramBot."""
        from app.bot.bot import TelegramBot

        mock_application = MagicMock()
        mock_application.bot_data = {}
        mock_app.return_value = mock_application

        bot = TelegramBot()

        # Проверить что сервисы инициализированы
        assert mock_assistant_service.called
        assert mock_user_service.called

        # Проверить что сервисы добавлены в bot_data
        assert 'assistant_service' in mock_application.bot_data
        assert 'user_service' in mock_application.bot_data

    @patch('app.bot.bot.create_application')
    @patch('app.bot.bot.AssistantService')
    @patch('app.bot.bot.UserService')
    async def test_telegram_bot_start(self, mock_user_service, mock_assistant_service, mock_app):
        """Тест запуска TelegramBot."""
        from app.bot.bot import TelegramBot

        mock_application = MagicMock()
        mock_application.bot_data = {}
        mock_application.run_polling = AsyncMock()
        mock_app.return_value = mock_application

        bot = TelegramBot()
        await bot.start()

        mock_application.run_polling.assert_called_once()

    @patch('app.bot.bot.create_application')
    @patch('app.bot.bot.AssistantService')
    @patch('app.bot.bot.UserService')
    async def test_telegram_bot_stop(self, mock_user_service, mock_assistant_service, mock_app):
        """Тест остановки TelegramBot."""
        from app.bot.bot import TelegramBot

        mock_application = MagicMock()
        mock_application.bot_data = {}
        mock_application.stop = AsyncMock()
        mock_app.return_value = mock_application

        bot = TelegramBot()
        await bot.stop()

        mock_application.stop.assert_called_once()


# ============================================================
# ТЕСТЫ Database Repositories
# ============================================================

class TestUserRepository:
    """Тесты для UserRepository."""

    @pytest.fixture
    def user_repository(self):
        """Инициализация UserRepository для тестов."""
        from app.database.repositories import UserRepository
        mock_session = MagicMock()
        return UserRepository(mock_session)

    def test_get_user_by_telegram_id_success(self, user_repository):
        """Тест получения пользователя по ID."""
        mock_user = MagicMock()
        user_repository._session.query.return_value.filter_by.return_value.first.return_value = mock_user

        result = user_repository.get_by_telegram_id(12345)

        assert result == mock_user

    def test_create_duplicate_user(self, user_repository):
        """Тест создания дублирующегося пользователя."""
        mock_existing_user = MagicMock()
        mock_existing_user.id = 1
        mock_existing_user.telegram_id = 12345

        # Первый вызов - пользователь существует
        user_repository._session.query.return_value.filter_by.return_value.first.return_value = (
            mock_existing_user
        )

        result = user_repository.create(12345, "Test", "testuser")

        # Должен вернуть существующего пользователя
        assert result == mock_existing_user


# ============================================================
# КОНФИГУРАЦИЯ pytest
# ============================================================

# conftest.py - дополнительная конфигурация

"""
# Содержимое файла tests/conftest.py

import pytest
import os
from dotenv import load_dotenv

# Загрузить переменные окружения для тестов
load_dotenv('.env.test')

@pytest.fixture(scope="session")
def event_loop():
    \"\"\"Создать event loop для всех async тестов.\"\"\"
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
def reset_imports():
    \"\"\"Сбросить импорты перед каждым тестом.\"\"\"
    yield
    # Cleanup after each test
    import sys
    # Можно добавить дополнительную очистку если нужна
"""


# ============================================================
# ЗАПУСК ТЕСТОВ
# ============================================================

"""
Команды для запуска тестов:

# Запустить все тесты
pytest tests/

# Запустить конкретный тестовый файл
pytest tests/test_services.py

# Запустить конкретный тест
pytest tests/test_services.py::TestUserService::test_get_user_stats_nonexistent_user

# Запустить с verbose выводом
pytest tests/ -v

# Запустить с покрытием кода
pytest tests/ --cov=app --cov-report=html

# Запустить с параллельным выполнением (требуется pytest-xdist)
pytest tests/ -n auto

# Запустить только тесты для ассистента
pytest tests/ -k "Assistant"

# Показать print выводы
pytest tests/ -s
"""

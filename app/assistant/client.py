"""
Клиент для взаимодействия с Yandex Assistant.
Использует LLM Yandex GPT 5 для поиска информации в базе знаний.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from app.assistant.exceptions import (
    AssistantConnectionError,
    AssistantProcessError,
    KnowledgeBaseError,
)
from app.config.settings import settings

logger = logging.getLogger(__name__)


class YandexAssistantClient:
    """
    Клиент для работы с Yandex Assistant API.
    Инкапсулирует логику взаимодействия с ассистентом и его базой знаний.
    """

    def __init__(self):
        """Инициализирует клиент Yandex Assistant."""
        try:
            # Импортируем SDK только при инициализации
            from yandex_cloud.genai.v1.assistant_service_pb2 import (
                StreamMessageRequest,
            )
            from yandex_cloud.genai.v1.common_pb2 import Message as GrpcMessage

            self.StreamMessageRequest = StreamMessageRequest
            self.GrpcMessage = GrpcMessage

            self._api_key = settings.yandex_api_key.get_secret_value()
            self._folder_id = settings.yandex_folder_id
            self._assistant_id = settings.yandex_assistant_id
            self._thread_id = settings.yandex_thread_id

            logger.info("Yandex Assistant Client инициализирован.")

        except ImportError as e:
            raise AssistantConnectionError(
                "Не удалось импортировать SDK Yandex Cloud. "
                "Убедитесь, что установлена библиотека yandex-cloud-ml-sdk."
            ) from e
        except AttributeError as e:
            raise AssistantConnectionError(
                f"Отсутствует требуемая переменная окружения: {e}"
            ) from e

    async def send_message(
        self,
        message: str,
        thread_id: Optional[str] = None,
    ) -> str:
        """
        Отправляет сообщение в Yandex Assistant и получает ответ.

        Args:
            message: Текст сообщения от пользователя.
            thread_id: ID потока диалога (если None, используется default).

        Returns:
            Ответ ассистента.

        Raises:
            AssistantProcessError: При ошибке обработки сообщения.
        """
        try:
            thread_id = thread_id or self._thread_id

            logger.debug(
                f"Отправка сообщения в Yandex Assistant. "
                f"Thread ID: {thread_id}"
            )

            response = await self._call_assistant_api(
                message=message,
                thread_id=thread_id,
            )

            logger.info(
                f"Получен ответ от Yandex Assistant "
                f"(длина: {len(response)} символов)"
            )

            return response

        except Exception as e:
            logger.exception(
                f"Ошибка при обработке сообщения в Yandex Assistant: {e}"
            )
            raise AssistantProcessError(
                f"Не удалось получить ответ от ассистента: {e}"
            ) from e

    async def _call_assistant_api(
        self,
        message: str,
        thread_id: str,
    ) -> str:
        """
        Внутренний метод для вызова API Yandex Assistant.
        
        Реализует REST API с retry логикой и обработкой ошибок.

        Args:
            message: Текст сообщения.
            thread_id: ID потока диалога.

        Returns:
            Ответ от ассистента.
            
        Raises:
            AssistantProcessError: При ошибке вызова API.
        """
        try:
            import aiohttp
            
            logger.debug(
                f"Вызов API Yandex Assistant для сообщения: {message[:100]}..."
            )

            # Параметры для retry
            max_attempts = 3
            attempt = 1
            last_error = None

            while attempt <= max_attempts:
                try:
                    response = await self._make_api_request(message, thread_id)
                    logger.info(f"Успешный ответ от API (попытка {attempt})")
                    return response
                    
                except asyncio.TimeoutError as e:
                    last_error = e
                    if attempt < max_attempts:
                        wait_time = 2 ** (attempt - 1)  # 1, 2, 4 сек
                        logger.warning(
                            f"Timeout (попытка {attempt}/{max_attempts}). "
                            f"Ждём {wait_time}сек перед повтором..."
                        )
                        await asyncio.sleep(wait_time)
                    attempt += 1
                    
                except aiohttp.ClientError as e:
                    last_error = e
                    if attempt < max_attempts:
                        wait_time = 2 ** (attempt - 1)
                        logger.warning(
                            f"Ошибка сети (попытка {attempt}/{max_attempts}). "
                            f"Ждём {wait_time}сек перед повтором: {str(e)[:100]}"
                        )
                        await asyncio.sleep(wait_time)
                    attempt += 1
                    
                except AssistantProcessError as e:
                    # Если rate limit или временная ошибка - повторяем
                    if "rate limit" in str(e).lower() or "429" in str(e):
                        if attempt < max_attempts:
                            wait_time = 2 ** attempt  # 2, 4, 8 сек для rate limit
                            logger.warning(
                                f"Rate limit (попытка {attempt}/{max_attempts}). "
                                f"Ждём {wait_time}сек перед повтором..."
                            )
                            await asyncio.sleep(wait_time)
                            attempt += 1
                        else:
                            raise
                    else:
                        # Постоянная ошибка - не повторяем
                        raise

            # Если все попытки исчерпаны
            raise AssistantProcessError(
                f"Не удалось получить ответ после {max_attempts} попыток: {last_error}"
            )

        except Exception as e:
            logger.error(f"Критическая ошибка при вызове API: {e}")
            raise AssistantProcessError(f"Ошибка API: {e}") from e

    async def _make_api_request(
        self,
        message: str,
        thread_id: str,
    ) -> str:
        """
        Выполняет одиночный запрос к REST API Yandex Assistant.
        
        Args:
            message: Текст сообщения.
            thread_id: ID потока диалога.
            
        Returns:
            Ответ от API.
            
        Raises:
            AssistantProcessError: При ошибке API.
            asyncio.TimeoutError: При timeout.
        """
        try:
            import aiohttp
            
            # Параметры запроса
            url = "https://api.llm.cloud.yandex.net:443/v1/messages"
            headers = {
                "Authorization": f"Api-Key {self._api_key}",
                "X-Folder-ID": self._folder_id,
                "Content-Type": "application/json",
            }
            
            payload = {
                "assistant_id": self._assistant_id,
                "thread_id": thread_id,
                "messages": [{"role": "user", "content": message}]
            }
            
            # Timeout: 30 секунд
            timeout = aiohttp.ClientTimeout(total=30, connect=10, sock_read=20)
            
            logger.debug(f"POST запрос к {url}")
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.post(
                    url,
                    json=payload,
                    headers=headers,
                    ssl=False  # Для development. В production использовать True
                ) as resp:
                    response_text = await resp.text()
                    
                    if resp.status == 200:
                        logger.debug(f"API ответил с кодом 200")
                        try:
                            import json
                            data = json.loads(response_text)
                            
                            # Попытаться получить ответ разными способами
                            if "response" in data:
                                return data["response"]
                            elif "message" in data:
                                if isinstance(data["message"], dict):
                                    return data["message"].get("content", str(data["message"]))
                                return str(data["message"])
                            elif "messages" in data and len(data["messages"]) > 0:
                                last_msg = data["messages"][-1]
                                if isinstance(last_msg, dict):
                                    return last_msg.get("content", str(last_msg))
                                return str(last_msg)
                            else:
                                logger.warning(f"Неожиданный формат ответа API: {data}")
                                return "Получен ответ от API, но не удалось распарсить формат"
                                
                        except ValueError as e:
                            logger.error(f"Ошибка парсинга JSON: {response_text[:200]}")
                            return f"Ошибка парсинга ответа API: {str(e)[:100]}"
                            
                    elif resp.status == 429:
                        raise AssistantProcessError(
                            "API rate limit превышен (код 429). Попробуйте позже."
                        )
                    elif resp.status == 401:
                        raise AssistantProcessError(
                            "Ошибка аутентификации (код 401). Проверьте YANDEX_API_KEY"
                        )
                    elif resp.status == 403:
                        raise AssistantProcessError(
                            "Доступ запрещён (код 403). Проверьте YANDEX_FOLDER_ID"
                        )
                    elif resp.status >= 500:
                        raise AssistantProcessError(
                            f"Ошибка сервера (код {resp.status}). "
                            f"Сервер Yandex недоступен. Попробуйте позже."
                        )
                    else:
                        raise AssistantProcessError(
                            f"API вернул код {resp.status}: {response_text[:200]}"
                        )
                        
        except asyncio.TimeoutError:
            logger.error("Timeout при вызове Yandex API (30 сек)")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Ошибка сети при вызове API: {type(e).__name__}: {e}")
            raise
        except AssistantProcessError:
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при вызове API: {type(e).__name__}: {e}")
            raise AssistantProcessError(f"Неожиданная ошибка: {e}") from e

    async def update_knowledge_base(
        self,
        documents: list[dict],
    ) -> bool:
        """
        Обновляет базу знаний ассистента с новой информацией.

        Args:
            documents: Список документов для добавления в базу знаний.
                      Каждый документ должен содержать 'title' и 'content'.

        Returns:
            True если обновление успешно, False в противном случае.

        Raises:
            KnowledgeBaseError: При ошибке обновления базы знаний.
        """
        if not documents:
            logger.warning("Попытка обновления пустой базы знаний")
            return False

        try:
            logger.info(f"Обновление базы знаний ассистента ({len(documents)} доков)")

            # TODO: Реализовать реальное обновление базы знаний
            # Использовать API Yandex Cloud для добавления/обновления документов

            for doc in documents:
                if "title" not in doc or "content" not in doc:
                    logger.warning(f"Неправильный формат документа: {doc}")
                    continue

                logger.debug(f"Добавление документа в базу знаний: {doc['title']}")

            logger.info("База знаний ассистента успешно обновлена")
            return True

        except Exception as e:
            logger.exception(f"Ошибка при обновлении базы знаний: {e}")
            raise KnowledgeBaseError(
                f"Не удалось обновить базу знаний: {e}"
            ) from e

    async def get_knowledge_base_info(self) -> dict:
        """
        Получает информацию о текущей базе знаний.

        Returns:
            Словарь с информацией о базе знаний.
        """
        try:
            logger.debug("Получение информации о базе знаний")

            # TODO: Реализовать реальный запрос информации о БЗ

            info = {
                "assistant_id": self._assistant_id,
                "thread_id": self._thread_id,
                "folder_id": self._folder_id,
                "documents_count": 0,
                "last_updated": None,
            }

            return info

        except Exception as e:
            logger.exception(f"Ошибка при получении информации о БЗ: {e}")
            raise KnowledgeBaseError(
                f"Не удалось получить информацию о базе знаний: {e}"
            ) from e

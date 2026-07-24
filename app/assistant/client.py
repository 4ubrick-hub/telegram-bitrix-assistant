"""
Клиент для взаимодействия с Yandex AI Studio Assistant.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Optional

from openai import (
    APIConnectionError,
    APITimeoutError,
    AsyncOpenAI,
    RateLimitError,
)

from app.assistant.exceptions import (
    AssistantConnectionError,
    AssistantProcessError,
    KnowledgeBaseError,
)
from app.config.settings import settings

logger = logging.getLogger(__name__)


class YandexAssistantClient:
    """
    Клиент для работы с Yandex AI Studio Assistant.
    """

    def __init__(self) -> None:
        try:
            self._api_key = settings.yandex_api_key.get_secret_value()
            self._folder_id = settings.yandex_folder_id
            self._assistant_id = settings.yandex_assistant_id
            self._thread_id = settings.yandex_thread_id

            self._client = AsyncOpenAI(
                api_key=self._api_key,
                base_url="https://ai.api.cloud.yandex.net/v1",
                project=self._folder_id,
            )

            logger.info("Yandex Assistant Client инициализирован.")

        except Exception as e:
            raise AssistantConnectionError(
                f"Ошибка инициализации клиента: {e}"
            ) from e

    async def send_message(
        self,
        message: str,
        thread_id: Optional[str] = None,
    ) -> str:
        """
        Отправляет сообщение ассистенту.
        """

        thread_id = thread_id or self._thread_id

        try:
            answer = await self._call_assistant_api(
                message=message,
                thread_id=thread_id,
            )

            logger.info(
                "Получен ответ ассистента (%d символов)",
                len(answer),
            )

            return answer

        except Exception as e:
            logger.exception(
                "Ошибка при обработке сообщения: %s",
                e,
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
        Выполняет запрос к Yandex AI Studio.
        """

        max_attempts = 3

        for attempt in range(1, max_attempts + 1):

            try:

                logger.info(
                    "Запрос к Yandex AI Studio (%d/%d)",
                    attempt,
                    max_attempts,
                )

                response = await self._client.responses.create(
                    prompt={
                        "id": self._assistant_id,
                    },
                    input=message,
                )

                try:
                    return response.output_text.strip()
                except Exception:
                    logger.info("Полный ответ AI Studio: %s", response)
                    raise AssistantProcessError(
                        "Не удалось извлечь текст ответа."
                    )

            except RateLimitError:

                if attempt == max_attempts:
                    raise AssistantProcessError(
                        "Превышен лимит запросов."
                    )

                delay = 2 ** attempt

                logger.warning(
                    "Rate Limit. Повтор через %d сек.",
                    delay,
                )

                await asyncio.sleep(delay)

            except APITimeoutError:

                if attempt == max_attempts:
                    raise AssistantProcessError(
                        "Истекло время ожидания ответа."
                    )

                delay = 2 ** attempt

                logger.warning(
                    "Timeout. Повтор через %d сек.",
                    delay,
                )

                await asyncio.sleep(delay)

            except APIConnectionError as e:

                if attempt == max_attempts:
                    raise AssistantProcessError(
                        f"Ошибка соединения: {e}"
                    )

                delay = 2 ** attempt

                logger.warning(
                    "Ошибка соединения. Повтор через %d сек.",
                    delay,
                )

                await asyncio.sleep(delay)

            except Exception as e:
                raise AssistantProcessError(str(e)) from e
    async def update_knowledge_base(
        self,
        documents: list[dict],
    ) -> bool:
        """
        Заглушка для будущего обновления базы знаний.

        В текущей версии AI Studio документы добавляются через интерфейс
        или отдельный API, поэтому здесь пока ничего делать не требуется.
        """

        if not documents:
            logger.warning("Попытка обновить пустую базу знаний.")
            return False

        logger.info(
            "Получен запрос на обновление базы знаний (%d документов).",
            len(documents),
        )

        for doc in documents:
            logger.debug(
                "Документ: %s",
                doc.get("title", "<без названия>"),
            )

        logger.info(
            "Обновление базы знаний пока не реализовано."
        )

        return True

    async def get_knowledge_base_info(self) -> dict:
        """
        Возвращает информацию о текущем ассистенте.
        """

        return {
            "assistant_id": self._assistant_id,
            "thread_id": self._thread_id,
            "folder_id": self._folder_id,
            "documents_count": None,
            "last_updated": None,
        }
"""
Модуль для работы с GPT API.
Содержит абстракцию над OpenAI API с обработкой ошибок и retry-логикой.
"""

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from openai import OpenAI

from .exceptions import (
    GPTClientError,
    GPTRateLimitError,
    GPTServiceError,
)
from utils.logging_utils import get_model_response_logger

logger = logging.getLogger(__name__)


@dataclass
class GPTUsage:
    """Информация об использовании токенов."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


@dataclass
class GPTResponse:
    """Ответ от GPT API."""

    content: str
    usage: GPTUsage
    model: str
    finish_reason: str


class GPTClient:
    """
    Клиент для работы с GPT API с обработкой ошибок и retry-логикой.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "o4-mini",
        max_retries: int = 3,
        retry_delay: float = 1.0,
        enable_response_logging: Optional[bool] = None,
    ) -> None:
        """
        Инициализирует GPT клиент.

        Args:
            api_key: API ключ OpenAI
            model: Модель GPT для использования
            max_retries: Максимальное количество повторных попыток
            retry_delay: Задержка между попытками в секундах
            enable_response_logging: Включить детальное логирование ответов
                                   (по умолчанию True, можно отключить через MATH_IDE_DISABLE_MODEL_LOGGING)
        """
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Определяем, включать ли логирование ответов
        if enable_response_logging is None:
            # По умолчанию включаем, если не отключено через переменную окружения
            self.enable_response_logging = not os.getenv("MATH_IDE_DISABLE_MODEL_LOGGING", "").lower() in ("true", "1", "yes")
        else:
            self.enable_response_logging = enable_response_logging

        try:
            self.client = OpenAI(api_key=api_key)
            logger.info(f"Инициализация GPT клиента с моделью {model}")
            
            # Инициализируем логгер ответов модели
            if self.enable_response_logging:
                self.response_logger = get_model_response_logger()
                logger.info("Логирование ответов модели включено")
            else:
                self.response_logger = None
                logger.info("Логирование ответов модели отключено")
                
        except ImportError as e:
            raise GPTClientError(f"OpenAI библиотека не установлена: {str(e)}")
        except Exception as e:
            raise GPTServiceError(f"Ошибка инициализации OpenAI клиента: {str(e)}")

    def _make_request_with_retry(
        self, messages: List[Dict[str, str]], temperature: float = 0.3
    ) -> GPTResponse:
        """
        Выполняет запрос к GPT с retry-логикой.

        Args:
            messages: Список сообщений для GPT
            temperature: Температура генерации

        Returns:
            Ответ от GPT

        Raises:
            GPTClientError: При ошибках API
        """
        last_error: Optional[Exception] = None
        request_id: Optional[str] = None

        for attempt in range(self.max_retries):
            try:
                logger.debug(f"GPT запрос, попытка {attempt + 1}/{self.max_retries}")

                # Логируем запрос если включено логирование
                if self.enable_response_logging and self.response_logger and attempt == 0:
                    request_id = self.response_logger.log_request(
                        model=self.model,
                        messages=messages,
                        temperature=temperature
                    )

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,  # type: ignore
                    # temperature=temperature,
                )

                # Проверяем что ответ корректный
                if not response.choices or not response.choices[0].message.content:
                    raise GPTClientError("Пустой ответ от GPT API")

                content = response.choices[0].message.content.strip()

                # Безопасная обработка usage
                if response.usage is None:
                    usage = GPTUsage(
                        prompt_tokens=0, completion_tokens=0, total_tokens=0
                    )
                else:
                    usage = GPTUsage(
                        prompt_tokens=response.usage.prompt_tokens,
                        completion_tokens=response.usage.completion_tokens,
                        total_tokens=response.usage.total_tokens,
                    )

                logger.debug(f"GPT ответ получен. Токены: {usage.total_tokens}")

                # Логируем содержимое ответа
                # logger.info(f"Ответ модели {self.model}: {content_preview}")  # УДАЛЕНО: теперь только подробный лог
                logger.debug(f"Полный ответ: {content}")

                finish_reason = response.choices[0].finish_reason
                if finish_reason is None:
                    finish_reason = "stop"

                # Логируем успешный ответ
                if self.enable_response_logging and self.response_logger and request_id:
                    usage_dict = {
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens,
                    }
                    self.response_logger.log_response(
                        request_id=request_id,
                        content=content,
                        usage=usage_dict,
                        model=self.model,
                        finish_reason=finish_reason,
                    )

                return GPTResponse(
                    content=content,
                    usage=usage,
                    model=self.model,
                    finish_reason=finish_reason,
                )

            except Exception as e:
                last_error = e
                error_msg = str(e).lower()

                # Логируем ошибку если включено логирование
                if self.enable_response_logging and self.response_logger and request_id:
                    usage_dict = {
                        "prompt_tokens": 0,
                        "completion_tokens": 0,
                        "total_tokens": 0,
                    }
                    self.response_logger.log_response(
                        request_id=request_id,
                        content="",
                        usage=usage_dict,
                        model=self.model,
                        finish_reason="error",
                        error=str(e),
                    )

                # Определяем тип ошибки
                if "rate limit" in error_msg or "quota" in error_msg:
                    logger.warning(f"Rate limit превышен, попытка {attempt + 1}")
                    if attempt < self.max_retries - 1:
                        time.sleep(
                            self.retry_delay * (2**attempt)
                        )  # Экспоненциальная задержка
                        continue
                    raise GPTRateLimitError(f"Превышен лимит запросов: {str(e)}")

                elif "connection" in error_msg or "timeout" in error_msg:
                    logger.warning(f"Проблема с подключением, попытка {attempt + 1}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    raise GPTServiceError(f"Ошибка подключения к API: {str(e)}")

                else:
                    # Для других ошибок не повторяем
                    logger.error(f"GPT API ошибка: {str(e)}")
                    raise GPTClientError(f"Ошибка GPT API: {str(e)}")

        if last_error is not None:
            raise GPTClientError(
                f"Не удалось выполнить запрос после {self.max_retries} попыток: {str(last_error)}"
            )
        # Если last_error is None, это означает, что цикл не выполнился ни разу
        raise GPTClientError("Не удалось выполнить запрос: цикл не выполнился")

    def generate_completion(self, prompt: str, temperature: float = 0.3) -> GPTResponse:
        """
        Генерирует ответ GPT для данного промпта.

        Args:
            prompt: Промпт для GPT
            temperature: Температура генерации

        Returns:
            Ответ от GPT
        """
        messages = [{"role": "user", "content": prompt}]
        return self._make_request_with_retry(messages, temperature)

    def chat_completion(
        self, messages: List[Dict[str, str]], temperature: float = 0.3
    ) -> GPTResponse:
        """
        Выполняет chat completion запрос.

        Args:
            messages: Список сообщений в формате [{"role": "user", "content": "..."}]
            temperature: Температура генерации

        Returns:
            Ответ от GPT
        """
        return self._make_request_with_retry(messages, temperature)

    def get_model_info(self) -> Dict[str, Any]:
        """
        Возвращает информацию о модели.

        Returns:
            Словарь с информацией о модели
        """
        return {
            "model": self.model,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
        }

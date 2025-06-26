"""
Модуль для работы с GPT API.
Содержит абстракцию над OpenAI API с обработкой ошибок и retry-логикой.
"""

import logging
import time
from typing import Optional, Dict, Any, List, Union, cast
from dataclasses import dataclass

from .exceptions import GPTError, GPTConnectionError, GPTRateLimitError, GPTInvalidResponseError

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
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo", 
                 max_retries: int = 3, retry_delay: float = 1.0) -> None:
        """
        Инициализирует GPT клиент.
        
        Args:
            api_key: API ключ OpenAI
            model: Модель GPT для использования
            max_retries: Максимальное количество повторных попыток
            retry_delay: Задержка между попытками в секундах
        """
        self.model = model
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            logger.info(f"Инициализация GPT клиента с моделью {model}")
        except ImportError as e:
            raise GPTError(f"OpenAI библиотека не установлена: {str(e)}")
        except Exception as e:
            raise GPTConnectionError(f"Ошибка инициализации OpenAI клиента: {str(e)}")
    
    def _make_request_with_retry(self, messages: List[Dict[str, str]], 
                                temperature: float = 0.3) -> GPTResponse:
        """
        Выполняет запрос к GPT с retry-логикой.
        
        Args:
            messages: Список сообщений для GPT
            temperature: Температура генерации
            
        Returns:
            Ответ от GPT
            
        Raises:
            GPTError: При ошибках API
        """
        last_error: Optional[Exception] = None
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"GPT запрос, попытка {attempt + 1}/{self.max_retries}")
                
                # Приводим сообщения к правильному типу для OpenAI API
                typed_messages = cast(List[Dict[str, str]], messages)
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=typed_messages,
                    temperature=temperature
                )
                
                # Проверяем что ответ корректный
                if not response.choices or not response.choices[0].message.content:
                    raise GPTInvalidResponseError("Пустой ответ от GPT API")
                
                content = response.choices[0].message.content.strip()
                
                # Безопасная обработка usage
                if response.usage is None:
                    usage = GPTUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
                else:
                    usage = GPTUsage(
                        prompt_tokens=response.usage.prompt_tokens,
                        completion_tokens=response.usage.completion_tokens,
                        total_tokens=response.usage.total_tokens
                    )
                
                logger.debug(f"GPT ответ получен. Токены: {usage.total_tokens}")
                
                finish_reason = response.choices[0].finish_reason
                if finish_reason is None:
                    finish_reason = "stop"
                
                return GPTResponse(
                    content=content,
                    usage=usage,
                    model=self.model,
                    finish_reason=finish_reason
                )
                
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                
                # Определяем тип ошибки
                if "rate limit" in error_msg or "quota" in error_msg:
                    logger.warning(f"Rate limit превышен, попытка {attempt + 1}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay * (2 ** attempt))  # Экспоненциальная задержка
                        continue
                    raise GPTRateLimitError(f"Превышен лимит запросов: {str(e)}")
                    
                elif "connection" in error_msg or "timeout" in error_msg:
                    logger.warning(f"Проблема с подключением, попытка {attempt + 1}")
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                    raise GPTConnectionError(f"Ошибка подключения к API: {str(e)}")
                    
                else:
                    # Для других ошибок не повторяем
                    logger.error(f"GPT API ошибка: {str(e)}")
                    raise GPTError(f"Ошибка GPT API: {str(e)}")
        
        # Если все попытки неудачны
        if last_error is not None:
            raise GPTError(f"Не удалось выполнить запрос после {self.max_retries} попыток: {str(last_error)}")
        else:
            raise GPTError(f"Не удалось выполнить запрос после {self.max_retries} попыток")
    
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
    
    def chat_completion(self, messages: List[Dict[str, str]], 
                       temperature: float = 0.3) -> GPTResponse:
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
            "retry_delay": self.retry_delay
        } 
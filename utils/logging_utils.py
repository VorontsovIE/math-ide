"""
Утилиты для настройки логирования.
Содержит функции для настройки цветного логирования и форматирования.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def setup_logging(level: str = "INFO", use_colors: bool = True) -> None:
    """
    Настраивает логирование для приложения.

    Args:
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
        use_colors: Использовать цветное логирование
    """
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        level=getattr(logging, level.upper()),
    )

    if use_colors:
        try:
            import coloredlogs

            coloredlogs.install(
                level=level.upper(),
                fmt="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
            )
        except ImportError:
            logging.getLogger(__name__).info(
                "coloredlogs не установлен. Используется стандартное логирование."
            )


def get_logger(name: str) -> logging.Logger:
    """
    Создает логгер с заданным именем.

    Args:
        name: Имя логгера

    Returns:
        Настроенный логгер
    """
    return logging.getLogger(name)


class ModelResponseLogger:
    """
    Логгер для детального логирования ответов модели.
    Сохраняет запросы и ответы в структурированном виде.
    """
    
    def __init__(self, log_dir: str = "logs/model_responses"):
        """
        Инициализирует логгер ответов модели.
        
        Args:
            log_dir: Директория для сохранения логов
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = get_logger("model_responses")
        
    def log_request(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        request_id: Optional[str] = None,
    ) -> str:
        """
        Логирует запрос к модели.
        
        Args:
            model: Название модели
            messages: Список сообщений
            temperature: Температура генерации
            request_id: ID запроса (генерируется автоматически если не указан)
            
        Returns:
            ID запроса для связи с ответом
        """
        if request_id is None:
            request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
            
        log_data = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        
        # Логируем в файл
        log_file = self.log_dir / f"{request_id}_request.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
            
        # Логируем в консоль
        self.logger.info(f"Запрос к модели {model} (ID: {request_id})")
        self.logger.debug(f"Сообщения: {len(messages)} шт.")
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content_preview = msg.get("content", "")[:100] + "..." if len(msg.get("content", "")) > 100 else msg.get("content", "")
            self.logger.debug(f"  {i+1}. {role}: {content_preview}")
            
        return request_id
        
    def log_response(
        self,
        request_id: str,
        content: str,
        usage: Dict[str, int],
        model: str,
        finish_reason: str,
        error: Optional[str] = None,
    ) -> None:
        """
        Логирует ответ модели.
        
        Args:
            request_id: ID запроса
            content: Содержимое ответа
            usage: Информация об использовании токенов
            model: Название модели
            finish_reason: Причина завершения
            error: Ошибка, если есть
        """
        log_data = {
            "request_id": request_id,
            "timestamp": datetime.now().isoformat(),
            "model": model,
            "content": content,
            "usage": usage,
            "finish_reason": finish_reason,
            "error": error,
        }
        
        # Логируем в файл
        log_file = self.log_dir / f"{request_id}_response.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
            
        # Логируем в консоль
        if error:
            self.logger.error(f"Ошибка ответа модели {model} (ID: {request_id}): {error}")
        else:
            self.logger.info(f"Ответ модели {model} (ID: {request_id})")
            self.logger.info(f"Токены: промпт={usage.get('prompt_tokens', 0)}, "
                           f"ответ={usage.get('completion_tokens', 0)}, "
                           f"всего={usage.get('total_tokens', 0)}")
            self.logger.info(f"Причина завершения: {finish_reason}")
            
            # Логируем содержимое ответа
            content_preview = content[:200] + "..." if len(content) > 200 else content
            self.logger.debug(f"Содержимое ответа: {content_preview}")
            
    def log_complete_interaction(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float,
        content: str,
        usage: Dict[str, int],
        finish_reason: str,
        error: Optional[str] = None,
    ) -> str:
        """
        Логирует полное взаимодействие с моделью (запрос + ответ).
        
        Args:
            model: Название модели
            messages: Список сообщений
            temperature: Температура генерации
            content: Содержимое ответа
            usage: Информация об использовании токенов
            finish_reason: Причина завершения
            error: Ошибка, если есть
            
        Returns:
            ID запроса
        """
        request_id = self.log_request(model, messages, temperature)
        self.log_response(request_id, content, usage, model, finish_reason, error)
        return request_id


def get_model_response_logger(log_dir: str = "logs/model_responses") -> ModelResponseLogger:
    """
    Создает и возвращает логгер ответов модели.
    
    Args:
        log_dir: Директория для сохранения логов
        
    Returns:
        Настроенный логгер ответов модели
    """
    return ModelResponseLogger(log_dir)

"""
Пример использования логирования ответов модели.
"""

import os
import tempfile
from pathlib import Path

from utils.logging_utils import get_model_response_logger


def example_basic_logging():
    """Пример базового логирования."""
    print("=== Пример базового логирования ===")
    
    # Создаем временную директорию для логов
    with tempfile.TemporaryDirectory() as temp_dir:
        logger = get_model_response_logger(temp_dir)
        
        # Пример запроса
        messages = [
            {"role": "system", "content": "Ты помощник по математике."},
            {"role": "user", "content": "Реши уравнение: 2x + 3 = 7"}
        ]
        
        # Логируем запрос
        request_id = logger.log_request(
            model="gpt-4",
            messages=messages,
            temperature=0.7
        )
        print(f"Создан запрос с ID: {request_id}")
        
        # Логируем ответ
        usage = {
            "prompt_tokens": 25,
            "completion_tokens": 50,
            "total_tokens": 75
        }
        
        logger.log_response(
            request_id=request_id,
            content="Для решения уравнения 2x + 3 = 7:\n1) Вычитаем 3 с обеих сторон: 2x = 4\n2) Делим на 2: x = 2\nОтвет: x = 2",
            usage=usage,
            model="gpt-4",
            finish_reason="stop"
        )
        print(f"Создан ответ для запроса: {request_id}")
        
        # Показываем созданные файлы
        log_files = list(Path(temp_dir).glob("*.json"))
        print(f"Создано файлов логов: {len(log_files)}")
        for file in log_files:
            print(f"  - {file.name}")


def example_complete_interaction():
    """Пример полного взаимодействия."""
    print("\n=== Пример полного взаимодействия ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        logger = get_model_response_logger(temp_dir)
        
        messages = [
            {"role": "user", "content": "Упрости выражение: (x + 2)(x - 2)"}
        ]
        
        usage = {
            "prompt_tokens": 15,
            "completion_tokens": 30,
            "total_tokens": 45
        }
        
        # Логируем полное взаимодействие одним вызовом
        request_id = logger.log_complete_interaction(
            model="gpt-4",
            messages=messages,
            temperature=0.5,
            content="(x + 2)(x - 2) = x² - 4 (по формуле разности квадратов)",
            usage=usage,
            finish_reason="stop"
        )
        
        print(f"Создано полное взаимодействие с ID: {request_id}")
        
        # Показываем файлы
        log_files = list(Path(temp_dir).glob("*.json"))
        for file in sorted(log_files):
            print(f"  - {file.name}")


def example_error_logging():
    """Пример логирования ошибок."""
    print("\n=== Пример логирования ошибок ===")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        logger = get_model_response_logger(temp_dir)
        
        # Логируем запрос
        request_id = logger.log_request(
            model="gpt-4",
            messages=[{"role": "user", "content": "Тестовый запрос"}],
            temperature=0.7
        )
        
        # Логируем ошибку
        logger.log_response(
            request_id=request_id,
            content="",
            usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
            model="gpt-4",
            finish_reason="error",
            error="Rate limit exceeded"
        )
        
        print(f"Создан лог ошибки для запроса: {request_id}")


def example_environment_variable():
    """Пример использования переменной окружения."""
    print("\n=== Пример переменной окружения ===")
    
    # Показываем текущее состояние
    current_value = os.getenv("MATH_IDE_DISABLE_MODEL_LOGGING")
    print(f"Текущее значение MATH_IDE_DISABLE_MODEL_LOGGING: {current_value}")
    
    # Демонстрируем, как отключить логирование
    print("Для отключения логирования установите:")
    print("export MATH_IDE_DISABLE_MODEL_LOGGING=true")
    
    # Демонстрируем, как включить логирование
    print("Для включения логирования:")
    print("unset MATH_IDE_DISABLE_MODEL_LOGGING")
    print("или")
    print("export MATH_IDE_DISABLE_MODEL_LOGGING=false")


if __name__ == "__main__":
    print("Демонстрация логирования ответов модели\n")
    
    example_basic_logging()
    example_complete_interaction()
    example_error_logging()
    example_environment_variable()
    
    print("\n=== Завершение демонстрации ===")
    print("Логи сохраняются в директории logs/model_responses/")
    print("Каждый запрос создает два файла:")
    print("  - {request_id}_request.json - запрос")
    print("  - {request_id}_response.json - ответ") 
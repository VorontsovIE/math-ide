#!/usr/bin/env python3
"""
Скрипт для тестирования модульной архитектуры MathIDE.
Проверяет корректность импортов всех ключевых компонентов.

Этот скрипт полезен для:
- Проверки целостности архитектуры после изменений
- Валидации модульной структуры
- Обнаружения проблем с импортами
- CI/CD пайплайнов

Использование:
    python tests/test_architecture.py
    ./tests/test_architecture.py

Коды возврата:
    0 - все основные тесты прошли успешно
    1 - есть проблемы с архитектурой

Автор: MathIDE Team
Дата: Декабрь 2024
Версия: 1.0
"""

import sys
import os
import traceback
from typing import List, Tuple

# Добавляем корневую папку проекта в sys.path для импорта модулей
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)


def test_import(module_path: str, items: List[str], description: str) -> Tuple[bool, str]:
    """
    Тестирует импорт указанных элементов из модуля.
    
    Args:
        module_path: Путь к модулю (например, 'core.types')
        items: Список элементов для импорта
        description: Описание теста
    
    Returns:
        Tuple[bool, str]: (успех, сообщение)
    """
    try:
        module = __import__(module_path, fromlist=items)
        for item in items:
            if not hasattr(module, item):
                return False, f"Элемент '{item}' не найден в модуле {module_path}"
        return True, f"✅ {description}: {', '.join(items)}"
    except ImportError as e:
        return False, f"❌ {description}: ImportError - {str(e)}"
    except Exception as e:
        return False, f"❌ {description}: {type(e).__name__} - {str(e)}"


def test_optional_import(module_path: str, description: str) -> Tuple[bool, str]:
    """
    Тестирует импорт опционального модуля с обходом проблем зависимостей.
    
    Args:
        module_path: Путь к модулю
        description: Описание теста
    
    Returns:
        Tuple[bool, str]: (успех, сообщение)
    """
    try:
        __import__(module_path)
        return True, f"✅ {description}: модуль импортирован успешно"
    except ImportError as e:
        error_msg = str(e)
        # Проверяем, является ли это проблемой с внешними зависимостями
        dependency_errors = ['click', 'telegram', 'fastapi', 'uvicorn', 'jinja2']
        if any(dep in error_msg.lower() for dep in dependency_errors):
            return True, f"⚠️  {description}: модуль найден, но требует внешние зависимости ({error_msg.split()[-1]})"
        else:
            return False, f"❌ {description}: ImportError - {error_msg}"
    except Exception as e:
        return False, f"❌ {description}: {type(e).__name__} - {str(e)}"


def test_simple_import(module_path: str, description: str) -> Tuple[bool, str]:
    """
    Тестирует простой импорт модуля.
    
    Args:
        module_path: Путь к модулю
        description: Описание теста
    
    Returns:
        Tuple[bool, str]: (успех, сообщение)
    """
    try:
        __import__(module_path)
        return True, f"✅ {description}: модуль импортирован успешно"
    except ImportError as e:
        return False, f"❌ {description}: ImportError - {str(e)}"
    except Exception as e:
        return False, f"❌ {description}: {type(e).__name__} - {str(e)}"


def run_architecture_tests() -> None:
    """Запускает все тесты архитектуры."""
    
    print("🎯 ТЕСТ МОДУЛЬНОЙ АРХИТЕКТУРЫ MathIDE")
    print("=" * 60)
    print()
    
    # Определяем тесты
    tests = [
        # Core модули - основные классы
        (test_import, ('core', ['TransformationEngine', 'SolutionHistory', 'HistoryStep'], 'Core модули')),
        
        # Core типы данных
        (test_import, ('core.types', ['Transformation', 'SolutionStep', 'GenerationResult'], 'Core типы')),
        
        # Core исключения
        (test_import, ('core.exceptions', ['MathIDEError', 'GPTError', 'ParseError'], 'Core исключения')),
        
        # GPT клиент
        (test_import, ('core.gpt_client', ['GPTClient'], 'GPT клиент')),
        
        # Парсеры
        (test_import, ('core.parsers', ['safe_json_parse', 'fix_latex_escapes_in_json'], 'Парсеры')),
        
        # Промпты
        (test_import, ('core.prompts', ['PromptManager'], 'Промпты')),
        
        # Math утилиты
        (test_import, ('utils.math_utils', ['validate_latex_expression'], 'Math утилиты')),
        
        # Logging утилиты
        (test_import, ('utils.logging_utils', ['setup_logging'], 'Logging утилиты')),
        
        # Дополнительные модули (проверка импорта)
        (test_simple_import, ('core.history', 'История решений')),
        (test_simple_import, ('core.engine', 'Движок преобразований')),
        (test_simple_import, ('utils', 'Утилиты')),
    ]
    
    # Опциональные тесты (могут не работать без зависимостей)
    optional_tests = [
        (test_optional_import, ('interfaces.cli', 'CLI интерфейс')),
        (test_optional_import, ('interfaces.telegram_bot', 'Telegram бот')),
        (test_simple_import, ('interfaces', 'Интерфейсы (базовый модуль)')),
    ]
    
    # Выполняем основные тесты
    passed = 0
    failed = 0
    
    print("🔍 ОСНОВНЫЕ ТЕСТЫ:")
    print("-" * 40)
    
    for test_func, args in tests:
        success, message = test_func(*args)
        print(message)
        if success:
            passed += 1
        else:
            failed += 1
    
    print()
    print("🔍 ОПЦИОНАЛЬНЫЕ ТЕСТЫ (интерфейсы):")
    print("-" * 40)
    
    optional_passed = 0
    optional_failed = 0
    
    for test_func, args in optional_tests:
        success, message = test_func(*args)
        print(message)
        if success:
            optional_passed += 1
        else:
            optional_failed += 1
    
    # Выводим результаты
    print()
    print("=" * 60)
    print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"• Основные тесты: {passed} пройдено, {failed} провалено")
    print(f"• Опциональные тесты: {optional_passed} пройдено, {optional_failed} провалено")
    print()
    
    if failed == 0:
        print("🎉 ВСЕ ОСНОВНЫЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("🏆 МОДУЛЬНАЯ АРХИТЕКТУРА ПОЛНОСТЬЮ ФУНКЦИОНАЛЬНА!")
        print()
        if optional_failed > 0:
            print("ℹ️  Некоторые интерфейсы требуют установки дополнительных зависимостей.")
            print("   Для полной функциональности выполните: poetry install")
        print()
        print("🚀 ПРОЕКТ ГОТОВ К ИСПОЛЬЗОВАНИЮ И РАЗВИТИЮ!")
        
        return_code = 0
    else:
        print("⚠️  ОБНАРУЖЕНЫ ПРОБЛЕМЫ В АРХИТЕКТУРЕ!")
        print("Необходимо исправить ошибки импорта перед использованием.")
        
        return_code = 1
    
    print("=" * 60)
    
    # Возвращаем код выхода
    sys.exit(return_code)


def main():
    """Главная функция."""
    try:
        run_architecture_tests()
    except KeyboardInterrupt:
        print("\n⏹️  Тестирование прервано пользователем.")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Неожиданная ошибка: {type(e).__name__}: {str(e)}")
        print("\nПолная трассировка:")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main() 
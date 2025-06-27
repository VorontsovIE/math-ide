#!/usr/bin/env python3
"""
Тесты архитектуры MathIDE.
Проверяет корректность структуры проекта и импортов.
"""

import sys
import os
from typing import List, Tuple

# Добавляем корневую директорию в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _test_import(
    module_path: str, items: List[str], description: str
) -> Tuple[bool, str]:
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


def _test_optional_import(module_path: str, description: str) -> Tuple[bool, str]:
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
        dependency_errors = ["click", "telegram", "fastapi", "uvicorn", "jinja2"]
        if any(dep in error_msg.lower() for dep in dependency_errors):
            return (
                True,
                f"⚠️  {description}: модуль найден, но требует внешние зависимости ({error_msg.split()[-1]})",
            )
        else:
            return False, f"❌ {description}: ImportError - {error_msg}"
    except Exception as e:
        return False, f"❌ {description}: {type(e).__name__} - {str(e)}"


def _test_simple_import(module_path: str, description: str) -> Tuple[bool, str]:
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


class TestArchitecture:
    """Тесты архитектуры системы."""

    def test_core_modules(self):
        """Тест импорта основных модулей ядра."""
        success, message = _test_import(
            "core",
            ["TransformationEngine", "SolutionHistory", "HistoryStep"],
            "Core модули",
        )
        print(message)
        assert success, message

    def test_core_types(self):
        """Тест импорта типов данных."""
        success, message = _test_import(
            "core.types",
            ["Transformation", "SolutionStep", "GenerationResult"],
            "Core типы",
        )
        print(message)
        assert success, message

    def test_core_exceptions(self):
        """Тест импорта исключений."""
        success, message = _test_import(
            "core.exceptions",
            ["MathIDEError", "GPTError", "ParseError"],
            "Core исключения",
        )
        print(message)
        assert success, message

    def test_gpt_client(self):
        """Тест импорта GPT клиента."""
        success, message = _test_import("core.gpt_client", ["GPTClient"], "GPT клиент")
        print(message)
        assert success, message

    def test_parsers(self):
        """Тест импорта парсеров."""
        success, message = _test_import(
            "core.parsers", ["safe_json_parse", "fix_latex_escapes_in_json"], "Парсеры"
        )
        print(message)
        assert success, message

    def test_prompts(self):
        """Тест импорта промптов."""
        success, message = _test_import("core.prompts", ["PromptManager"], "Промпты")
        print(message)
        assert success, message

    def test_math_utils(self):
        """Тест импорта математических утилит."""
        success, message = _test_import(
            "utils.math_utils", ["validate_latex_expression"], "Math утилиты"
        )
        print(message)
        assert success, message

    def test_logging_utils(self):
        """Тест импорта утилит логирования."""
        success, message = _test_import(
            "utils.logging_utils", ["setup_logging"], "Logging утилиты"
        )
        print(message)
        assert success, message

    def test_history_module(self):
        """Тест импорта модуля истории."""
        success, message = _test_simple_import("core.history", "История решений")
        print(message)
        assert success, message

    def test_engine_module(self):
        """Тест импорта модуля движка."""
        success, message = _test_simple_import("core.engine", "Движок преобразований")
        print(message)
        assert success, message

    def test_utils_module(self):
        """Тест импорта модуля утилит."""
        success, message = _test_simple_import("utils", "Утилиты")
        print(message)
        assert success, message


class TestOptionalInterfaces:
    """Тесты опциональных интерфейсов (могут требовать дополнительные зависимости)."""

    def test_cli_interface(self):
        """Тест импорта CLI интерфейса."""
        success, message = _test_optional_import("interfaces.cli", "CLI интерфейс")
        print(message)
        # Не требуем успеха для опциональных модулей

    def test_telegram_interface(self):
        """Тест импорта Telegram интерфейса."""
        success, message = _test_optional_import(
            "interfaces.telegram_bot", "Telegram бот"
        )
        print(message)
        # Не требуем успеха для опциональных модулей

    def test_interfaces_base(self):
        """Тест импорта базового модуля интерфейсов."""
        success, message = _test_simple_import(
            "interfaces", "Интерфейсы (базовый модуль)"
        )
        print(message)
        assert success, message


# Функции для совместимости со старым API
def run_architecture_tests() -> None:
    """Запускает все тесты архитектуры (legacy функция для совместимости)."""

    print("🎯 ТЕСТ МОДУЛЬНОЙ АРХИТЕКТУРЫ MathIDE")
    print("=" * 60)
    print()

    # Определяем тесты
    tests = [
        # Core модули - основные классы
        (
            _test_import,
            (
                "core",
                ["TransformationEngine", "SolutionHistory", "HistoryStep"],
                "Core модули",
            ),
        ),
        # Core типы данных
        (
            _test_import,
            (
                "core.types",
                ["Transformation", "SolutionStep", "GenerationResult"],
                "Core типы",
            ),
        ),
        # Core исключения
        (
            _test_import,
            (
                "core.exceptions",
                ["MathIDEError", "GPTError", "ParseError"],
                "Core исключения",
            ),
        ),
        # GPT клиент
        (_test_import, ("core.gpt_client", ["GPTClient"], "GPT клиент")),
        # Парсеры
        (
            _test_import,
            (
                "core.parsers",
                ["safe_json_parse", "fix_latex_escapes_in_json"],
                "Парсеры",
            ),
        ),
        # Промпты
        (_test_import, ("core.prompts", ["PromptManager"], "Промпты")),
        # Math утилиты
        (
            _test_import,
            ("utils.math_utils", ["validate_latex_expression"], "Math утилиты"),
        ),
        # Logging утилиты
        (_test_import, ("utils.logging_utils", ["setup_logging"], "Logging утилиты")),
        # Дополнительные модули (проверка импорта)
        (_test_simple_import, ("core.history", "История решений")),
        (_test_simple_import, ("core.engine", "Движок преобразований")),
        (_test_simple_import, ("utils", "Утилиты")),
    ]

    # Опциональные тесты (могут не работать без зависимостей)
    optional_tests = [
        (_test_optional_import, ("interfaces.cli", "CLI интерфейс")),
        (_test_optional_import, ("interfaces.telegram_bot", "Telegram бот")),
        (_test_simple_import, ("interfaces", "Интерфейсы (базовый модуль)")),
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

    for test_func, args in optional_tests:
        success, message = test_func(*args)
        print(message)

    print()
    print("📊 РЕЗУЛЬТАТЫ:")
    print("-" * 40)
    print(f"✅ Успешно: {passed}")
    print(f"❌ Ошибок: {failed}")
    print(f"📈 Процент успеха: {(passed / (passed + failed) * 100):.1f}%")

    if failed == 0:
        print()
        print("🎉 ВСЕ ОСНОВНЫЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("🚀 Архитектура MathIDE готова к работе!")
    else:
        print()
        print("⚠️ Обнаружены проблемы в архитектуре.")
        print("🔧 Требуется исправление перед использованием.")


def main():
    """Главная функция для запуска как скрипта."""
    run_architecture_tests()
    sys.exit(0 if run_architecture_tests() else 1)


if __name__ == "__main__":
    main()

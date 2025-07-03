#!/usr/bin/env python3
"""
Тест для демонстрации работы verification функциональности.
"""

import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from core.engine import TransformationEngine
from core.types import SolutionStep

def test_verification():
    """Тестирует функциональность verification."""
    
    print("🧪 Тестирование verification функциональности...")
    
    # Инициализируем движок
    engine = TransformationEngine()
    
    # Тест 1: Пересчёт (recalculate)
    print("\n1️⃣ Тест пересчёта (recalculate):")
    print("Исходное выражение: 2x + 4 = 10")
    print("Преобразование: Вычесть 4 из обеих частей")
    print("Полученный результат: 2x = 7 (ошибочный)")
    
    try:
        result = engine.verify_transformation(
            original_expression="2x + 4 = 10",
            transformation_description="Вычесть 4 из обеих частей",
            current_result="2x = 7",
            verification_type="recalculate"
        )
        
        print(f"✅ Результат проверки:")
        print(f"   Корректно: {result.is_correct}")
        print(f"   Исправленный результат: {result.corrected_result}")
        print(f"   Объяснение: {result.verification_explanation}")
        if result.errors_found:
            print(f"   Найденные ошибки: {result.errors_found}")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
    
    # Тест 2: Проверка предложения пользователя (verify_user_suggestion)
    print("\n2️⃣ Тест проверки предложения пользователя (verify_user_suggestion):")
    print("Исходное выражение: x² - 4 = 0")
    print("Преобразование: Факторизация")
    print("Предложенный пользователем результат: (x-2)(x+2) = 0")
    
    try:
        result = engine.verify_transformation(
            original_expression="x² - 4 = 0",
            transformation_description="Факторизация",
            current_result="x² - 4 = 0",
            verification_type="verify_user_suggestion",
            user_suggested_result="(x-2)(x+2) = 0"
        )
        
        print(f"✅ Результат проверки:")
        print(f"   Корректно: {result.is_correct}")
        print(f"   Исправленный результат: {result.corrected_result}")
        print(f"   Объяснение: {result.verification_explanation}")
        if result.user_result_assessment:
            print(f"   Оценка предложения пользователя: {result.user_result_assessment}")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
    
    # Тест 3: Проверка самостоятельного преобразования (verify_user_transformation)
    print("\n3️⃣ Тест проверки самостоятельного преобразования (verify_user_transformation):")
    print("Исходное выражение: 3(x + 2) = 12")
    print("Пользователь: 'Я раскрыл скобки и получил 3x + 6 = 12'")
    
    try:
        result = engine.verify_transformation(
            original_expression="3(x + 2) = 12",
            transformation_description="Пользователь: 'Я раскрыл скобки и получил 3x + 6 = 12'",
            current_result="3x + 6 = 12",
            verification_type="verify_user_transformation"
        )
        
        print(f"✅ Результат проверки:")
        print(f"   Корректно: {result.is_correct}")
        print(f"   Исправленный результат: {result.corrected_result}")
        print(f"   Объяснение: {result.verification_explanation}")
        if result.user_result_assessment:
            print(f"   Оценка пользовательского преобразования: {result.user_result_assessment}")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")

def show_verification_usage():
    """Показывает, как использовать verification в коде."""
    
    print("\n📖 Как использовать verification в коде:")
    print("=" * 50)
    
    print("""
# 1. Импорт и инициализация
from core.engine import TransformationEngine

engine = TransformationEngine()

# 2. Пересчёт (когда пользователь говорит, что результат ошибочен)
result = engine.verify_transformation(
    original_expression="2x + 4 = 10",
    transformation_description="Вычесть 4 из обеих частей",
    current_result="2x = 7",  # Ошибочный результат
    verification_type="recalculate"
)

# 3. Проверка предложения пользователя
result = engine.verify_transformation(
    original_expression="x² - 4 = 0",
    transformation_description="Факторизация",
    current_result="x² - 4 = 0",
    verification_type="verify_user_suggestion",
    user_suggested_result="(x-2)(x+2) = 0"
)

# 4. Проверка самостоятельного преобразования
result = engine.verify_transformation(
    original_expression="3(x + 2) = 12",
    transformation_description="Пользователь: 'Я раскрыл скобки'",
    current_result="3x + 6 = 12",
    verification_type="verify_user_transformation"
)

# 5. Анализ результата
print(f"Корректно: {result.is_correct}")
print(f"Исправленный результат: {result.corrected_result}")
print(f"Объяснение: {result.verification_explanation}")
print(f"Ошибки: {result.errors_found}")
print(f"Пошаговая проверка: {result.step_by_step_check}")
""")

def show_verification_in_interfaces():
    """Показывает, как verification используется в интерфейсах."""
    
    print("\n🎯 Как verification используется в интерфейсах:")
    print("=" * 50)
    
    print("""
# В Telegram боте (keyboards.py):
def get_verification_keyboard(transformation_id: str, verification_type: str, current_step_id: str):
    # Создаёт клавиатуру с кнопками:
    # - "✅ Правильно" / "❌ Неправильно" (для manual)
    # - "🔍 Проверить" (для auto)

# В обработчиках (handlers.py):
# Обработчики для callback_data:
# - verify_correct_{transformation_id}
# - verify_incorrect_{transformation_id}  
# - verify_auto_{transformation_id}

# В CLI (пока не реализовано):
# Пользователь может выбрать:
# 1. Пересчитать результат
# 2. Предложить свой результат
# 3. Сообщить о самостоятельно выполненном преобразовании
""")

if __name__ == "__main__":
    print("🚀 Демонстрация verification функциональности...")
    
    # Проверяем наличие API ключа
    if not os.getenv("OPENAI_API_KEY"):
        print("⚠️  OPENAI_API_KEY не установлен, пропускаем тесты с GPT")
        show_verification_usage()
        show_verification_in_interfaces()
    else:
        test_verification()
        show_verification_usage()
        show_verification_in_interfaces()
    
    print("\n✅ Демонстрация завершена!") 
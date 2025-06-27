#!/usr/bin/env python3
"""
Тест для функции извлечения математических выражений.
"""

import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interfaces.telegram.renderers import extract_math_expression


def test_extract_math_expression():
    """Тестирует функцию извлечения математических выражений."""
    
    test_cases = [
        # Простые случаи
        ("2(x + 1) = 4", "2(x + 1) = 4"),
        ("Решите уравнение 2(x + 1) = 4", "2(x + 1) = 4"),
        ("Пожалуйста, решите 2(x + 1) = 4", "2(x + 1) = 4"),
        
        # Сложные случаи
        ("Найдите корни уравнения x² + 5x + 6 = 0", "x² + 5x + 6 = 0"),
        ("Упростите выражение (a + b)²", "(a + b)²"),
        
        # С LaTeX командами
        ("Вычислите \\frac{1}{2} + \\frac{1}{3}", "\\frac{1}{2} + \\frac{1}{3}"),
        
        # LaTeX блоки
        ("Решите уравнение $2x + 3 = 7$", "2x + 3 = 7"),
        ("Найдите корни $$x^2 + 5x + 6 = 0$$", "x^2 + 5x + 6 = 0"),
        
        # Без математических выражений
        ("Привет, как дела?", "Привет, как дела?"),
        ("", ""),
        
        # Дополнительные тесты
        ("Упростите 3x + 2y - 5", "3x + 2y - 5"),
        ("Решите систему x + y = 5, x - y = 1", "x + y = 5, x - y = 1"),
    ]
    
    print("Тестирование функции extract_math_expression:")
    print("=" * 50)
    
    passed = 0
    total = len(test_cases)
    
    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = extract_math_expression(input_text)
        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        print(f"{i}. {status} Вход: '{input_text}'")
        print(f"   Ожидалось: '{expected}'")
        print(f"   Получено:  '{result}'")
        print()
    
    print(f"Результат: {passed}/{total} тестов прошли успешно")
    return passed == total


if __name__ == "__main__":
    success = test_extract_math_expression()
    sys.exit(0 if success else 1) 
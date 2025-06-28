#!/usr/bin/env python3
"""
Тест для функции извлечения математических выражений.
"""

import sys
import os

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from interfaces.telegram.renderers import extract_math_expression, convert_superscript_subscript_to_latex


def test_convert_superscript_subscript():
    """Тестирует функцию преобразования надстрочных/подстрочных символов."""
    
    test_cases = [
        # Надстрочные символы
        ("x²", "x^2"),
        ("x³", "x^3"),
        ("x² + y³", "x^2 + y^3"),
        ("x³²", "x^{32}"),  # Последовательные символы - правильный LaTeX формат
        ("2⁴", "2^4"),
        
        # Подстрочные символы
        ("x₁", "x_1"),
        ("x₂", "x_2"),
        ("x₁ + y₂", "x_1 + y_2"),
        ("x₁₂", "x_{12}"),  # Последовательные символы - правильный LaTeX формат
        
        # Смешанные случаи
        ("x₁²", "x_1^2"),
        ("x²₁", "x^2_1"),
        
        # Без изменений
        ("x + y", "x + y"),
        ("", ""),
    ]
    
    print("Тестирование функции convert_superscript_subscript_to_latex:")
    print("=" * 60)
    
    passed = 0
    total = len(test_cases)
    
    for i, (input_text, expected) in enumerate(test_cases, 1):
        result = convert_superscript_subscript_to_latex(input_text)
        status = "✓" if result == expected else "✗"
        if result == expected:
            passed += 1
        print(f"{i}. {status} Вход: '{input_text}'")
        print(f"   Ожидалось: '{expected}'")
        print(f"   Получено:  '{result}'")
        print()
    
    print(f"Результат: {passed}/{total} тестов прошли успешно")
    return passed == total


def test_extract_math_expression():
    """Тестирует функцию нормализации математических выражений."""
    
    test_cases = [
        # Простые формулы - без изменений
        ("2(x + 1) = 4", "2(x + 1) = 4"),
        ("x + y = 5", "x + y = 5"),
        ("3x + 2y - 5", "3x + 2y - 5"),
        
        # Формулы с надстрочными символами
        ("x² + 5x + 6 = 0", "x^2 + 5x + 6 = 0"),
        ("(a + b)²", "(a + b)^2"),
        ("x³ + y²", "x^3 + y^2"),
        ("2⁴ × 3²", "2^4 × 3^2"),
        
        # Формулы с подстрочными символами
        ("x₁ + x₂", "x_1 + x_2"),
        ("x_1 + x_2", "x_1 + x_2"),
        
        # Формулы с LaTeX командами
        ("\\frac{1}{2} + \\frac{1}{3}", "\\frac{1}{2} + \\frac{1}{3}"),
        ("\\sqrt{x² + y²}", "\\sqrt{x^2 + y^2}"),
        ("\\sin(x) + \\cos(y)", "\\sin(x) + \\cos(y)"),
        
        # LaTeX блоки
        ("$2x + 3 = 7$", "$2x + 3 = 7$"),
        ("$$x^2 + 5x + 6 = 0$$", "$$x^2 + 5x + 6 = 0$$"),
        
        # Множественные выражения через запятую
        ("x + y = 5, x - y = 1", "x + y = 5, x - y = 1"),
        ("x² = 4, x³ = 8", "x^2 = 4, x^3 = 8"),
        
        # Пробелы по краям
        (" , x₁ + x₂ , ", ", x_1 + x_2 ,"),
        (", 2x + 3y = 7 ", ", 2x + 3y = 7"),
        ("  x + y  ", "x + y"),
        
        # Английские формулы
        ("x^2 + 2x + 1 = 0", "x^2 + 2x + 1 = 0"),
        ("(a+b)^2", "(a+b)^2"),
        ("y = mx + b", "y = mx + b"),
        ("f(x) = x^2", "f(x) = x^2"),
        ("A = \\sin(x) + \\cos(y)", "A = \\sin(x) + \\cos(y)"),
        ("x = 5", "x = 5"),
        
        # Пустые строки
        ("", ""),
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


def main():
    """Запускает все тесты."""
    print("Запуск тестов для функций обработки математических выражений")
    print("=" * 70)
    print()
    
    # Тестируем преобразование надстрочных/подстрочных символов
    superscript_success = test_convert_superscript_subscript()
    print()
    
    # Тестируем извлечение математических выражений
    extraction_success = test_extract_math_expression()
    print()
    
    # Общий результат
    all_success = superscript_success and extraction_success
    print(f"Общий результат: {'✓ Все тесты прошли' if all_success else '✗ Некоторые тесты не прошли'}")
    
    return all_success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 
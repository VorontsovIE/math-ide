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
    """Тестирует функцию извлечения математических выражений."""
    
    test_cases = [
        # Простые случаи
        ("2(x + 1) = 4", "2(x + 1) = 4"),
        ("Решите уравнение 2(x + 1) = 4", "2(x + 1) = 4"),
        ("Пожалуйста, решите 2(x + 1) = 4", "2(x + 1) = 4"),
        
        # Сложные случаи с надстрочными символами
        ("Найдите корни уравнения x² + 5x + 6 = 0", "x^2 + 5x + 6 = 0"),
        ("Упростите выражение (a + b)²", "(a + b)^2"),
        ("Вычислите x³ + y²", "x^3 + y^2"),
        
        # С LaTeX командами
        ("Вычислите \\frac{1}{2} + \\frac{1}{3}", "\\frac{1}{2} + \\frac{1}{3}"),
        ("Найдите \\sqrt{x² + y²}", "\\sqrt{x^2 + y^2}"),
        ("Вычислите \\sin(x) + \\cos(y)", "\\sin(x) + \\cos(y)"),
        
        # LaTeX блоки
        ("Решите уравнение $2x + 3 = 7$", "2x + 3 = 7"),
        ("Найдите корни $$x^2 + 5x + 6 = 0$$", "x^2 + 5x + 6 = 0"),
        
        # Множественные выражения через запятую
        ("Решите систему x + y = 5, x - y = 1", "x + y = 5, x - y = 1"),
        ("Найдите корни x² = 4, x³ = 8", "x^2 = 4, x^3 = 8"),
        (" , x₁ + x₂ , ", "x_1 + x_2"),  # пробелы и запятые по краям
        (", 2x + 3y = 7 ", "2x + 3y = 7"),
        ("  x + y  ", "x + y"),
        
        # Латиница, формула в английском тексте
        ("Solve the equation x^2 + 2x + 1 = 0", "x^2 + 2x + 1 = 0"),
        ("Please simplify (a+b)^2", "(a+b)^2"),
        ("Find the roots: y = mx + b", "y = mx + b"),
        ("Integrate f(x) = x^2 from 0 to 1", "f(x) = x^2"),
        ("Let A = \\sin(x) + \\cos(y)", "A = \\sin(x) + \\cos(y)"),
        ("put x = 5", "x = 5"),
        ("Calculate the value of y = 2x + 3", "y = 2x + 3"),
        
        # Без математических выражений
        ("Привет, как дела?", ""),
        ("Hello, how are you?", ""),
        ("", ""),
        
        # Дополнительные тесты
        ("Упростите 3x + 2y - 5", "3x + 2y - 5"),
        ("Вычислите 2⁴ × 3²", "2^4 × 3^2"),
        ("Найдите x₁ + x₂", "x_1 + x_2"),
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
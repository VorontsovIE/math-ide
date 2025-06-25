#!/usr/bin/env python3
"""
Тест для проверки исправления экранирования LaTeX-команд в JSON.
"""

import json
import sys
import os

# Добавляем путь к модулям проекта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from core.engine import fix_latex_escapes_in_json, safe_json_parse


def test_fix_latex_escapes():
    """Тестирует функцию исправления LaTeX-экранирования."""
    
    test_cases = [
        # Простые случаи
        {
            "input": '{"expression": "\\sin(x) + \\cos(y)"}',
            "expected": '{"expression": "\\\\sin(x) + \\\\cos(y)"}',
            "description": "Простые тригонометрические функции"
        },
        {
            "input": '{"result": "2\\cdot\\sin(x)\\cos(x)"}',
            "expected": '{"result": "2\\\\cdot\\\\sin(x)\\\\cos(x)"}',
            "description": "Смешанные LaTeX-команды"
        },
        {
            "input": '{"explanation": "Применил формулу \\sin(2x) = 2\\sin(x)\\cos(x)"}',
            "expected": '{"explanation": "Применил формулу \\\\sin(2x) = 2\\\\sin(x)\\\\cos(x)"}',
            "description": "LaTeX в объяснении"
        },
        # Уже правильно экранированные команды
        {
            "input": '{"expression": "\\\\sin(x) + \\\\cos(y)"}',
            "expected": '{"expression": "\\\\sin(x) + \\\\cos(y)"}',
            "description": "Уже правильно экранированные команды"
        },
        # Смешанные случаи
        {
            "input": '{"result": "\\\\sin(x) + \\cos(y) + \\\\tan(z)"}',
            "expected": '{"result": "\\\\sin(x) + \\\\cos(y) + \\\\tan(z)"}',
            "description": "Смешанные правильно и неправильно экранированные команды"
        },
        # Проблемный случай из логов
        {
            "input": '{"result_expression": "-2\\sin(x)\\cos(x) + 10\\sin(x) - 9 = 0"}',
            "expected": '{"result_expression": "-2\\\\sin(x)\\\\cos(x) + 10\\\\sin(x) - 9 = 0"}',
            "description": "Проблемный случай из логов"
        }
    ]
    
    print("Тестирование функции fix_latex_escapes_in_json:")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nТест {i}: {test_case['description']}")
        print(f"Вход:  {test_case['input']}")
        
        try:
            result = fix_latex_escapes_in_json(test_case['input'])
            print(f"Выход: {result}")
            print(f"Ожидалось: {test_case['expected']}")
            
            if result == test_case['expected']:
                print("✅ ПРОЙДЕН")
            else:
                print("❌ НЕ ПРОЙДЕН")
                
        except Exception as e:
            print(f"❌ ОШИБКА: {e}")


def test_safe_json_parse():
    """Тестирует функцию безопасного парсинга JSON."""
    
    test_cases = [
        # Валидный JSON
        {
            "input": '{"result": "x = 5", "is_valid": true}',
            "should_parse": True,
            "description": "Валидный JSON"
        },
        # JSON с LaTeX-командами
        {
            "input": '{"result": "\\sin(x) = 0", "is_valid": true}',
            "should_parse": True,
            "description": "JSON с LaTeX-командами"
        },
        # Проблемный случай из логов
        {
            "input": '{"result_expression": "-2\\sin(x)\\cos(x) + 10\\sin(x) - 9 = 0", "is_valid": true}',
            "should_parse": True,
            "description": "Проблемный случай из логов"
        },
        # Невалидный JSON
        {
            "input": '{"result": "x = 5", "is_valid": true',  # Отсутствует закрывающая скобка
            "should_parse": False,
            "description": "Невалидный JSON"
        }
    ]
    
    print("\n\nТестирование функции safe_json_parse:")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nТест {i}: {test_case['description']}")
        print(f"Вход: {test_case['input']}")
        
        try:
            result = safe_json_parse(test_case['input'])
            print(f"Результат: {result}")
            
            if test_case['should_parse']:
                print("✅ ПРОЙДЕН - JSON успешно распарсен")
            else:
                print("❌ НЕ ПРОЙДЕН - JSON не должен был распарситься")
                
        except json.JSONDecodeError as e:
            print(f"Ошибка парсинга: {e}")
            
            if not test_case['should_parse']:
                print("✅ ПРОЙДЕН - Ожидаемая ошибка парсинга")
            else:
                print("❌ НЕ ПРОЙДЕН - Неожиданная ошибка парсинга")
                
        except Exception as e:
            print(f"❌ НЕОЖИДАННАЯ ОШИБКА: {e}")


def test_real_world_examples():
    """Тестирует реальные примеры из логов."""
    
    real_examples = [
        # Пример из логов - генерация преобразований
        '''[
  {
    "description": "Разложить sin^2(x) на элементарные функции",
    "expression": "1 - 2 \\cdot (2sin(x)cos(x)) + 10sin(x) - 9 = 0",
    "type": "expand",
    "metadata": {
      "usefullness": "good",
      "reasoning": "Раскрытие sin^2(x) в элементарные функции поможет привести к простым слагаемым."
    }
  }
]''',
        
        # Пример из логов - применение преобразования
        '''{
  "result_expression": "-2\\sin(x)\\cos(x) + 10\\sin(x) - 9 = 0",
  "is_valid": true,
  "explanation": "Приведение подобных слагаемых: 1 - 2(2\\sin(x)\\cos(x)) + 10\\sin(x) - 9 = 0 => -2\\sin(x)\\cos(x) + 10\\sin(x) - 9 = 0",
  "errors": null
}''',
        
        # Пример из логов - проверка завершенности
        '''{
  "is_solved": false,
  "confidence": 0.30,
  "explanation": "Уравнение содержит тригонометрические функции и требует дальнейших преобразований",
  "solution_type": "partial"
}'''
    ]
    
    print("\n\nТестирование реальных примеров из логов:")
    print("=" * 60)
    
    for i, example in enumerate(real_examples, 1):
        print(f"\nПример {i}:")
        print(f"Вход: {example[:100]}...")
        
        try:
            result = safe_json_parse(example)
            print(f"✅ УСПЕШНО распарсен: {type(result)}")
            if isinstance(result, list):
                print(f"   Количество элементов: {len(result)}")
            elif isinstance(result, dict):
                print(f"   Ключи: {list(result.keys())}")
                
        except Exception as e:
            print(f"❌ ОШИБКА: {e}")


if __name__ == "__main__":
    test_fix_latex_escapes()
    test_safe_json_parse()
    test_real_world_examples()
    
    print("\n\n" + "=" * 60)
    print("Тестирование завершено!") 
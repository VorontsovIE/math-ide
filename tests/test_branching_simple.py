"""
Простые тесты для ветвящихся решений MathIDE.
"""

import sys
import os

# Добавляем корневую директорию в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.types import (
    SolutionType,
    create_solution_step,
    create_system_step,
    create_cases_step,
    create_alternatives_step,
)


def test_solution_step_creation():
    """Тест создания простого шага решения."""
    print("Тестируем создание простого шага решения...")
    step = create_solution_step("x + 2 = 5")

    assert step.expression == "x + 2 = 5"
    assert step.solution_type == SolutionType.SINGLE
    assert len(step.branches) == 0
    print("✅ Тест создания простого шага прошел успешно")


def test_system_step_creation():
    """Тест создания шага с системой уравнений."""
    print("Тестируем создание системы уравнений...")
    equations = ["2x + 3y = 7", "x - y = 1"]
    step = create_system_step("Система двух уравнений с двумя неизвестными", equations)

    assert step.expression == "Система двух уравнений с двумя неизвестными"
    assert step.solution_type == SolutionType.SYSTEM
    assert len(step.branches) == 2

    # Проверяем первое уравнение
    assert step.branches[0].id == "eq_0"
    assert step.branches[0].name == "Уравнение 1"
    assert step.branches[0].expression == "2x + 3y = 7"
    assert step.branches[0].condition is None

    # Проверяем второе уравнение
    assert step.branches[1].id == "eq_1"
    assert step.branches[1].name == "Уравнение 2"
    assert step.branches[1].expression == "x - y = 1"
    assert step.branches[1].condition is None
    print("✅ Тест создания системы уравнений прошел успешно")


def test_cases_step_creation():
    """Тест создания шага с разбором случаев."""
    print("Тестируем создание разбора случаев...")
    cases = [
        ("x ≥ 0", "x + 2 = 5", "Случай 1: x ≥ 0"),
        ("x < 0", "-x + 2 = 5", "Случай 2: x < 0"),
    ]
    step = create_cases_step("Решение уравнения |x| + 2 = 5", cases)

    assert step.expression == "Решение уравнения |x| + 2 = 5"
    assert step.solution_type == SolutionType.CASES
    assert len(step.branches) == 2

    # Проверяем первый случай
    assert step.branches[0].id == "case_0"
    assert step.branches[0].name == "Случай 1: x ≥ 0"
    assert step.branches[0].expression == "x + 2 = 5"
    assert step.branches[0].condition == "x ≥ 0"

    # Проверяем второй случай
    assert step.branches[1].id == "case_1"
    assert step.branches[1].name == "Случай 2: x < 0"
    assert step.branches[1].expression == "-x + 2 = 5"
    assert step.branches[1].condition == "x < 0"
    print("✅ Тест создания разбора случаев прошел успешно")


def test_alternatives_step_creation():
    """Тест создания шага с альтернативными методами."""
    print("Тестируем создание альтернативных методов...")
    alternatives = [
        ("(x - 2)(x + 3) = 0", "Метод разложения на множители"),
        ("D = b² - 4ac = 1 + 24 = 25", "Метод дискриминанта"),
    ]
    step = create_alternatives_step(
        "Решение квадратного уравнения x² + x - 6 = 0", alternatives
    )

    assert step.expression == "Решение квадратного уравнения x² + x - 6 = 0"
    assert step.solution_type == SolutionType.ALTERNATIVES
    assert len(step.branches) == 2

    # Проверяем первый метод
    assert step.branches[0].id == "alt_0"
    assert step.branches[0].name == "Метод разложения на множители"
    assert step.branches[0].expression == "(x - 2)(x + 3) = 0"
    assert step.branches[0].condition is None

    # Проверяем второй метод
    assert step.branches[1].id == "alt_1"
    assert step.branches[1].name == "Метод дискриминанта"
    assert step.branches[1].expression == "D = b² - 4ac = 1 + 24 = 25"
    assert step.branches[1].condition is None
    print("✅ Тест создания альтернативных методов прошел успешно")


def test_complex_branching_scenario():
    """Тест сложного сценария с ветвящимися решениями."""
    print("Тестируем сложный сценарий с ветвящимися решениями...")
    # Создаем начальную задачу
    initial_step = create_solution_step("Решить: |x - 1| = 2x + 3")

    # Создаем разбор случаев
    cases = [
        ("x ≥ 1", "x - 1 = 2x + 3", "Случай 1: x ≥ 1"),
        ("x < 1", "-(x - 1) = 2x + 3", "Случай 2: x < 1"),
    ]
    cases_step = create_cases_step("Разбор случаев для модуля", cases)

    # Проверяем структуру
    assert initial_step.solution_type == SolutionType.SINGLE
    assert cases_step.solution_type == SolutionType.CASES
    assert len(cases_step.branches) == 2

    # Проверяем первый случай
    first_case = cases_step.branches[0]
    assert first_case.condition == "x ≥ 1"
    assert first_case.expression == "x - 1 = 2x + 3"

    # Проверяем второй случай
    second_case = cases_step.branches[1]
    assert second_case.condition == "x < 1"
    assert second_case.expression == "-(x - 1) = 2x + 3"
    print("✅ Тест сложного сценария прошел успешно")


def run_all_tests():
    """Запускает все тесты."""
    print("🧪 Запуск тестов ветвящихся решений MathIDE\n")

    try:
        test_solution_step_creation()
        test_system_step_creation()
        test_cases_step_creation()
        test_alternatives_step_creation()
        test_complex_branching_scenario()

        print("\n🎉 Все тесты прошли успешно!")
        print("✅ Поддержка ветвящихся решений работает корректно")

    except AssertionError as e:
        print(f"\n❌ Тест провалился: {e}")
        return False
    except Exception as e:
        print(f"\n💥 Ошибка во время тестирования: {e}")
        return False

    return True


if __name__ == "__main__":
    run_all_tests()

"""
Тесты для ветвящихся решений MathIDE.
Проверяет функциональность работы с системами уравнений, разбором случаев и альтернативными методами.
"""

import sys
import os

# Добавляем корневую директорию в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest  # noqa: E402
from core.types import (  # noqa: E402
    SolutionType,
    SolutionBranch,
    create_solution_step,
    create_system_step,
    create_cases_step,
    create_alternatives_step,
)


def test_solution_step_creation():
    """Тест создания простого шага решения."""
    step = create_solution_step("x + 2 = 5")

    assert step.expression == "x + 2 = 5"
    assert step.solution_type == SolutionType.SINGLE
    assert len(step.branches) == 0


def test_system_step_creation():
    """Тест создания шага с системой уравнений."""
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


def test_cases_step_creation():
    """Тест создания шага с разбором случаев."""
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


def test_alternatives_step_creation():
    """Тест создания шага с альтернативными методами."""
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


def test_solution_branch_creation():
    """Тест создания ветви решения."""
    branch = SolutionBranch(
        id="test_branch",
        name="Тестовая ветвь",
        expression="x = 3",
        condition="x > 0",
        is_valid=True,
    )

    assert branch.id == "test_branch"
    assert branch.name == "Тестовая ветвь"
    assert branch.expression == "x = 3"
    assert branch.condition == "x > 0"
    assert branch.is_valid is True


def test_solution_types_enum():
    """Тест перечисления типов решений."""
    assert SolutionType.SINGLE.value == "single"
    assert SolutionType.SYSTEM.value == "system"
    assert SolutionType.CASES.value == "cases"
    assert SolutionType.ALTERNATIVES.value == "alternatives"
    assert SolutionType.UNION.value == "union"
    assert SolutionType.INTERSECTION.value == "intersection"


def test_complex_branching_scenario():
    """Тест сложного сценария с ветвящимися решениями."""
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


if __name__ == "__main__":
    pytest.main([__file__])

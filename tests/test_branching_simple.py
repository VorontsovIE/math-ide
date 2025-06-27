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
    SolutionStep,
    SolutionBranch,
)


def test_simple_step_creation() -> None:
    """Тест создания простого шага."""
    step = create_solution_step("x + 2 = 5")
    assert step.expression == "x + 2 = 5"
    assert step.solution_type == SolutionType.SINGLE
    assert len(step.branches) == 0


def test_system_step_creation() -> None:
    """Тест создания шага с системой уравнений."""
    equations = ["x + y = 5", "x - y = 1"]
    step = create_system_step("Система уравнений", equations)
    assert step.expression == "Система уравнений"
    assert step.solution_type == SolutionType.SYSTEM
    assert len(step.branches) == 2


def test_cases_step_creation() -> None:
    """Тест создания шага с разбором случаев."""
    cases = [("x ≥ 0", "x = 2", "Случай 1: x ≥ 0"), ("x < 0", "x = -2", "Случай 2: x < 0")]
    step = create_cases_step("|x| = 2", cases)
    assert step.expression == "|x| = 2"
    assert step.solution_type == SolutionType.CASES
    assert len(step.branches) == 2


def test_alternatives_step_creation() -> None:
    """Тест создания шага с альтернативными путями."""
    alternatives = [
        ("Факторизация", "x^2 - 4 = (x-2)(x+2)"),
        ("Квадратное уравнение", "x^2 = 4"),
    ]
    step = create_alternatives_step("x^2 - 4 = 0", alternatives)
    assert step.expression == "x^2 - 4 = 0"
    assert step.solution_type == SolutionType.ALTERNATIVES
    assert len(step.branches) == 2


def test_complex_branching_scenario() -> None:
    """Тест сложного сценария ветвления."""
    # Создаем сложную задачу с модулем
    cases = [("x ≥ 0", "x + 1 = 3", "Случай 1: x ≥ 0"), ("x < 0", "-x + 1 = 3", "Случай 2: x < 0")]
    step = create_cases_step("|x| + 1 = 3", cases)

    # Проверяем структуру
    assert step.solution_type == SolutionType.CASES
    assert len(step.branches) == 2

    # Проверяем ветви
    branch1 = step.branches[0]
    assert branch1.name == "Случай 1: x ≥ 0"
    assert branch1.expression == "x + 1 = 3"
    assert branch1.condition == "x ≥ 0"

    branch2 = step.branches[1]
    assert branch2.name == "Случай 2: x < 0"
    assert branch2.expression == "-x + 1 = 3"
    assert branch2.condition == "x < 0"

    print("✅ Тест сложного сценария прошел успешно")


def test_simple_branching() -> None:
    """Тест простого ветвления."""
    # Создаем простой шаг
    step = SolutionStep(expression="x^2 = 4")

    # Проверяем, что шаг создан корректно
    assert step.expression == "x^2 = 4"
    assert step.solution_type == SolutionType.SINGLE
    assert step.branches == []


def test_branching_with_conditions() -> None:
    """Тест ветвления с условиями."""
    # Создаем ветви
    branches = [
        SolutionBranch(
            id="branch_1",
            name="x = 2",
            expression="x = 2",
            condition="x > 0",
            is_valid=True,
        ),
        SolutionBranch(
            id="branch_2",
            name="x = -2",
            expression="x = -2",
            condition="x < 0",
            is_valid=True,
        ),
    ]

    # Создаем шаг с ветвлением
    step = SolutionStep(
        expression="x^2 = 4", solution_type=SolutionType.CASES, branches=branches
    )

    # Проверяем
    assert len(step.branches) == 2
    assert step.branches[0].name == "x = 2"
    assert step.branches[1].name == "x = -2"


def test_branching_validation() -> None:
    """Тест валидации ветвления."""
    # Создаем невалидную ветвь
    invalid_branch = SolutionBranch(
        id="invalid", name="Invalid", expression="", condition=None, is_valid=False
    )

    # Проверяем
    assert not invalid_branch.is_valid
    assert invalid_branch.expression == ""


def test_branching_metadata() -> None:
    """Тест метаданных ветвления."""
    metadata = {"complexity": "medium", "requires_analysis": True}

    step = SolutionStep(
        expression="|x| = 3", solution_type=SolutionType.CASES, metadata=metadata
    )

    assert step.metadata["complexity"] == "medium"
    assert step.metadata["requires_analysis"] is True


def test_branching_serialization() -> None:
    """Тест сериализации ветвления."""
    branches = [
        SolutionBranch(
            id="test_branch",
            name="Test Branch",
            expression="x = 1",
            condition="x > 0",
            is_valid=True,
        )
    ]

    step = SolutionStep(
        expression="x^2 = 1", solution_type=SolutionType.CASES, branches=branches
    )

    # Проверяем, что можно получить словарь
    step_dict = step.__dict__
    assert "expression" in step_dict
    assert "solution_type" in step_dict
    assert "branches" in step_dict


def run_all_tests():
    """Запускает все тесты."""
    print("🧪 Запуск тестов ветвящихся решений MathIDE\n")

    try:
        test_simple_step_creation()
        test_system_step_creation()
        test_cases_step_creation()
        test_alternatives_step_creation()
        test_complex_branching_scenario()
        test_simple_branching()
        test_branching_with_conditions()
        test_branching_validation()
        test_branching_metadata()
        test_branching_serialization()

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

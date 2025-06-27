"""
Тесты для параметризованных преобразований MathIDE.
Проверяет функциональность работы с параметрами преобразований.
"""

import sys
import os

# Добавляем корневую директорию в sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.engine import TransformationEngine
from core.types import (  # noqa: E402
    ParameterType,
    ParameterDefinition,
    Transformation,
)


def test_basic_parametrized_transformation():
    """Тест базового параметризованного преобразования."""

    # Создаем параметризованное преобразование
    param_def = ParameterDefinition(
        name="FACTOR",
        prompt="Введите множитель для разложения на множители",
        param_type=ParameterType.EXPRESSION,
        default_value="x",
    )

    transformation = Transformation(
        description="Разложить на множители: {FACTOR}",
        expression="({FACTOR})(остальная часть)",
        type="factor",
        parameter_definitions=[param_def],
        requires_user_input=True,
    )

    # Симулируем пользовательский ввод
    def mock_user_input(param_def):
        return "2x"

    # Создаем движок (в тестовом режиме)
    engine = TransformationEngine(preview_mode=True)

    # Запрашиваем параметры
    filled_transformation = engine.request_parameters(transformation, mock_user_input)

    # Проверяем результат
    assert not filled_transformation.requires_user_input
    assert filled_transformation.parameters is not None
    assert len(filled_transformation.parameters) == 1
    assert filled_transformation.parameters[0].name == "FACTOR"
    assert filled_transformation.parameters[0].value == "2x"
    assert filled_transformation.description == "Разложить на множители: 2x"
    assert filled_transformation.expression == "(2x)(остальная часть)"


def test_choice_parameter():
    """Тест параметра с выбором из вариантов."""

    param_def = ParameterDefinition(
        name="METHOD",
        prompt="Выберите метод решения",
        param_type=ParameterType.CHOICE,
        options=["подстановка", "исключение", "матричный метод"],
    )

    transformation = Transformation(
        description="Решить систему методом: {METHOD}",
        expression="Применяем {METHOD}",
        type="solve_system",
        parameter_definitions=[param_def],
        requires_user_input=True,
    )

    # Симулируем выбор второго варианта
    def mock_user_input(param_def):
        return "исключение"

    engine = TransformationEngine(preview_mode=True)
    filled_transformation = engine.request_parameters(transformation, mock_user_input)

    assert filled_transformation.parameters is not None
    assert filled_transformation.parameters[0].value == "исключение"
    assert filled_transformation.description == "Решить систему методом: исключение"


def test_multiple_parameters():
    """Тест преобразования с несколькими параметрами."""

    param_defs = [
        ParameterDefinition(
            name="A",
            prompt="Введите первое число",
            param_type=ParameterType.NUMBER,
            default_value="1",
        ),
        ParameterDefinition(
            name="B",
            prompt="Введите второе число",
            param_type=ParameterType.NUMBER,
            default_value="0",
        ),
    ]

    transformation = Transformation(
        description="Прибавить {A} и умножить на {B}",
        expression="({current_expression} + {A}) * {B}",
        type="custom",
        parameter_definitions=param_defs,
        requires_user_input=True,
    )

    # Симулируем ввод значений
    input_values = {"A": "5", "B": "3"}

    def mock_user_input(param_def):
        return input_values[param_def.name]

    engine = TransformationEngine(preview_mode=True)
    filled_transformation = engine.request_parameters(transformation, mock_user_input)

    assert filled_transformation.parameters is not None
    assert len(filled_transformation.parameters) == 2
    assert filled_transformation.description == "Прибавить 5 и умножить на 3"
    assert (
        "5" in filled_transformation.expression
        and "3" in filled_transformation.expression
    )


if __name__ == "__main__":
    test_basic_parametrized_transformation()
    test_choice_parameter()
    test_multiple_parameters()
    print("Все тесты параметризованных преобразований прошли успешно!")

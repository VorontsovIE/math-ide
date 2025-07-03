#!/usr/bin/env python3
"""
Тестовый пример работы с параметризованными преобразованиями.
Демонстрирует, как работают плейсхолдеры, требующие пользовательского ввода.
"""

from core.engine import TransformationEngine
from core.types import (
    ParameterDefinition,
    ParameterType,
    Transformation,
    TransformationParameter,
)


def demo_parametrized_transformations():
    """Демонстрация параметризованных преобразований."""
    print("=== Демонстрация параметризованных преобразований ===\n")
    
    # Создаем движок
    engine = TransformationEngine(preview_mode=True)
    
    # Пример 1: Преобразование с числовым параметром
    print("1. Преобразование с числовым параметром:")
    param_def_number = ParameterDefinition(
        name="NUMBER",
        prompt="Введите число для вычитания из обеих частей",
        param_type=ParameterType.NUMBER,
        default_value="4",
        suggested_values=["2", "4", "6", "8"]
    )
    
    transformation_number = Transformation(
        description="Вычесть {NUMBER} из обеих частей",
        expression="2x + 4 - {NUMBER} = 10 - {NUMBER}",
        type="subtract",
        parameter_definitions=[param_def_number],
        requires_user_input=True,
    )
    
    print(f"   Описание: {transformation_number.description}")
    print(f"   Выражение: {transformation_number.expression}")
    print(f"   Требует ввода: {transformation_number.requires_user_input}")
    print(f"   Параметры: {[p.name for p in transformation_number.parameter_definitions]}")
    
    # Симулируем ввод пользователя
    def mock_user_input(param_def):
        if param_def.name == "NUMBER":
            return "4"
        return param_def.default_value or ""
    
    # Запрашиваем параметры
    filled_transformation = engine.request_parameters(transformation_number, mock_user_input)
    
    print(f"   После заполнения: {filled_transformation.description}")
    print(f"   Результат: {filled_transformation.expression}")
    print(f"   Требует ввода: {filled_transformation.requires_user_input}")
    print()
    
    # Пример 2: Преобразование с выбором метода
    print("2. Преобразование с выбором метода:")
    param_def_method = ParameterDefinition(
        name="METHOD",
        prompt="Выберите метод решения",
        param_type=ParameterType.CHOICE,
        options=["подстановка", "исключение", "матричный метод", "графический метод"],
        default_value="подстановка"
    )
    
    transformation_method = Transformation(
        description="Решить систему методом: {METHOD}",
        expression="Применяем метод {METHOD} к системе уравнений",
        type="solve_system",
        parameter_definitions=[param_def_method],
        requires_user_input=True,
    )
    
    print(f"   Описание: {transformation_method.description}")
    print(f"   Выражение: {transformation_method.expression}")
    print(f"   Варианты выбора: {param_def_method.options}")
    
    # Симулируем выбор метода
    def mock_method_choice(param_def):
        if param_def.name == "METHOD":
            return "исключение"
        return param_def.default_value or ""
    
    filled_method = engine.request_parameters(transformation_method, mock_method_choice)
    print(f"   После выбора: {filled_method.description}")
    print(f"   Результат: {filled_method.expression}")
    print()
    
    # Пример 3: Преобразование с математическим выражением
    print("3. Преобразование с математическим выражением:")
    param_def_expression = ParameterDefinition(
        name="FACTOR",
        prompt="Введите множитель для разложения на множители",
        param_type=ParameterType.EXPRESSION,
        default_value="x",
        suggested_values=["x", "2x", "x+1", "x-2"]
    )
    
    transformation_expression = Transformation(
        description="Разложить на множители: {FACTOR}",
        expression="({FACTOR})(остальная часть выражения)",
        type="factor",
        parameter_definitions=[param_def_expression],
        requires_user_input=True,
    )
    
    print(f"   Описание: {transformation_expression.description}")
    print(f"   Выражение: {transformation_expression.expression}")
    print(f"   Предлагаемые значения: {param_def_expression.suggested_values}")
    
    # Симулируем ввод выражения
    def mock_expression_input(param_def):
        if param_def.name == "FACTOR":
            return "2x"
        return param_def.default_value or ""
    
    filled_expression = engine.request_parameters(transformation_expression, mock_expression_input)
    print(f"   После ввода: {filled_expression.description}")
    print(f"   Результат: {filled_expression.expression}")
    print()
    
    # Пример 4: Преобразование с несколькими параметрами
    print("4. Преобразование с несколькими параметрами:")
    param_defs_multiple = [
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
    
    transformation_multiple = Transformation(
        description="Прибавить {A} и умножить на {B}",
        expression="({current_expression} + {A}) * {B}",
        type="custom",
        parameter_definitions=param_defs_multiple,
        requires_user_input=True,
    )
    
    print(f"   Описание: {transformation_multiple.description}")
    print(f"   Выражение: {transformation_multiple.expression}")
    print(f"   Параметры: {[p.name for p in transformation_multiple.parameter_definitions]}")
    
    # Симулируем ввод нескольких значений
    input_values = {"A": "5", "B": "3"}
    
    def mock_multiple_input(param_def):
        return input_values.get(param_def.name, param_def.default_value or "")
    
    filled_multiple = engine.request_parameters(transformation_multiple, mock_multiple_input)
    print(f"   После заполнения: {filled_multiple.description}")
    print(f"   Результат: {filled_multiple.expression}")
    print(f"   Значения параметров: {[(p.name, p.value) for p in filled_multiple.parameters]}")
    print()
    
    print("=== Демонстрация завершена ===")


if __name__ == "__main__":
    demo_parametrized_transformations() 
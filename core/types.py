"""
Типы данных для MathIDE.
Содержит все основные dataclass'ы и enums, используемые в системе.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from enum import Enum


class BaseTransformationType(Enum):
    """
    Базовые типы преобразований, которые служат ориентиром для GPT.
    GPT может предлагать и другие типы, если они релевантны.
    """

    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"
    FACTOR = "factor"
    EXPAND = "expand"
    COLLECT_TERMS = "collect_terms"
    SUBSTITUTE = "substitute"
    EXPAND_CASES = "expand_cases"  # Для разбора случаев, например, с модулем |x|
    SIMPLIFY = "simplify"
    CUSTOM = "custom"

    @classmethod
    def descriptions(cls) -> Dict[str, str]:
        """Возвращает описания типов преобразований."""
        return {
            cls.ADD.value: "Сложение выражений",
            cls.SUBTRACT.value: "Вычитание выражений",
            cls.MULTIPLY.value: "Умножение выражений",
            cls.DIVIDE.value: "Деление выражений",
            cls.FACTOR.value: "Разложение на множители",
            cls.EXPAND.value: "Раскрытие скобок",
            cls.COLLECT_TERMS.value: "Приведение подобных членов",
            cls.SUBSTITUTE.value: "Подстановка значений",
            cls.EXPAND_CASES.value: "Разбор случаев",
            cls.SIMPLIFY.value: "Упрощение выражения",
            cls.CUSTOM.value: "Пользовательское преобразование",
        }


class ParameterType(Enum):
    """Типы параметров преобразований."""

    NUMBER = "number"  # Числовое значение
    EXPRESSION = "expression"  # Математическое выражение
    CHOICE = "choice"  # Выбор из предложенных вариантов
    TEXT = "text"  # Произвольный текст


@dataclass
class ParameterDefinition:
    """Определение параметра для запроса у пользователя."""

    name: str  # Имя параметра (например, "FACTOR")
    prompt: str  # Текст для запроса у пользователя
    param_type: ParameterType  # Тип параметра
    options: Optional[List[Any]] = None  # Варианты выбора (для CHOICE)
    default_value: Optional[Any] = None  # Значение по умолчанию
    validation_rule: Optional[str] = None  # Правило валидации
    suggested_values: Optional[List[Any]] = None  # Предлагаемые значения


@dataclass
class TransformationParameter:
    """Параметр с выбранным значением для использования в преобразовании."""

    name: str
    value: Any
    param_type: ParameterType = ParameterType.TEXT
    original_definition: Optional[ParameterDefinition] = None


@dataclass
class Transformation:
    """Представляет одно математическое преобразование."""

    description: str
    expression: str  # Было latex
    type: str  # Тип преобразования (желательно из BaseTransformationType)
    parameters: Optional[List[TransformationParameter]] = None
    parameter_definitions: Optional[List[ParameterDefinition]] = (
        None  # Определения параметров для запроса
    )
    metadata: Dict[str, Any] = field(default_factory=dict)
    preview_result: Optional[str] = (
        None  # Предварительный результат применения преобразования
    )
    requires_user_input: bool = False  # Требует ли преобразование ввода от пользователя


class SolutionType(Enum):
    """Типы решений для поддержки ветвящихся решений."""

    SINGLE = "single"  # Одно выражение
    SYSTEM = "system"  # Система уравнений/неравенств
    ALTERNATIVES = "alternatives"  # Альтернативные пути решения
    CASES = "cases"  # Разбор случаев (например, с модулем |x|)
    UNION = "union"  # Объединение решений
    INTERSECTION = "intersection"  # Пересечение решений


@dataclass
class SolutionBranch:
    """
    Представляет одну ветвь решения в ветвящемся решении.
    """

    id: str
    name: str  # Название ветви (например, "Случай 1: x ≥ 0")
    expression: str  # Выражение этой ветви
    condition: Optional[str] = None  # Условие для этой ветви
    is_valid: bool = True  # Является ли ветвь валидной
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SolutionStep:
    """
    Представляет один шаг в процессе решения математической задачи.
    Поддерживает как простые выражения, так и ветвящиеся решения.
    """

    expression: str  # Основное выражение или описание шага
    solution_type: SolutionType = SolutionType.SINGLE
    branches: List[SolutionBranch] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationResult:
    """Результат генерации, содержащий список возможных преобразований."""

    transformations: List[Transformation]


@dataclass
class ApplyResult:
    """Результат применения преобразования."""

    result: str
    is_valid: bool
    explanation: str
    errors: Optional[List[str]] = None
    mathematical_verification: Optional[str] = (
        None  # Математическая проверка корректности
    )


@dataclass
class CheckResult:
    """Результат проверки завершённости решения."""

    is_solved: bool
    confidence: float
    explanation: str
    solution_type: str  # exact, approximate, partial
    next_steps: List[str] = field(default_factory=list)
    mathematical_verification: Optional[str] = (
        None  # Математическая проверка корректности
    )


@dataclass
class ProgressAnalysisResult:
    """Результат анализа прогресса решения."""

    progress_assessment: str  # good, neutral, poor
    confidence: float
    analysis: str
    recommend_rollback: bool
    recommended_step: Optional[int] = None
    rollback_reason: Optional[str] = None
    suggestion_message: Optional[str] = None


@dataclass
class VerificationResult:
    """Результат проверки и пересчёта математического преобразования."""

    is_correct: bool
    corrected_result: str
    verification_explanation: str
    errors_found: List[str] = field(default_factory=list)
    step_by_step_check: str = ""
    user_result_assessment: Optional[str] = None


def get_transformation_types_markdown() -> str:
    """Возвращает Markdown-описание типов преобразований."""
    desc = BaseTransformationType.descriptions()
    return "\n".join([f"- `{k}` — {v}" for k, v in desc.items()])


def create_solution_step(
    expression: str, solution_type: SolutionType = SolutionType.SINGLE
) -> SolutionStep:
    """Создает простой шаг решения."""
    return SolutionStep(expression=expression, solution_type=solution_type)


def create_system_step(system_description: str, equations: List[str]) -> SolutionStep:
    """Создает шаг с системой уравнений."""
    branches = []
    for i, equation in enumerate(equations):
        branch = SolutionBranch(
            id=f"eq_{i}", name=f"Уравнение {i+1}", expression=equation
        )
        branches.append(branch)

    return SolutionStep(
        expression=system_description,
        solution_type=SolutionType.SYSTEM,
        branches=branches,
    )


def create_cases_step(problem_description: str, cases: List[tuple]) -> SolutionStep:
    """
    Создает шаг с разбором случаев.

    Args:
        problem_description: Описание проблемы
        cases: Список кортежей (условие, выражение, название)
    """
    branches = []
    for i, (condition, expression, name) in enumerate(cases):
        branch = SolutionBranch(
            id=f"case_{i}",
            name=name or f"Случай {i+1}",
            expression=expression,
            condition=condition,
        )
        branches.append(branch)

    return SolutionStep(
        expression=problem_description,
        solution_type=SolutionType.CASES,
        branches=branches,
    )


def create_alternatives_step(
    problem_description: str, alternatives: List[tuple]
) -> SolutionStep:
    """
    Создает шаг с альтернативными путями решения.

    Args:
        problem_description: Описание проблемы
        alternatives: Список кортежей (выражение, название_метода)
    """
    branches = []
    for i, (expression, method_name) in enumerate(alternatives):
        branch = SolutionBranch(
            id=f"alt_{i}", name=method_name or f"Метод {i+1}", expression=expression
        )
        branches.append(branch)

    return SolutionStep(
        expression=problem_description,
        solution_type=SolutionType.ALTERNATIVES,
        branches=branches,
    )

"""
Типы данных для MathIDE.
Содержит все основные dataclass'ы и enums, используемые в системе.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


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
    parameters: Optional[List[TransformationParameter]] = None
    parameter_definitions: Optional[List[ParameterDefinition]] = (
        None  # Определения параметров для запроса
    )
    metadata: Dict[str, Any] = field(default_factory=dict)
    preview_result: Optional[str] = (
        None  # Предварительный результат применения преобразования
    )
    requires_user_input: bool = False  # Требует ли преобразование ввода от пользователя


@dataclass
class SolutionStep:
    """
    Представляет один шаг в процессе решения математической задачи.
    """

    expression: str  # Основное выражение или описание шага
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationResult:
    """Результат генерации, содержащий список возможных преобразований."""

    transformations: List[Transformation]


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


def create_solution_step(expression: str) -> SolutionStep:
    """Создает простой шаг решения."""
    return SolutionStep(expression=expression)

"""
Типы данных для MathIDE.
Содержит все основные dataclass'ы и enums, используемые в системе.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from enum import Enum
from datetime import datetime


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
    def descriptions(cls):
        """Возвращает описания типов преобразований."""
        return {
            cls.ADD.value: "добавление к обеим частям",
            cls.SUBTRACT.value: "вычитание из обеих частей",
            cls.MULTIPLY.value: "умножение обеих частей",
            cls.DIVIDE.value: "деление обеих частей",
            cls.FACTOR.value: "разложение на множители",
            cls.EXPAND.value: "раскрытие скобок",
            cls.COLLECT_TERMS.value: "приведение подобных слагаемых",
            cls.SUBSTITUTE.value: "подстановка",
            cls.EXPAND_CASES.value: "разбор случаев (например, с модулем)",
            cls.SIMPLIFY.value: "упрощение выражения",
            cls.CUSTOM.value: "любое другое преобразование"
        }


@dataclass
class TransformationParameter:
    """Параметр, который может быть использован в преобразовании."""
    name: str
    value: Any
    options: Optional[List[Any]] = None  # Возможные значения (для будущей параметризации)


@dataclass
class Transformation:
    """Представляет одно математическое преобразование."""
    description: str
    expression: str  # Было latex
    type: str  # Тип преобразования (желательно из BaseTransformationType)
    parameters: Optional[List[TransformationParameter]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    preview_result: Optional[str] = None  # Предварительный результат применения преобразования


@dataclass
class SolutionStep:
    """
    Представляет один шаг в процессе решения математической задачи.
    Это может быть уравнение, неравенство, система и т.д. на любом этапе.
    """
    expression: str  # Было latex_content


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
    mathematical_verification: Optional[str] = None  # Математическая проверка корректности


@dataclass
class CheckResult:
    """Результат проверки завершённости решения."""
    is_solved: bool
    confidence: float
    explanation: str
    solution_type: str  # exact, approximate, partial
    next_steps: List[str] = field(default_factory=list)
    mathematical_verification: Optional[str] = None  # Математическая проверка корректности


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
"""
Ядро MathIDE - основные компоненты для работы с математическими преобразованиями.
"""

# Основные классы
from .engine import TransformationEngine

# Импортируем исключения
from .exceptions import (
    ExpressionValidationError,
    GPTConnectionError,
    GPTError,
    GPTInvalidResponseError,
    GPTRateLimitError,
    HistoryError,
    InvalidStepError,
    JSONParseError,
    LaTeXParseError,
    MathIDEError,
    ParseError,
    PromptError,
    PromptFormatError,
    PromptNotFoundError,
    StepNotFoundError,
    TransformationValidationError,
    ValidationError,
)
from .history import HistoryStep, SolutionHistory

# Импортируем основные типы данных
from .types import (
    ApplyResult,
    BaseTransformationType,
    CheckResult,
    GenerationResult,
    ProgressAnalysisResult,
    SolutionStep,
    Transformation,
    TransformationParameter,
    VerificationResult,
    get_transformation_types_markdown,
)

__all__ = [
    # Типы данных
    "BaseTransformationType",
    "TransformationParameter",
    "Transformation",
    "SolutionStep",
    "GenerationResult",
    "ApplyResult",
    "CheckResult",
    "ProgressAnalysisResult",
    "VerificationResult",
    "get_transformation_types_markdown",
    # Исключения
    "MathIDEError",
    "GPTError",
    "GPTConnectionError",
    "GPTRateLimitError",
    "GPTInvalidResponseError",
    "ParseError",
    "JSONParseError",
    "LaTeXParseError",
    "ValidationError",
    "TransformationValidationError",
    "ExpressionValidationError",
    "PromptError",
    "PromptNotFoundError",
    "PromptFormatError",
    "HistoryError",
    "StepNotFoundError",
    "InvalidStepError",
    # Основные классы
    "TransformationEngine",
    "SolutionHistory",
    "HistoryStep",
]

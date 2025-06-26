"""
Ядро MathIDE - основные компоненты для работы с математическими преобразованиями.
"""

# Импортируем основные типы данных
from .types import (
    BaseTransformationType,
    TransformationParameter,
    Transformation,
    SolutionStep,
    GenerationResult,
    ApplyResult,
    CheckResult,
    ProgressAnalysisResult,
    VerificationResult,
    get_transformation_types_markdown,
)

# Импортируем исключения
from .exceptions import (
    MathIDEError,
    GPTError,
    GPTConnectionError,
    GPTRateLimitError,
    GPTInvalidResponseError,
    ParseError,
    JSONParseError,
    LaTeXParseError,
    ValidationError,
    TransformationValidationError,
    ExpressionValidationError,
    PromptError,
    PromptNotFoundError,
    PromptFormatError,
    HistoryError,
    StepNotFoundError,
    InvalidStepError,
)

# Основные классы
from .engine import TransformationEngine
from .history import SolutionHistory, HistoryStep

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
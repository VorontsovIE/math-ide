"""
Пользовательские исключения для MathIDE.
Определяет иерархию исключений для различных типов ошибок.
"""


class MathIDEError(Exception):
    """Базовое исключение для всех ошибок MathIDE."""
    pass


class GPTError(MathIDEError):
    """Ошибки при работе с GPT API."""
    pass


class GPTConnectionError(GPTError):
    """Ошибка подключения к GPT API."""
    pass


class GPTRateLimitError(GPTError):
    """Превышен лимит запросов к GPT API."""
    pass


class GPTInvalidResponseError(GPTError):
    """Некорректный ответ от GPT API."""
    pass


class ParseError(MathIDEError):
    """Ошибки парсинга данных."""
    pass


class JSONParseError(ParseError):
    """Ошибка парсинга JSON ответа."""
    pass


class LaTeXParseError(ParseError):
    """Ошибка парсинга LaTeX выражения."""
    pass


class ValidationError(MathIDEError):
    """Ошибки валидации данных."""
    pass


class TransformationValidationError(ValidationError):
    """Ошибка валидации преобразования."""
    pass


class ExpressionValidationError(ValidationError):
    """Ошибка валидации математического выражения."""
    pass


class PromptError(MathIDEError):
    """Ошибки работы с промптами."""
    pass


class PromptNotFoundError(PromptError):
    """Промпт не найден."""
    pass


class PromptFormatError(PromptError):
    """Ошибка форматирования промпта."""
    pass


class HistoryError(MathIDEError):
    """Ошибки работы с историей решения."""
    pass


class StepNotFoundError(HistoryError):
    """Шаг не найден в истории."""
    pass


class InvalidStepError(HistoryError):
    """Некорректный шаг в истории."""
    pass 
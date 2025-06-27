"""
Математические утилиты для обработки LaTeX и математических выражений.
"""

import re


def clean_latex_expression(latex_expr: str) -> str:
    """
    Очищает LaTeX выражение от лишних символов.

    Args:
        latex_expr: LaTeX выражение

    Returns:
        Очищенное выражение
    """
    # Удаляем лишние пробелы
    cleaned = re.sub(r"\s+", " ", latex_expr.strip())

    # Удаляем пустые группы скобок
    cleaned = re.sub(r"\{\s*\}", "", cleaned)

    return cleaned


def validate_latex_expression(latex_expr: str) -> bool:
    """
    Проверяет валидность LaTeX выражения.

    Args:
        latex_expr: LaTeX выражение для проверки

    Returns:
        True если выражение валидно
    """
    if not latex_expr or not isinstance(latex_expr, str):
        return False

    # Проверяем баланс скобок
    brackets = {"(": ")", "[": "]", "{": "}"}
    stack = []

    for char in latex_expr:
        if char in brackets:
            stack.append(char)
        elif char in brackets.values():
            if not stack:
                return False
            last_bracket = stack.pop()
            if brackets[last_bracket] != char:
                return False

    return len(stack) == 0


def extract_latex_commands(latex_expr: str) -> list:
    """
    Извлекает LaTeX команды из выражения.

    Args:
        latex_expr: LaTeX выражение

    Returns:
        Список найденных команд
    """
    pattern = r"\\[a-zA-Z]+"
    return re.findall(pattern, latex_expr)


def normalize_mathematical_expression(expr: str) -> str:
    """
    Нормализует математическое выражение для сравнения.

    Args:
        expr: Математическое выражение

    Returns:
        Нормализованное выражение
    """
    # Удаляем пробелы
    normalized = re.sub(r"\s+", "", expr)

    # Приводим к нижнему регистру функции
    normalized = re.sub(
        r"\\([a-zA-Z]+)", lambda m: "\\" + m.group(1).lower(), normalized
    )

    return normalized

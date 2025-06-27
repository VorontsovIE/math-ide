"""
Модуль для парсинга JSON и LaTeX данных.
Содержит утилиты для безопасного парсинга ответов GPT с исправлением LaTeX.
"""

import json
import re
import logging
from typing import Dict, Any, cast

from .exceptions import JSONParseError

logger = logging.getLogger(__name__)


def fix_latex_escapes_in_json(json_content: str) -> str:
    """
    Исправляет экранирование обратных слэшей в LaTeX-выражениях в JSON.

    Проблема: GPT возвращает \sin, \cos и т.д., но в JSON это должно быть \\sin, \\cos
    """
    # Список известных LaTeX-команд
    latex_commands = [
        "sin",
        "cos",
        "tan",
        "cot",
        "sec",
        "csc",
        "arcsin",
        "arccos",
        "arctan",
        "arccot",
        "arcsec",
        "arccsc",
        "sinh",
        "cosh",
        "tanh",
        "coth",
        "sech",
        "csch",
        "log",
        "ln",
        "exp",
        "lim",
        "inf",
        "infty",
        "sqrt",
        "cbrt",
        "frac",
        "over",
        "binom",
        "choose",
        "pm",
        "mp",
        "times",
        "div",
        "cdot",
        "ast",
        "leq",
        "geq",
        "neq",
        "approx",
        "equiv",
        "propto",
    ]

    def fix_latex_in_string(content: str) -> str:
        """Исправляет LaTeX-команды в строке"""
        temp_markers = {}
        marker_counter = 0

        def create_marker() -> str:
            nonlocal marker_counter
            marker = f"__TEMP_MARKER_{marker_counter}__"
            marker_counter += 1
            return marker

        for cmd in latex_commands:
            pattern = rf"\\\\{cmd}"
            if pattern in content:
                marker = create_marker()
                temp_markers[marker] = f"\\\\{cmd}"
                content = content.replace(pattern, marker)

        for cmd in latex_commands:
            pattern = rf"(?<!\\)\\{cmd}(?![a-zA-Z])"
            content = re.sub(pattern, rf"\\\\{cmd}", content)

        for marker, replacement in temp_markers.items():
            content = content.replace(marker, replacement)

        return content

    result = ""
    in_string = False
    string_start = 0
    i = 0

    while i < len(json_content):
        char = json_content[i]

        if char == '"' and (i == 0 or json_content[i - 1] != "\\"):
            if not in_string:
                in_string = True
                string_start = i
            else:
                in_string = False
                string_content = json_content[string_start + 1 : i]
                fixed_string = fix_latex_in_string(string_content)
                result += f'"{fixed_string}"'
        elif not in_string:
            result += char

        i += 1

    if not in_string and i < len(json_content):
        result += json_content[i:]

    return result


def safe_json_parse(json_content: str, fallback_attempts: int = 3) -> Dict[str, Any]:
    """
    Безопасно парсит JSON с несколькими попытками исправления.
    """
    attempts = []

    try:
        return cast(Dict[str, Any], json.loads(json_content))
    except json.JSONDecodeError as e:
        attempts.append(f"Прямой парсинг: {str(e)}")

    try:
        fixed_content = fix_latex_escapes_in_json(json_content)
        return cast(Dict[str, Any], json.loads(fixed_content))
    except json.JSONDecodeError as e:
        attempts.append(f"После исправления LaTeX: {str(e)}")

    try:
        aggressive_fixed = re.sub(r"(?<!\\)\\(?!\\)", r"\\\\", json_content)
        return cast(Dict[str, Any], json.loads(aggressive_fixed))
    except json.JSONDecodeError as e:
        attempts.append(f"Агрессивное исправление: {str(e)}")

    try:
        cleaned_content = re.sub(r'(?<!\\)\\(?!["\\/bfnrt])', "", json_content)
        return cast(Dict[str, Any], json.loads(cleaned_content))
    except json.JSONDecodeError as e:
        attempts.append(f"Очистка слэшей: {str(e)}")

    error_msg = f"Не удалось распарсить JSON после {len(attempts)} попыток"
    logger.error(error_msg)
    raise JSONParseError(error_msg)

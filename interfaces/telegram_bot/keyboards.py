"""
Модуль клавиатур для Telegram бота.
Содержит функции создания inline-клавиатур для различных взаимодействий.
"""

import logging
import base64
import json
from typing import Any, Dict, List, Optional

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

logger = logging.getLogger(__name__)





def get_transformations_keyboard(
    transformation_ids: List[str], current_step_id: str, transformations: Optional[List[Any]] = None
) -> InlineKeyboardMarkup:
    """Создает клавиатуру с доступными преобразованиями."""
    keyboard = []

    # Создаем ряд с кнопками преобразований (горизонтально)
    transformation_row = []
    for i, transformation_id in enumerate(transformation_ids):
        # Используем только номер преобразования на кнопке
        button = InlineKeyboardButton(
            text=str(i + 1),
            callback_data=f"transform_{transformation_id}",
        )
        transformation_row.append(button)
    
    # Добавляем ряд с кнопками преобразований
    if transformation_row:
        keyboard.append(transformation_row)

    # Добавляем кнопки навигации
    nav_row = []
    nav_row.append(
        InlineKeyboardButton("🔄 Обновить", callback_data=f"refresh_{current_step_id}")
    )
    keyboard.append(nav_row)

    return InlineKeyboardMarkup(keyboard)


def get_transformations_description_text(transformations: List[Any], use_html: bool = True) -> str:
    """Формирует текст с пронумерованными описаниями преобразований."""
    if not transformations:
        return "Нет доступных преобразований"
    
    description_lines = []
    for i, transformation in enumerate(transformations):
        # Получаем описание преобразования
        if isinstance(transformation, dict):
            description = transformation.get("description", f"Преобразование {i+1}")
        else:
            description = getattr(transformation, "description", f"Преобразование {i+1}")
        
        if use_html:
            # Используем HTML-разметку для жирных номеров
            description_lines.append(f"<b>{i+1}.</b> {description}")
        else:
            # Обычный текст без разметки
            description_lines.append(f"{i+1}. {description}")
    
    return "\n".join(description_lines)


def get_verification_keyboard(
    transformation_id: str, verification_type: str, current_step_id: str
) -> InlineKeyboardMarkup:
    """Создает клавиатуру для верификации преобразования."""
    keyboard = []

    # Кнопки для разных типов верификации
    if verification_type == "manual":
        keyboard.append(
            [
                InlineKeyboardButton(
                    "✅ Правильно", callback_data=f"verify_correct_{transformation_id}"
                ),
                InlineKeyboardButton(
                    "❌ Неправильно",
                    callback_data=f"verify_incorrect_{transformation_id}",
                ),
            ]
        )
    elif verification_type == "auto":
        keyboard.append(
            [
                InlineKeyboardButton(
                    "🔍 Проверить", callback_data=f"verify_auto_{transformation_id}"
                )
            ]
        )

    # Кнопки навигации
    nav_row = []
    nav_row.append(
        InlineKeyboardButton("🔄 Обновить", callback_data=f"refresh_{current_step_id}")
    )
    keyboard.append(nav_row)

    return InlineKeyboardMarkup(keyboard)


def get_parameter_input_keyboard(
    parameter_name: str,
    parameter_type: str,
    options: Optional[List[str]] = None,
    current_step_id: str = "",
) -> InlineKeyboardMarkup:
    """Создает клавиатуру для ввода параметров преобразования."""
    keyboard = []

    if parameter_type == "choice" and options:
        # Кнопки для выбора из вариантов
        for i, option in enumerate(options):
            button = InlineKeyboardButton(
                text=option,
                callback_data=f"param_{parameter_name}_{i}_{current_step_id}",
            )
            keyboard.append([button])
    else:
        # Кнопка для ручного ввода
        keyboard.append(
            [
                InlineKeyboardButton(
                    "✏️ Ввести вручную",
                    callback_data=f"param_manual_{parameter_name}_{current_step_id}",
                )
            ]
        )

    # Кнопки навигации
    nav_row = []
    nav_row.append(
        InlineKeyboardButton(
            "◀️ Отмена", callback_data=f"cancel_param_{current_step_id}"
        )
    )
    keyboard.append(nav_row)

    return InlineKeyboardMarkup(keyboard)


def get_solution_complete_keyboard(
    is_solved: bool, confidence: float, current_step_id: str
) -> InlineKeyboardMarkup:
    """Создает клавиатуру для завершенного решения."""
    keyboard = []

    if is_solved:
        status_text = f"✅ Решено (уверенность: {confidence:.1%})"
        keyboard.append(
            [InlineKeyboardButton(status_text, callback_data="solution_complete")]
        )
    else:
        status_text = f"❌ Не решено (уверенность: {confidence:.1%})"
        keyboard.append(
            [InlineKeyboardButton(status_text, callback_data="solution_incomplete")]
        )

    # Кнопки навигации
    nav_row = []
    nav_row.append(
        InlineKeyboardButton(
            "🔄 Продолжить", callback_data=f"continue_{current_step_id}"
        )
    )
    nav_row.append(
        InlineKeyboardButton("📝 Новое решение", callback_data="new_solution")
    )
    keyboard.append(nav_row)

    return InlineKeyboardMarkup(keyboard)


def get_error_keyboard(
    error_type: str, current_step_id: str = ""
) -> InlineKeyboardMarkup:
    """Создает клавиатуру для обработки ошибок."""
    keyboard = []

    if error_type == "api_error":
        keyboard.append(
            [
                InlineKeyboardButton(
                    "🔄 Повторить", callback_data=f"retry_{current_step_id}"
                ),
                InlineKeyboardButton("📝 Новое решение", callback_data="new_solution"),
            ]
        )
    elif error_type == "validation_error":
        keyboard.append(
            [
                InlineKeyboardButton(
                    "✏️ Исправить", callback_data=f"fix_{current_step_id}"
                ),
                InlineKeyboardButton(
                    "◀️ Назад", callback_data=f"back_{current_step_id}"
                ),
            ]
        )
    else:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "🔄 Повторить", callback_data=f"retry_{current_step_id}"
                ),
                InlineKeyboardButton("📝 Новое решение", callback_data="new_solution"),
            ]
        )

    return InlineKeyboardMarkup(keyboard)


def get_user_transformation_keyboard() -> InlineKeyboardMarkup:
    """Создает клавиатуру для ввода собственного преобразования."""
    keyboard = [
        [
            InlineKeyboardButton(
                "🎯 Я выполнил преобразование", callback_data="user_transformation"
            )
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

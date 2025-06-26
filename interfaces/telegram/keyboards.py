"""
Модуль клавиатур для Telegram бота.
Содержит функции создания inline-клавиатур для различных взаимодействий.
"""

from typing import List, Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    from core.types import Transformation


def get_transformations_keyboard(transformations: "List[Transformation]", step_id: Optional[str] = None) -> "InlineKeyboardMarkup":
    """Создаёт клавиатуру с доступными преобразованиями."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = []
    for idx, tr in enumerate(transformations):
        # Формируем текст кнопки только с описанием действия
        button_text = f"{idx + 1}. {tr.description}"
        
        # Включаем step_id в callback_data если он предоставлен
        callback_data = f"transform_{idx}"
        if step_id:
            callback_data = f"transform_{idx}_{step_id}"
        
        keyboard.append([
            InlineKeyboardButton(
                button_text,
                callback_data=callback_data
            )
        ])
    
    # Добавляем кнопку для ввода собственного преобразования
    custom_callback_data = f"custom_transform"
    if step_id:
        custom_callback_data = f"custom_transform_{step_id}"
    
    keyboard.append([
        InlineKeyboardButton(
            "✏️ Ввести своё преобразование",
            callback_data=custom_callback_data
        )
    ])
    
    # Добавляем кнопку для самостоятельного выполнения преобразования
    user_done_callback_data = f"user_done_transform"
    if step_id:
        user_done_callback_data = f"user_done_transform_{step_id}"
    
    keyboard.append([
        InlineKeyboardButton(
            "🎯 Я сам выполнил преобразование",
            callback_data=user_done_callback_data
        )
    ])
    
    return InlineKeyboardMarkup(keyboard)


def get_verification_keyboard(verification_context: Dict[str, Any]) -> "InlineKeyboardMarkup":
    """Создает клавиатуру для проверки результата преобразования."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton("🔄 Пересчитать (есть ошибка)", callback_data="verify_recalculate")],
        [InlineKeyboardButton("💡 Предложить свой результат", callback_data="verify_suggest")],
        [InlineKeyboardButton("✅ Результат правильный", callback_data="verify_accept")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_user_transformation_keyboard() -> "InlineKeyboardMarkup":
    """Создает клавиатуру для ввода собственного преобразования."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    keyboard = [
        [InlineKeyboardButton("🎯 Я выполнил преобразование", callback_data="user_transformation")]
    ]
    return InlineKeyboardMarkup(keyboard) 
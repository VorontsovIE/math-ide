"""
Модульный Telegram интерфейс.
Содержит разделенные компоненты для Telegram бота.
"""

# Импортируем основные компоненты
from .state import (
    UserState,
    user_states,
    get_user_state,
    create_user_state,
    reset_user_state,
)
from .rate_limiter import RateLimiter, rate_limiter

# Временно комментируем импорт renderers из-за зависимости matplotlib
# from .renderers import render_latex_to_image, render_transformations_image, fix_latex_expression, check_and_suggest_rollback

from .utils import (
    send_status_message,
    edit_status_message,
    update_status_with_progress,
    get_progress_indicator,
)
from .keyboards import (
    get_transformations_keyboard,
    get_verification_keyboard,
    get_user_transformation_keyboard,
)

# Обработчики команд
from .handlers import (
    start,
    help_command,
    cancel,
    show_history,
    handle_task,
    handle_transformation_choice,
    handle_custom_transformation,
    handle_user_suggestion,
    handle_user_transformation_result,
    show_final_history,
)

__all__ = [
    # Состояние
    "UserState",
    "user_states",
    "get_user_state",
    "create_user_state",
    "reset_user_state",
    # Rate limiting
    "RateLimiter",
    "rate_limiter",
    # Утилиты
    "send_status_message",
    "edit_status_message",
    "update_status_with_progress",
    "get_progress_indicator",
    # Клавиатуры
    "get_transformations_keyboard",
    "get_verification_keyboard",
    "get_user_transformation_keyboard",
    # Обработчики
    "start",
    "help_command",
    "cancel",
    "show_history",
    "handle_task",
    "handle_transformation_choice",
    "handle_custom_transformation",
    "handle_user_suggestion",
    "handle_user_transformation_result",
    "show_final_history",
]

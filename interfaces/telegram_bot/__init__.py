"""
Модульный Telegram интерфейс.
Содержит разделенные компоненты для Telegram бота.
"""

# Обработчики команд
from .handlers import (
    cancel,
    handle_custom_transformation,
    handle_task,
    handle_transformation_choice,
    handle_user_suggestion,
    handle_user_transformation_result,
    help_command,
    show_final_history,
    show_history,
    start,
)
from .keyboards import (
    get_transformations_keyboard,
    get_user_transformation_keyboard,
    get_verification_keyboard,
)
from .rate_limiter import RateLimiter, rate_limiter

# Импортируем основные компоненты
from .state import (
    UserState,
    create_user_state,
    get_user_state,
    reset_user_state,
    user_states,
)
from .utils import (
    edit_status_message,
    get_progress_indicator,
    send_status_message,
    update_status_with_progress,
)

# Временно комментируем импорт renderers из-за зависимости matplotlib
# from .renderers import (
#     render_latex_to_image,
#     render_transformations_images,
#     fix_latex_expression,
#     check_and_suggest_rollback
# )


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

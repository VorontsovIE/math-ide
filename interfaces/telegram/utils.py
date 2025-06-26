"""
Утилиты для отправки сообщений в Telegram боте.
Содержит функции для управления статусными сообщениями с учетом лимитов API.
"""

import logging
import time
from typing import Optional, TYPE_CHECKING

# Избегаем прямого импорта telegram для предотвращения ошибок
# if TYPE_CHECKING:
#     from telegram import Update, Message

from .rate_limiter import rate_limiter

logger = logging.getLogger(__name__)


def get_progress_indicator(operation_time: float) -> str:
    """Генерирует индикатор прогресса на основе времени операции."""
    if operation_time < 5:
        return "🔄"
    elif operation_time < 10:
        return "⏳"
    elif operation_time < 15:
        return "⏰"
    else:
        return "🐌"


async def send_status_message(update, message: str, force_update: bool = False):
    """Отправляет сообщение со статусом с проверкой лимитов."""
    user_id = update.effective_user.id
    
    if not rate_limiter.can_update_status(user_id, force_update):
        logger.debug(f"Пропущено обновление статуса для пользователя {user_id} из-за лимитов")
        return None
    
    try:
        result = await update.message.reply_text(message)
        rate_limiter.record_status_update(user_id)
        return result
    except Exception as e:
        logger.error(f"Ошибка при отправке статуса: {e}")
        return None


async def edit_status_message(message: Message, new_text: str, user_id: int, force_update: bool = False) -> bool:
    """Редактирует сообщение со статусом с проверкой лимитов."""
    if not rate_limiter.can_update_status(user_id, force_update):
        logger.debug(f"Пропущено редактирование статуса для пользователя {user_id} из-за лимитов")
        return False
    
    try:
        await message.edit_text(new_text)
        rate_limiter.record_status_update(user_id)
        return True
    except Exception as e:
        logger.error(f"Ошибка при редактировании статуса: {e}")
        return False


async def update_status_with_progress(message: Message, base_text: str, user_id: int) -> bool:
    """Обновляет статус с индикатором прогресса для длительных операций."""
    if not rate_limiter.should_show_progress(user_id):
        return False
    
    current_time = time.time()
    state = get_user_state(user_id)
    if not state:
        return False
    
    operation_time = current_time - state.current_operation_start
    progress_indicator = get_progress_indicator(operation_time)
    
    # Добавляем информацию о времени выполнения
    if operation_time > 5:
        progress_text = f"{base_text}\n\n⏱️ Выполняется уже {int(operation_time)} сек..."
    else:
        progress_text = base_text
    
    return await edit_status_message(message, progress_text, user_id) 
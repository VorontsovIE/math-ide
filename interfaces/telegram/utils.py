"""
Утилиты для Telegram бота.
Содержит вспомогательные функции для отправки сообщений и обновления статуса.
"""

import time
import logging
from typing import Optional

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telegram import Update, Message

from .rate_limiter import rate_limiter, get_progress_indicator
from .state import get_user_state

# Получаем логгер
logger = logging.getLogger(__name__)


async def send_status_message(update: Update, message: str, force_update: bool = False) -> Optional[Message]:
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
"""
Модуль ограничения запросов для Telegram бота.
Содержит RateLimiter для управления частотой обновлений статуса.
"""

import time
import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .state import UserState

# Получаем логгер
logger = logging.getLogger(__name__)

# Константы для управления лимитами
MIN_STATUS_UPDATE_INTERVAL = 2.0  # Минимальный интервал между обновлениями статуса (в секундах)
MAX_STATUS_UPDATES_PER_MINUTE = 20  # Максимальное количество обновлений статуса в минуту
PROGRESS_UPDATE_INTERVAL = 3.0  # Интервал для обновления прогресса


class RateLimiter:
    """Класс для управления лимитами API."""
    
    def __init__(self) -> None:
        self.global_last_update = 0.0
        self.global_update_count = 0
        self.global_reset_time = time.time()
    
    def can_update_status(self, user_id: int, force_update: bool = False) -> bool:
        """Проверяет, можно ли обновить статус для пользователя."""
        # Импорт здесь для избежания циклических зависимостей
        from .state import get_user_state
        
        current_time = time.time()
        
        # Получаем состояние пользователя
        state = get_user_state(user_id)
        if not state:
            return True
        
        # Принудительное обновление (для важных сообщений)
        if force_update:
            return True
        
        # Проверяем минимальный интервал
        if current_time - state.last_status_update < MIN_STATUS_UPDATE_INTERVAL:
            logger.debug(f"Слишком частое обновление для пользователя {user_id}")
            return False
        
        # Сбрасываем счетчик, если прошла минута
        if current_time - state.status_reset_time >= 60:
            state.status_update_count = 0
            state.status_reset_time = current_time
        
        # Проверяем лимит обновлений в минуту
        if state.status_update_count >= MAX_STATUS_UPDATES_PER_MINUTE:
            logger.warning(f"Превышен лимит обновлений статуса для пользователя {user_id}")
            return False
        
        return True
    
    def should_show_progress(self, user_id: int) -> bool:
        """Проверяет, нужно ли показать прогресс для длительных операций."""
        # Импорт здесь для избежания циклических зависимостей
        from .state import get_user_state
        
        current_time = time.time()
        state = get_user_state(user_id)
        
        if not state:
            return False
        
        # Показываем прогресс, если операция длится больше 3 секунд
        return current_time - state.current_operation_start >= PROGRESS_UPDATE_INTERVAL
    
    def record_status_update(self, user_id: int) -> None:
        """Записывает обновление статуса."""
        # Импорт здесь для избежания циклических зависимостей
        from .state import get_user_state
        
        current_time = time.time()
        
        # Обновляем глобальные счетчики
        if current_time - self.global_reset_time >= 60:
            self.global_update_count = 0
            self.global_reset_time = current_time
        
        self.global_update_count += 1
        self.global_last_update = current_time
        
        # Обновляем счетчики пользователя
        state = get_user_state(user_id)
        if state:
            state.last_status_update = current_time
            state.status_update_count += 1
    
    def start_operation(self, user_id: int) -> None:
        """Отмечает начало новой операции."""
        # Импорт здесь для избежания циклических зависимостей
        from .state import get_user_state
        
        current_time = time.time()
        state = get_user_state(user_id)
        if state:
            state.current_operation_start = current_time


# Глобальный экземпляр rate limiter
rate_limiter = RateLimiter()


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
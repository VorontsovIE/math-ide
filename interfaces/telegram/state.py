"""
Модуль управления состоянием пользователей Telegram бота.
Содержит UserState и глобальное хранилище состояний пользователей.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.history import SolutionHistory
from core.types import SolutionStep, Transformation


@dataclass
class UserState:
    """Состояние пользователя в боте."""

    history: Optional[SolutionHistory] = None
    current_step: Optional[SolutionStep] = None
    available_transformations: List[Transformation] = field(default_factory=list)
    last_status_update: float = 0.0  # Время последнего обновления статуса
    status_update_count: int = 0  # Счетчик обновлений статуса в текущей минуте
    status_reset_time: float = 0.0  # Время сброса счетчика обновлений
    current_operation_start: float = 0.0  # Время начала текущей операции
    waiting_for_custom_transformation: bool = (
        False  # Ожидание ввода пользовательского преобразования
    )
    custom_transformation_target_step_id: Optional[str] = (
        None  # ID шага для применения пользовательского преобразования
    )
    # Новые поля для проверки преобразований
    waiting_for_user_suggestion: bool = False  # Ожидание предложения пользователя
    waiting_for_user_result: bool = False  # Ожидание результата от пользователя
    verification_context: Optional[Dict[str, Any]] = None  # Контекст для проверки


# Хранилище состояний пользователей
user_states: Dict[int, UserState] = {}


def get_user_state(user_id: int) -> Optional[UserState]:
    """Получает состояние пользователя."""
    return user_states.get(user_id)


def create_user_state(user_id: int) -> UserState:
    """Создает новое состояние для пользователя."""
    state = UserState()
    user_states[user_id] = state
    return state


def reset_user_state(user_id: int) -> UserState:
    """Сбрасывает состояние пользователя."""
    return create_user_state(user_id)


def update_user_state(user_id: int, **kwargs: Any) -> None:
    """Обновляет состояние пользователя."""
    state = user_states.get(user_id)
    if state:
        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)

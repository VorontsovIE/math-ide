"""
Модуль управления состоянием пользователей Telegram бота.
Содержит UserState и глобальное хранилище состояний пользователей.
"""

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.history import SolutionHistory
from core.types import SolutionStep, Transformation


@dataclass
class TransformationStorage:
    """Хранилище преобразований с уникальными идентификаторами."""
    
    transformations: Dict[str, Transformation] = field(default_factory=dict)
    step_transformations: Dict[str, List[str]] = field(default_factory=dict)  # step_id -> [transformation_ids]
    
    def add_transformations(self, step_id: str, transformations: List[Transformation]) -> List[str]:
        """Добавляет преобразования и возвращает их идентификаторы."""
        transformation_ids = []
        for transformation in transformations:
            transformation_id = str(uuid.uuid4())
            self.transformations[transformation_id] = transformation
            transformation_ids.append(transformation_id)
        
        self.step_transformations[step_id] = transformation_ids
        return transformation_ids
    
    def get_transformation(self, transformation_id: str) -> Optional[Transformation]:
        """Получает преобразование по идентификатору."""
        return self.transformations.get(transformation_id)
    
    def get_step_transformations(self, step_id: str) -> List[Transformation]:
        """Получает все преобразования для шага."""
        transformation_ids = self.step_transformations.get(step_id, [])
        return [self.transformations[tid] for tid in transformation_ids if tid in self.transformations]
    
    def cleanup_old_transformations(self, max_age_hours: int = 24) -> None:
        """Очищает старые преобразования (пока просто заглушка)."""
        # TODO: Реализовать очистку старых преобразований
        pass


@dataclass
class UserState:
    """Состояние пользователя в боте."""

    history: Optional[SolutionHistory] = None
    current_step: Optional[SolutionStep] = None
    available_transformations: List[Transformation] = field(default_factory=list)
    transformation_storage: TransformationStorage = field(default_factory=TransformationStorage)
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
    # Новые поля для сценария 2024-06
    student_step_number: int = 1  # Номер шага студента (сколько раз зашёл в пункт 2)
    correct_free_answers: int = 0  # Количество правильных ответов в свободной форме
    total_free_answers: int = 0  # Всего попыток в свободной форме
    correct_choice_answers: int = 0  # Количество правильных ответов при выборе результата
    total_choice_answers: int = 0  # Всего попыток при выборе результата
    # Кэш для вариантов результата преобразования: (step_number, transformation_id) -> list[dict]
    result_variants_cache: dict = field(default_factory=dict)
    # Поле для контроля состояния пользователя
    last_chosen_transformation_id: Optional[str] = None  # ID последнего выбранного преобразования


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

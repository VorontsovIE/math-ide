from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid


@dataclass
class HistoryStep:
    """
    Представляет один шаг в истории решения задачи.
    Содержит всю информацию о шаге для возможности отката.
    """
    id: str
    step_number: int
    expression: str
    available_transformations: List[Dict[str, Any]]
    chosen_transformation: Optional[Dict[str, Any]]
    result_expression: Optional[str]
    timestamp: datetime
    parent_id: Optional[str] = None  # Для поддержки ветвления в будущем
    metadata: Dict[str, Any] = field(default_factory=dict)


class SolutionHistory:
    """
    Управляет историей решения математической задачи.
    Поддерживает просмотр истории и задел для отката к произвольному шагу.
    """
    
    def __init__(self, original_task: str):
        self.original_task = original_task
        self.steps: List[HistoryStep] = []
        self.current_step_number = 0
    
    def add_step(self, 
                 expression: str, 
                 available_transformations: List[Dict[str, Any]],
                 chosen_transformation: Optional[Dict[str, Any]] = None,
                 result_expression: Optional[str] = None) -> str:
        """
        Добавляет новый шаг в историю.
        
        Args:
            expression: Выражение шага
            available_transformations: Список доступных преобразований
            chosen_transformation: Выбранное преобразование (если есть)
            result_expression: Результат применения преобразования (если есть)
            
        Returns:
            ID созданного шага
        """
        step_id = str(uuid.uuid4())
        
        # Определяем parent_id (ID предыдущего шага)
        parent_id = None
        if self.steps:
            parent_id = self.steps[-1].id
        
        step = HistoryStep(
            id=step_id,
            step_number=self.current_step_number,
            expression=expression,
            available_transformations=available_transformations,
            chosen_transformation=chosen_transformation,
            result_expression=result_expression,
            timestamp=datetime.now(),
            parent_id=parent_id
        )
        
        self.steps.append(step)
        self.current_step_number += 1
        
        return step_id
    
    def get_current_step(self) -> Optional[HistoryStep]:
        """Возвращает текущий (последний) шаг."""
        return self.steps[-1] if self.steps else None
    
    def get_step_by_id(self, step_id: str) -> Optional[HistoryStep]:
        """Возвращает шаг по ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_step_by_number(self, step_number: int) -> Optional[HistoryStep]:
        """Возвращает шаг по номеру."""
        for step in self.steps:
            if step.step_number == step_number:
                return step
        return None
    
    def get_all_steps(self) -> List[HistoryStep]:
        """Возвращает все шаги в хронологическом порядке."""
        return self.steps.copy()
    
    def get_steps_count(self) -> int:
        """Возвращает количество шагов в истории."""
        return len(self.steps)
    
    def is_empty(self) -> bool:
        """Проверяет, пуста ли история."""
        return len(self.steps) == 0
    
    def get_step_summary(self, step: HistoryStep) -> Dict[str, Any]:
        """
        Возвращает краткую сводку шага для отображения в интерфейсе.
        """
        summary = {
            "step_number": step.step_number,
            "expression": step.expression,
            "timestamp": step.timestamp.isoformat(),
            "has_chosen_transformation": step.chosen_transformation is not None,
            "has_result": step.result_expression is not None
        }
        
        if step.chosen_transformation:
            summary["chosen_transformation"] = {
                "description": step.chosen_transformation.get("description", ""),
                "type": step.chosen_transformation.get("type", ""),
                "expression": step.chosen_transformation.get("expression", "")
            }
        
        if step.result_expression:
            summary["result_expression"] = step.result_expression
        
        return summary
    
    def get_full_history_summary(self) -> Dict[str, Any]:
        """
        Возвращает полную сводку истории для отображения.
        """
        return {
            "original_task": self.original_task,
            "total_steps": len(self.steps),
            "current_step_number": self.current_step_number,
            "steps": [self.get_step_summary(step) for step in self.steps],
            "is_complete": self.steps and self.steps[-1].result_expression is not None
        }
    
    def export_history(self) -> Dict[str, Any]:
        """
        Экспортирует историю в формат для сохранения/загрузки.
        """
        return {
            "original_task": self.original_task,
            "current_step_number": self.current_step_number,
            "steps": [
                {
                    "id": step.id,
                    "step_number": step.step_number,
                    "expression": step.expression,
                    "available_transformations": step.available_transformations,
                    "chosen_transformation": step.chosen_transformation,
                    "result_expression": step.result_expression,
                    "timestamp": step.timestamp.isoformat(),
                    "parent_id": step.parent_id,
                    "metadata": step.metadata
                }
                for step in self.steps
            ]
        }
    
    def import_history(self, history_data: Dict[str, Any]) -> None:
        """
        Импортирует историю из сохранённого формата.
        """
        self.original_task = history_data["original_task"]
        self.current_step_number = history_data["current_step_number"]
        
        self.steps = []
        for step_data in history_data["steps"]:
            step = HistoryStep(
                id=step_data["id"],
                step_number=step_data["step_number"],
                expression=step_data["expression"],
                available_transformations=step_data["available_transformations"],
                chosen_transformation=step_data["chosen_transformation"],
                result_expression=step_data["result_expression"],
                timestamp=datetime.fromisoformat(step_data["timestamp"]),
                parent_id=step_data["parent_id"],
                metadata=step_data["metadata"]
            )
            self.steps.append(step)
    
    def rollback_to_step(self, step_number: int) -> bool:
        """
        Возвращается к указанному шагу, отбрасывая все последующие шаги.
        
        Args:
            step_number: Номер шага, к которому нужно вернуться
            
        Returns:
            bool: True если возврат успешен, False если шаг не найден
        """
        # Проверяем, что номер шага валиден
        if step_number < 0 or step_number >= len(self.steps):
            return False
        
        # Находим шаг по номеру
        target_step = None
        for step in self.steps:
            if step.step_number == step_number:
                target_step = step
                break
        
        if target_step is None:
            return False
        
        # Сохраняем только шаги до целевого шага включительно
        self.steps = [step for step in self.steps if step.step_number <= step_number]
        
        # Обновляем текущий номер шага
        self.current_step_number = step_number + 1
        
        return True
    
    def rollback_to_step_by_id(self, step_id: str) -> bool:
        """
        Возвращается к указанному шагу по ID, отбрасывая все последующие шаги.
        
        Args:
            step_id: ID шага, к которому нужно вернуться
            
        Returns:
            bool: True если возврат успешен, False если шаг не найден
        """
        target_step = self.get_step_by_id(step_id)
        if target_step is None:
            return False
        
        return self.rollback_to_step(target_step.step_number)
    
    def get_current_expression(self) -> str:
        """
        Возвращает выражение текущего (последнего) шага.
        Если есть результат преобразования, возвращает его, иначе исходное выражение шага.
        """
        current_step = self.get_current_step()
        if current_step is None:
            return self.original_task
        
        # Возвращаем результат, если он есть, иначе исходное выражение шага
        return current_step.result_expression or current_step.expression
    
    def can_rollback(self) -> bool:
        """Проверяет, возможен ли откат (есть ли шаги в истории)."""
        return len(self.steps) > 1  # Больше одного шага (исключая начальный)


# Пример использования для демонстрации
if __name__ == "__main__":
    # Создаём историю
    history = SolutionHistory("Решить уравнение: 2(x + 1) = 4")
    
    # Добавляем первый шаг
    step1_id = history.add_step(
        expression="2(x + 1) = 4",
        available_transformations=[
            {
                "description": "Раскрыть скобки в левой части",
                "type": "expand",
                "expression": "2x + 2 = 4"
            },
            {
                "description": "Разделить обе части на 2",
                "type": "divide", 
                "expression": "x + 1 = 2"
            }
        ],
        chosen_transformation={
            "description": "Раскрыть скобки в левой части",
            "type": "expand",
            "expression": "2x + 2 = 4"
        },
        result_expression="2x + 2 = 4"
    )
    
    
    step2_id = history.add_step(
        expression="2x + 2 = 4",
        available_transformations=[
            {
                "description": "Вычесть 2 из обеих частей",
                "type": "subtract",
                "expression": "2x = 2"
            },
            {
                "description": "Разделить обе части на 2",
                "type": "divide",
                "expression": "x + 1 = 2"
            }
        ],
        chosen_transformation={
            "description": "Разделить обе части на 2",
            "type": "divide",
            "expression": "x + 1 = 2"
        },
        result_expression="x + 1 = 2"
    )
    
    # Выводим сводку
    print("Сводка истории:")
    summary = history.get_full_history_summary()
    for step in summary["steps"]:
        print(f"Шаг {step['step_number']}: {step['expression']}")
        if step['has_chosen_transformation']:
            print(f"  Выбрано: {step['chosen_transformation']['description']}")
        if step['has_result']:
            print(f"  Результат: {step['result_expression']}")
        print() 
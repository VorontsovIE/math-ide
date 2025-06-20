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
    latex_content: str
    available_transformations: List[Dict[str, Any]]
    chosen_transformation: Optional[Dict[str, Any]]
    result_latex: Optional[str]
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
                 latex_content: str, 
                 available_transformations: List[Dict[str, Any]],
                 chosen_transformation: Optional[Dict[str, Any]] = None,
                 result_latex: Optional[str] = None) -> str:
        """
        Добавляет новый шаг в историю.
        
        Args:
            latex_content: LaTeX-содержимое шага
            available_transformations: Список доступных преобразований
            chosen_transformation: Выбранное преобразование (если есть)
            result_latex: Результат применения преобразования (если есть)
            
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
            latex_content=latex_content,
            available_transformations=available_transformations,
            chosen_transformation=chosen_transformation,
            result_latex=result_latex,
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
            "latex_content": step.latex_content,
            "timestamp": step.timestamp.isoformat(),
            "has_chosen_transformation": step.chosen_transformation is not None,
            "has_result": step.result_latex is not None
        }
        
        if step.chosen_transformation:
            summary["chosen_transformation"] = {
                "description": step.chosen_transformation.get("description", ""),
                "type": step.chosen_transformation.get("type", ""),
                "latex": step.chosen_transformation.get("latex", "")
            }
        
        if step.result_latex:
            summary["result_latex"] = step.result_latex
        
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
            "is_complete": self.steps and self.steps[-1].result_latex is not None
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
                    "latex_content": step.latex_content,
                    "available_transformations": step.available_transformations,
                    "chosen_transformation": step.chosen_transformation,
                    "result_latex": step.result_latex,
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
                latex_content=step_data["latex_content"],
                available_transformations=step_data["available_transformations"],
                chosen_transformation=step_data["chosen_transformation"],
                result_latex=step_data["result_latex"],
                timestamp=datetime.fromisoformat(step_data["timestamp"]),
                parent_id=step_data["parent_id"],
                metadata=step_data["metadata"]
            )
            self.steps.append(step)


# Пример использования для демонстрации
if __name__ == "__main__":
    # Создаём историю
    history = SolutionHistory("Решить уравнение: 2(x + 1) = 4")
    
    # Добавляем первый шаг
    step1_id = history.add_step(
        latex_content="2(x + 1) = 4",
        available_transformations=[
            {
                "description": "Раскрыть скобки в левой части",
                "type": "expand",
                "latex": "2x + 2 = 4"
            },
            {
                "description": "Разделить обе части на 2",
                "type": "divide", 
                "latex": "x + 1 = 2"
            }
        ]
    )
    
    # Выбираем преобразование и добавляем результат
    chosen_transformation = {
        "description": "Раскрыть скобки в левой части",
        "type": "expand",
        "latex": "2x + 2 = 4"
    }
    
    step2_id = history.add_step(
        latex_content="2x + 2 = 4",
        available_transformations=[
            {
                "description": "Вычесть 2 из обеих частей",
                "type": "subtract",
                "latex": "2x = 2"
            },
            {
                "description": "Разделить обе части на 2",
                "type": "divide",
                "latex": "x = 1"
            }
        ],
        chosen_transformation=chosen_transformation,
        result_latex="2x + 2 = 4"
    )
    
    # Выводим сводку
    print("Сводка истории:")
    summary = history.get_full_history_summary()
    for step in summary["steps"]:
        print(f"Шаг {step['step_number']}: {step['latex_content']}")
        if step['has_chosen_transformation']:
            print(f"  Выбрано: {step['chosen_transformation']['description']}")
        if step['has_result']:
            print(f"  Результат: {step['result_latex']}")
        print() 
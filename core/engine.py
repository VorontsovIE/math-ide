from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from enum import Enum


class BaseTransformationType(Enum):
    """
    Базовые типы преобразований, которые служат ориентиром для GPT.
    GPT может предлагать и другие типы, если они релевантны.
    """
    ADD = "add"
    SUBTRACT = "subtract"
    MULTIPLY = "multiply"
    DIVIDE = "divide"
    FACTOR = "factor"
    EXPAND = "expand"
    COLLECT_TERMS = "collect_terms"
    SUBSTITUTE = "substitute"
    EXPAND_CASES = "expand_cases"  # Для разбора случаев, например, с модулем |x|
    SIMPLIFY = "simplify"


@dataclass
class TransformationParameter:
    """Параметр, который может быть использован в преобразовании."""
    name: str
    value: Any
    options: Optional[List[Any]] = None  # Возможные значения (для будущей параметризации)


@dataclass
class Transformation:
    """Представляет одно математическое преобразование."""
    description: str
    latex: str
    type: str  # Тип преобразования (желательно из BaseTransformationType)
    parameters: Optional[List[TransformationParameter]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SolutionStep:
    """
    Представляет один шаг в процессе решения математической задачи.
    Это может быть уравнение, неравенство, система и т.д. на любом этапе.
    """
    latex_content: str  # Полное содержимое задачи в формате LaTeX


@dataclass
class GenerationResult:
    """Результат генерации, содержащий список возможных преобразований."""
    transformations: List[Transformation]


class TransformationEngine:
    """
    Ядро для генерации допустимых математических преобразований.
    """

    def __init__(self, model: str = "openai"):
        self.model = model  # Задел для поддержки разных моделей в будущем

    def generate_transformations(self, step: SolutionStep) -> GenerationResult:
        """
        Генерирует список допустимых преобразований для текущего шага решения.
        В MVP-версии это заглушка.
        """
        # TODO: Интеграция с GPT API и реальная логика генерации.
        # Пример-заглушка для демонстрации:
        dummy_transformation = Transformation(
            description="Раскрыть скобки в левой части",
            latex="2x + 2 = 4",
            type=BaseTransformationType.EXPAND.value,
        )
        return GenerationResult(transformations=[dummy_transformation])

    def apply_transformation(self, current_step: SolutionStep, transformation: Transformation) -> SolutionStep:
        """
        Применяет выбранное преобразование к текущему шагу решения.
        В MVP-версии просто возвращает новый шаг с LaTeX из преобразования.
        """
        # TODO: В будущем здесь может быть более сложная логика,
        # например, валидация применимости преобразования.
        return SolutionStep(latex_content=transformation.latex)


# Пример использования для демонстрации и отладки
if __name__ == "__main__":
    engine = TransformationEngine()
    # Пример начального шага задачи
    initial_step = SolutionStep(latex_content="2(x + 1) = 4")
    print(f"Начальный шаг: {initial_step.latex_content}")

    # 1. Генерируем преобразования
    generation_result = engine.generate_transformations(initial_step)
    print("\nВозможные преобразования:")
    for i, t in enumerate(generation_result.transformations):
        print(f"{i+1}. Тип: {t.type}, Описание: {t.description}, Результат: {t.latex}")

    # 2. Применяем первое из сгенерированных преобразований
    if generation_result.transformations:
        chosen_transformation = generation_result.transformations[0]
        print(f"\nВыбрано преобразование: '{chosen_transformation.description}'")
        
        new_step = engine.apply_transformation(initial_step, chosen_transformation)
        print(f"Новый шаг: {new_step.latex_content}")
    else:
        print("\nНет доступных преобразований.") 
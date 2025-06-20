import json
import random
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from enum import Enum
from pathlib import Path
import openai
from openai import OpenAI


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
    expression: str  # Было latex
    type: str  # Тип преобразования (желательно из BaseTransformationType)
    parameters: Optional[List[TransformationParameter]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SolutionStep:
    """
    Представляет один шаг в процессе решения математической задачи.
    Это может быть уравнение, неравенство, система и т.д. на любом этапе.
    """
    expression: str  # Было latex_content


@dataclass
class GenerationResult:
    """Результат генерации, содержащий список возможных преобразований."""
    transformations: List[Transformation]


@dataclass
class ApplyResult:
    """Результат применения преобразования."""
    result: str
    is_valid: bool
    explanation: str
    errors: Optional[List[str]] = None


@dataclass
class CheckResult:
    """Результат проверки завершённости решения."""
    is_solved: bool
    confidence: float
    explanation: str
    solution_type: str  # exact, approximate, partial
    next_steps: List[str] = field(default_factory=list)


class PromptManager:
    """Управляет загрузкой и подстановкой промптов."""
    
    def __init__(self, prompts_dir: str = "prompts"):
        self.prompts_dir = Path(prompts_dir)
    
    def load_prompt(self, filename: str) -> str:
        """Загружает промпт из файла."""
        prompt_path = self.prompts_dir / filename
        if not prompt_path.exists():
            raise FileNotFoundError(f"Промпт не найден: {prompt_path}")
        
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def format_prompt(self, prompt: str, **kwargs) -> str:
        """Форматирует промпт с подстановкой переменных."""
        return prompt.format(**kwargs)


class TransformationEngine:
    """
    Ядро для генерации допустимых математических преобразований.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.prompt_manager = PromptManager()
        
        # Загружаем промпты
        self.generation_prompt = self.prompt_manager.load_prompt("generation.md")
        self.apply_prompt = self.prompt_manager.load_prompt("apply.md")
        self.check_prompt = self.prompt_manager.load_prompt("check.md")

    def generate_transformations(self, step: SolutionStep) -> GenerationResult:
        """
        Генерирует список допустимых преобразований для текущего шага решения.
        """
        try:
            # Форматируем промпт
            transformation_types = [t.value for t in BaseTransformationType]
            formatted_prompt = self.prompt_manager.format_prompt(
                self.generation_prompt,
                current_state=step.expression,
                transformation_types=", ".join(transformation_types)
            )
            
            # Запрос к GPT
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты - эксперт по математике. Отвечай только в JSON-формате."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            # Парсим ответ
            content = response.choices[0].message.content
            transformations_data = json.loads(content)
            
            # Преобразуем в объекты Transformation
            transformations = []
            for data in transformations_data:
                transformation = Transformation(
                    description=data["description"],
                    expression=data["expression"],
                    type=data["type"],
                    metadata=data.get("metadata", {})
                )
                transformations.append(transformation)
            
            # Сортировка по полезности (good > neutral > bad)
            def usefulness_key(tr: Transformation):
                value = tr.metadata.get("usefullness", "neutral")
                if value == "good":
                    return 0
                elif value == "neutral":
                    return 1
                else:
                    return 2
            transformations.sort(key=usefulness_key)
            # Выбор и перемешивание топ-5
            top5 = transformations[:5]
            if len(top5) > 1:
                random.shuffle(top5)
            return GenerationResult(transformations=top5)
            
        except Exception as e:
            # В случае ошибки возвращаем заглушку
            print(f"Ошибка генерации преобразований: {e}")
            dummy_transformation = Transformation(
                description="Раскрыть скобки в левой части",
                expression="2x + 2 = 4",
                type=BaseTransformationType.EXPAND.value,
                metadata={"difficulty": "easy", "reasoning": "Заглушка при ошибке API"}
            )
            return GenerationResult(transformations=[dummy_transformation])

    def apply_transformation(self, current_step: SolutionStep, transformation: Transformation) -> ApplyResult:
        """
        Применяет выбранное преобразование к текущему шагу решения.
        """
        try:
            # Форматируем промпт
            formatted_prompt = self.prompt_manager.format_prompt(
                self.apply_prompt,
                current_state=current_step.expression,
                transformation_description=transformation.description,
                transformation_type=transformation.type
            )
            
            # Запрос к GPT
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты - эксперт по математике. Отвечай только в JSON-формате."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Парсим ответ
            content = response.choices[0].message.content
            result_data = json.loads(content)
            
            return ApplyResult(
                result=result_data.get("result", ""),
                is_valid=result_data.get("is_valid", False),
                explanation=result_data.get("explanation", ""),
                errors=result_data.get("errors")
            )
            
        except Exception as e:
            # В случае ошибки возвращаем ошибку
            print(f"Ошибка применения преобразования: {e}")
            return ApplyResult(
                result="",
                is_valid=False,
                explanation=f"Ошибка при применении преобразования: {e}",
                errors=[str(e)]
            )

    def check_solution_completeness(self, current_step: SolutionStep, original_task: str) -> CheckResult:
        """
        Проверяет, завершено ли решение задачи.
        """
        try:
            # Форматируем промпт
            formatted_prompt = self.prompt_manager.format_prompt(
                self.check_prompt,
                current_state=current_step.expression,
                original_task=original_task
            )
            
            # Запрос к GPT
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты - эксперт по математике. Отвечай только в JSON-формате."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # Парсим ответ
            content = response.choices[0].message.content
            result_data = json.loads(content)
            
            return CheckResult(
                is_solved=result_data.get("is_solved", False),
                confidence=result_data.get("confidence", 0.0),
                explanation=result_data.get("explanation", ""),
                solution_type=result_data.get("solution_type", "partial"),
                next_steps=result_data.get("next_steps", [])
            )
            
        except Exception as e:
            # В случае ошибки возвращаем неопределённый результат
            print(f"Ошибка проверки завершённости: {e}")
            return CheckResult(
                is_solved=False,
                confidence=0.0,
                explanation=f"Ошибка при проверке завершённости: {e}",
                solution_type="partial",
                next_steps=["Проверить подключение к API"]
            )


# Пример использования для демонстрации и отладки
if __name__ == "__main__":
    # Для демонстрации используем заглушку без API ключа
    engine = TransformationEngine()
    
    # Пример начального шага задачи
    initial_step = SolutionStep(expression="2(x + 1) = 4")
    print(f"Начальный шаг: {initial_step.expression}")

    # 1. Генерируем преобразования
    generation_result = engine.generate_transformations(initial_step)
    print("\nВозможные преобразования:")
    for i, t in enumerate(generation_result.transformations):
        print(f"{i+1}. Тип: {t.type}, Описание: {t.description}, Результат: {t.expression}")

    # 2. Применяем первое из сгенерированных преобразований
    if generation_result.transformations:
        chosen_transformation = generation_result.transformations[0]
        print(f"\nВыбрано преобразование: '{chosen_transformation.description}'")
        
        apply_result = engine.apply_transformation(initial_step, chosen_transformation)
        if apply_result.is_valid:
            new_step = SolutionStep(expression=apply_result.result)
            print(f"Новый шаг: {new_step.expression}")
            print(f"Объяснение: {apply_result.explanation}")
        else:
            print(f"Ошибка применения: {apply_result.explanation}")
    else:
        print("\nНет доступных преобразований.") 
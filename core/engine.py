import json
import random
import logging
from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from enum import Enum
from pathlib import Path
import openai
from openai import OpenAI

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Добавляем цветной форматтер для консоли
try:
    import coloredlogs
    coloredlogs.install(
        level='INFO',
        logger=logger,
        fmt="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )
except ImportError:
    logger.info("coloredlogs не установлен. Используется стандартное логирование.")


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
    CUSTOM = "custom"

    @classmethod
    def descriptions(cls):
        return {
            cls.ADD.value: "добавление к обеим частям",
            cls.SUBTRACT.value: "вычитание из обеих частей",
            cls.MULTIPLY.value: "умножение обеих частей",
            cls.DIVIDE.value: "деление обеих частей",
            cls.FACTOR.value: "разложение на множители",
            cls.EXPAND.value: "раскрытие скобок",
            cls.COLLECT_TERMS.value: "приведение подобных слагаемых",
            cls.SUBSTITUTE.value: "подстановка",
            cls.EXPAND_CASES.value: "разбор случаев (например, с модулем)",
            cls.SIMPLIFY.value: "упрощение выражения",
            cls.CUSTOM.value: "любое другое преобразование"
        }


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


def get_transformation_types_markdown() -> str:
    desc = BaseTransformationType.descriptions()
    return "\n".join([f"- `{k}` — {v}" for k, v in desc.items()])


class TransformationEngine:
    """
    Ядро для генерации допустимых математических преобразований.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.prompt_manager = PromptManager()
        
        logger.info(f"Инициализация TransformationEngine с моделью {model}")
        
        # Загружаем промпты
        logger.debug("Загрузка промптов...")
        self.generation_prompt = self.prompt_manager.load_prompt("generation.md")
        self.apply_prompt = self.prompt_manager.load_prompt("apply.md")
        self.check_prompt = self.prompt_manager.load_prompt("check.md")
        logger.debug("Промпты успешно загружены")

    def generate_transformations(self, step: SolutionStep) -> GenerationResult:
        """
        Генерирует список возможных математических преобразований для текущего шага.
        """
        try:
            logger.info("Генерация преобразований для выражения: %s", step.expression)
            
            # Форматируем промпт
            formatted_prompt = self.prompt_manager.format_prompt(
                self.generation_prompt,
                current_state=step.expression,
                transformation_types=get_transformation_types_markdown(),
                transformation_types_list=self.prompt_manager.load_prompt("transformation_types.md")
            )
            
            logger.debug("Отправка запроса к GPT для генерации преобразований")
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
            
            # Логируем токены
            usage = response.usage
            logger.info(
                "Использование токенов: промпт=%d, ответ=%d, всего=%d",
                usage.prompt_tokens,
                usage.completion_tokens,
                usage.total_tokens
            )
            
            # Парсим ответ
            content = response.choices[0].message.content.strip()
            logger.debug("Получен ответ от GPT: %s", content)
            
            # Проверяем, что ответ не пустой
            if not content:
                logger.error("Получен пустой ответ от GPT")
                return GenerationResult(transformations=[])
            
            # Пытаемся найти JSON в ответе (на случай, если GPT добавил лишний текст)
            json_start = content.find('[')
            json_end = content.rfind(']') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("Не найден JSON-массив в ответе GPT. Полный ответ: %s", content)
                return GenerationResult(transformations=[])
            
            json_content = content[json_start:json_end]
            logger.debug("Извлеченный JSON: %s", json_content)
            
            try:
                transformations_data = json.loads(json_content)
            except json.JSONDecodeError as e:
                logger.error("Ошибка парсинга JSON: %s", str(e))
                logger.error("Проблемный JSON: %s", json_content)
                logger.error("Полный ответ GPT: %s", content)
                return GenerationResult(transformations=[])
            
            # Проверяем, что это список
            if not isinstance(transformations_data, list):
                logger.error("Ожидался список преобразований, получен: %s", type(transformations_data))
                return GenerationResult(transformations=[])
            
            # Преобразуем в объекты Transformation
            transformations = []
            for i, data in enumerate(transformations_data):
                try:
                    if not isinstance(data, dict):
                        logger.warning("Пропускаем элемент %d: не является словарем", i)
                        continue
                    
                    # Проверяем обязательные поля
                    required_fields = ["description", "expression", "type"]
                    missing_fields = [field for field in required_fields if field not in data]
                    if missing_fields:
                        logger.warning("Пропускаем элемент %d: отсутствуют поля %s", i, missing_fields)
                        continue
                    
                    transformation = Transformation(
                        description=data["description"],
                        expression=data["expression"],
                        type=data["type"],
                        metadata=data.get("metadata", {})
                    )
                    transformations.append(transformation)
                    logger.debug("Добавлено преобразование %d: %s", i, transformation.description)
                    
                except Exception as e:
                    logger.warning("Ошибка при обработке преобразования %d: %s", i, str(e))
                    continue
            
            logger.info("Сгенерировано %d преобразований", len(transformations))
            
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
            
            logger.info("Отобрано %d лучших преобразований", len(top5))
            return GenerationResult(transformations=top5)
            
        except Exception as e:
            logger.error("Ошибка при генерации преобразований: %s", str(e), exc_info=True)
            return GenerationResult(transformations=[])

    def apply_transformation(self, current_step: SolutionStep, transformation: Transformation) -> ApplyResult:
        """
        Применяет выбранное преобразование к текущему шагу решения.
        """
        try:
            logger.info(
                "Применение преобразования типа '%s' к выражению: %s",
                transformation.type,
                current_step.expression
            )
            
            # Форматируем промпт
            formatted_prompt = self.prompt_manager.format_prompt(
                self.apply_prompt,
                current_state=current_step.expression,
                transformation_type=transformation.type,
                transformation_description=transformation.description,
                transformation_expression=transformation.expression
            )
            
            logger.debug("Отправка запроса к GPT для применения преобразования")
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
            
            # Логируем токены
            usage = response.usage
            logger.info(
                "Использование токенов: промпт=%d, ответ=%d, всего=%d",
                usage.prompt_tokens,
                usage.completion_tokens,
                usage.total_tokens
            )
            
            # Парсим ответ
            content = response.choices[0].message.content.strip()
            logger.debug("Получен ответ от GPT: %s", content)
            
            # Проверяем, что ответ не пустой
            if not content:
                logger.error("Получен пустой ответ от GPT")
                return ApplyResult(
                    result=current_step.expression,
                    is_valid=False,
                    explanation="Получен пустой ответ от GPT",
                    errors=["empty_response"]
                )
            
            # Пытаемся найти JSON в ответе (на случай, если GPT добавил лишний текст)
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("Не найден JSON-объект в ответе GPT. Полный ответ: %s", content)
                return ApplyResult(
                    result=current_step.expression,
                    is_valid=False,
                    explanation="Не найден JSON-объект в ответе GPT",
                    errors=["no_json_found"]
                )
            
            json_content = content[json_start:json_end]
            logger.debug("Извлеченный JSON: %s", json_content)
            
            try:
                result_data = json.loads(json_content)
            except json.JSONDecodeError as e:
                logger.error("Ошибка парсинга JSON: %s", str(e))
                logger.error("Проблемный JSON: %s", json_content)
                logger.error("Полный ответ GPT: %s", content)
                return ApplyResult(
                    result=current_step.expression,
                    is_valid=False,
                    explanation=f"Ошибка парсинга JSON: {str(e)}",
                    errors=["json_parse_error"]
                )
            
            # Проверяем обязательные поля
            required_fields = ["result_expression", "is_valid", "explanation"]
            missing_fields = [field for field in required_fields if field not in result_data]
            if missing_fields:
                logger.error("Отсутствуют обязательные поля в ответе: %s", missing_fields)
                logger.error("Полученные поля: %s", list(result_data.keys()))
                return ApplyResult(
                    result=current_step.expression,
                    is_valid=False,
                    explanation=f"Отсутствуют обязательные поля: {missing_fields}",
                    errors=["missing_fields"]
                )
            
            logger.info(
                "Результат применения: успех=%s, объяснение='%s'",
                result_data["is_valid"],
                result_data["explanation"]
            )
            
            return ApplyResult(
                result=result_data["result_expression"],
                is_valid=result_data["is_valid"],
                explanation=result_data["explanation"],
                errors=result_data.get("errors", [])
            )
            
        except Exception as e:
            logger.error("Ошибка при применении преобразования: %s", str(e), exc_info=True)
            return ApplyResult(
                result=current_step.expression,
                is_valid=False,
                explanation=f"Ошибка при применении преобразования: {str(e)}",
                errors=["internal_error"]
            )

    def check_solution_completeness(self, current_step: SolutionStep, original_task: str) -> CheckResult:
        """
        Проверяет, является ли текущий шаг завершающим для решения задачи.
        """
        try:
            logger.info("Проверка завершённости решения для выражения: %s", current_step.expression)
            
            # Форматируем промпт
            formatted_prompt = self.prompt_manager.format_prompt(
                self.check_prompt,
                current_state=current_step.expression,
                original_task=original_task
            )
            
            logger.debug("Отправка запроса к GPT для проверки завершённости")
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
            
            # Логируем токены
            usage = response.usage
            logger.info(
                "Использование токенов: промпт=%d, ответ=%d, всего=%d",
                usage.prompt_tokens,
                usage.completion_tokens,
                usage.total_tokens
            )
            
            # Парсим ответ
            content = response.choices[0].message.content.strip()
            logger.debug("Получен ответ от GPT: %s", content)
            
            # Проверяем, что ответ не пустой
            if not content:
                logger.error("Получен пустой ответ от GPT")
                return CheckResult(
                    is_solved=False,
                    confidence=0.0,
                    explanation="Получен пустой ответ от GPT",
                    solution_type="error"
                )
            
            # Пытаемся найти JSON в ответе (на случай, если GPT добавил лишний текст)
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("Не найден JSON-объект в ответе GPT. Полный ответ: %s", content)
                return CheckResult(
                    is_solved=False,
                    confidence=0.0,
                    explanation="Не найден JSON-объект в ответе GPT",
                    solution_type="error"
                )
            
            json_content = content[json_start:json_end]
            logger.debug("Извлеченный JSON: %s", json_content)
            
            try:
                check_data = json.loads(json_content)
            except json.JSONDecodeError as e:
                logger.error("Ошибка парсинга JSON: %s", str(e))
                logger.error("Проблемный JSON: %s", json_content)
                logger.error("Полный ответ GPT: %s", content)
                return CheckResult(
                    is_solved=False,
                    confidence=0.0,
                    explanation=f"Ошибка парсинга JSON: {str(e)}",
                    solution_type="error"
                )
            
            # Проверяем обязательные поля
            required_fields = ["is_solved", "confidence", "explanation", "solution_type"]
            missing_fields = [field for field in required_fields if field not in check_data]
            if missing_fields:
                logger.error("Отсутствуют обязательные поля в ответе: %s", missing_fields)
                logger.error("Полученные поля: %s", list(check_data.keys()))
                return CheckResult(
                    is_solved=False,
                    confidence=0.0,
                    explanation=f"Отсутствуют обязательные поля: {missing_fields}",
                    solution_type="error"
                )
            
            logger.info(
                "Результат проверки: решено=%s, уверенность=%.2f, тип='%s'",
                check_data["is_solved"],
                check_data["confidence"],
                check_data["solution_type"]
            )
            
            return CheckResult(
                is_solved=check_data["is_solved"],
                confidence=check_data["confidence"],
                explanation=check_data["explanation"],
                solution_type=check_data["solution_type"],
                next_steps=check_data.get("next_steps", [])
            )
            
        except Exception as e:
            logger.error("Ошибка при проверке завершённости: %s", str(e), exc_info=True)
            return CheckResult(
                is_solved=False,
                confidence=0.0,
                explanation=f"Ошибка при проверке завершённости: {str(e)}",
                solution_type="error"
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
# transformation_generator.py

import json
import random
import logging
from typing import List, Dict, Any, cast, Union

from ..types import (
    SolutionStep,
    Transformation,
    ParameterDefinition,
    ParameterType,
    GenerationResult,
    get_transformation_types_markdown,
)
from ..parsers import safe_json_parse
from ..prompts import PromptManager
from ..gpt_client import GPTClient

# Настройка логирования
logger = logging.getLogger(__name__)


class TransformationGenerator:
    """
    Компонент для генерации математических преобразований.
    Отвечает за анализ текущего состояния и предложение возможных преобразований.
    """

    def __init__(self, client: GPTClient, prompt_manager: PromptManager, preview_mode: bool = False) -> None:
        self.client = client
        self.prompt_manager = prompt_manager
        self.preview_mode = preview_mode
        
        # Загружаем промпт для генерации
        self.generation_prompt = self.prompt_manager.load_prompt("generation.md")
        logger.debug("TransformationGenerator инициализирован")

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
            # Запрос к GPT через GPTClient
            gpt_response = self.client.chat_completion(
                messages=[
                    {"role": "system", "content": "Ты - эксперт по математике. Отвечай только в JSON-формате."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.7
            )
            
            # Логируем токены
            logger.info(
                "Использование токенов: промпт=%d, ответ=%d, всего=%d",
                gpt_response.usage.prompt_tokens,
                gpt_response.usage.completion_tokens,
                gpt_response.usage.total_tokens
            )
            
            # Парсим ответ
            content = gpt_response.content
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
                # Используем безопасный парсинг JSON с автоматическим исправлением
                parsed_data = safe_json_parse(json_content)
                if not isinstance(parsed_data, list):
                    logger.error("Ожидался список преобразований, получен: %s", type(parsed_data))
                    return GenerationResult(transformations=[])
                transformations_data = parsed_data
            except Exception as e:
                logger.error("Ошибка парсинга JSON: %s", str(e))
                logger.error("Проблемный JSON: %s", json_content)
                logger.error("Полный ответ GPT: %s", content)
                return GenerationResult(transformations=[])
            
            # Преобразуем в объекты Transformation
            transformations = self._parse_transformations(transformations_data)
            
            logger.info("Сгенерировано %d преобразований", len(transformations))
            
            # Сортировка по полезности (good > neutral > bad)
            def usefulness_key(tr: Transformation) -> int:
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
            
            # Заполняем предварительные результаты, если включен режим предпоказа
            if self.preview_mode:
                logger.info("Заполнение предварительных результатов из поля expression")
                for transformation in top5:
                    # Используем уже имеющееся поле expression как предварительный результат
                    transformation.preview_result = transformation.expression
            
            return GenerationResult(transformations=top5)
            
        except Exception as e:
            logger.error("Ошибка при генерации преобразований: %s", str(e), exc_info=True)
            return GenerationResult(transformations=[])

    def _parse_transformations(self, transformations_data: List[Dict[str, Any]]) -> List[Transformation]:
        """
        Парсит данные преобразований из JSON в объекты Transformation.
        """
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
                
                # Обрабатываем определения параметров, если они есть
                parameter_definitions = []
                if data.get("parameter_definitions"):
                    param_defs = data["parameter_definitions"]
                    if isinstance(param_defs, list):
                        for param_def_data in param_defs:
                            if isinstance(param_def_data, dict):
                                try:
                                    param_def = ParameterDefinition(
                                        name=param_def_data["name"],
                                        prompt=param_def_data["prompt"],
                                        param_type=ParameterType(param_def_data["param_type"]),
                                        options=param_def_data.get("options"),
                                        default_value=param_def_data.get("default_value"),
                                        validation_rule=param_def_data.get("validation_rule"),
                                        suggested_values=param_def_data.get("suggested_values")
                                    )
                                    parameter_definitions.append(param_def)
                                except (KeyError, ValueError) as e:
                                    logger.warning("Ошибка при парсинге определения параметра: %s", str(e))
                
                transformation = Transformation(
                    description=data["description"],
                    expression=data["expression"],
                    type=data["type"],
                    parameter_definitions=parameter_definitions if parameter_definitions else None,
                    requires_user_input=data.get("requires_user_input", False),
                    metadata=data.get("metadata", {})
                )
                transformations.append(transformation)
                logger.debug("Добавлено преобразование %d: %s", i, transformation.description)
                
            except Exception as e:
                logger.warning("Ошибка при обработке преобразования %d: %s", i, str(e))
                continue
        
        return transformations

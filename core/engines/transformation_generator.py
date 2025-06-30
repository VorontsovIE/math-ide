# transformation_generator.py

import logging
import random
from typing import Any, Dict, List, cast

from ..gpt_client import GPTClient
from ..parsers import safe_json_parse
from ..prompts import PromptManager
from ..types import (
    GenerationResult,
    ParameterDefinition,
    ParameterType,
    SolutionStep,
    Transformation,
    get_transformation_types_markdown,
)

# Настройка логирования
logger = logging.getLogger(__name__)


class TransformationGenerator:
    """
    Компонент для генерации математических преобразований.
    Отвечает за анализ текущего состояния и предложение возможных преобразований.
    """

    def __init__(
        self,
        client: GPTClient,
        prompt_manager: PromptManager,
        preview_mode: bool = False,
    ) -> None:
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
                transformation_types_list=self.prompt_manager.load_prompt(
                    "transformation_types.md"
                ),
            )

            logger.debug("Отправка запроса к GPT для генерации преобразований")
            # Запрос к GPT через GPTClient
            gpt_response = self.client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "Ты - эксперт по математике. Отвечай только в JSON-формате.",
                    },
                    {"role": "user", "content": formatted_prompt},
                ],
                temperature=0.7,
            )

            # Логируем токены
            logger.info(
                "Использование токенов: промпт=%d, ответ=%d, всего=%d",
                gpt_response.usage.prompt_tokens,
                gpt_response.usage.completion_tokens,
                gpt_response.usage.total_tokens,
            )

            # Парсим ответ
            content = gpt_response.content
            logger.debug("Получен ответ от GPT: %s", content)

            # Проверяем, что ответ не пустой
            if not content:
                logger.error("Получен пустой ответ от GPT")
                return GenerationResult(transformations=[])

            # Пытаемся найти JSON в ответе (на случай, если GPT добавил лишний текст)
            json_start = content.find("[")
            json_end = content.rfind("]") + 1

            logger.debug("Поиск JSON-массива: начало=%d, конец=%d", json_start, json_end)

            if json_start == -1 or json_end == 0:
                logger.error(
                    "Не найден JSON-массив в ответе GPT. Полный ответ: %s", content
                )
                # Попробуем найти JSON-объект вместо массива
                json_start_obj = content.find("{")
                json_end_obj = content.rfind("}") + 1
                logger.debug("Попытка найти JSON-объект: начало=%d, конец=%d", json_start_obj, json_end_obj)
                
                if json_start_obj != -1 and json_end_obj != 0:
                    logger.info("Найден JSON-объект, попытка извлечь массив из него")
                    json_content_obj = content[json_start_obj:json_end_obj]
                    logger.debug("Извлеченный JSON-объект: %s", json_content_obj)
                    
                    try:
                        obj_data = safe_json_parse(json_content_obj)
                        if isinstance(obj_data, dict) and "transformations" in obj_data:
                            logger.info("Найден массив преобразований в объекте")
                            transformations_data = obj_data["transformations"]
                            if isinstance(transformations_data, list):
                                transformations = self._parse_transformations(transformations_data)
                                logger.info("Сгенерировано %d преобразований из объекта", len(transformations))
                                return self._process_transformations(transformations)
                    except Exception as e:
                        logger.error("Ошибка при парсинге JSON-объекта: %s", str(e))
                
                return GenerationResult(transformations=[])

            json_content = content[json_start:json_end]
            logger.debug("Извлеченный JSON: %s", json_content)

            transformations_data = self._parse_json_transformations(json_content)
            # Преобразуем в объекты Transformation
            transformations = self._parse_transformations(transformations_data)

            return self._process_transformations(transformations)

        except Exception as e:
            logger.error(
                "Ошибка при генерации преобразований: %s", str(e), exc_info=True
            )
            return GenerationResult(transformations=[])

    def _process_transformations(self, transformations: List[Transformation]) -> GenerationResult:
        """
        Обрабатывает список преобразований: сортирует, выбирает топ-5, заполняет предварительные результаты.
        """
        logger.info("Сгенерировано %d преобразований", len(transformations))
        
        # Детальное логирование преобразований
        logger.debug("Детали преобразований:")
        for i, tr in enumerate(transformations):
            logger.debug(f"  {i}: {tr.description} ({tr.type}) - полезность: {tr.metadata.get('usefullness', 'unknown')}")

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

    def _parse_json_transformations(self, json_content: str) -> List[Dict[str, Any]]:
        """
        Безопасно парсит JSON-массив преобразований. Всегда возвращает список.
        """
        try:
            parsed_data = safe_json_parse(json_content)
            if isinstance(parsed_data, list):
                # Используем cast для явного приведения типов
                return cast(List[Dict[str, Any]], parsed_data)
            logger.error(
                "Ожидался список преобразований, получен: %s", type(parsed_data)
            )
            return []
        except Exception as e:
            logger.error("Ошибка парсинга JSON: %s", str(e))
            logger.error("Проблемный JSON: %s", json_content)
            logger.error("Содержимое ответа GPT: %s", json_content)
            logger.error("Попытка извлечения JSON из позиций %d:%d", json_content.find("["), json_content.rfind("]") + 1)
            return []

    def _parse_transformations(
        self, transformations_data: List[Dict[str, Any]]
    ) -> List[Transformation]:
        """
        Парсит данные преобразований из JSON в объекты Transformation.
        """
        transformations = []
        logger.debug("Начинаем парсинг %d элементов преобразований", len(transformations_data))
        
        for i, data in enumerate(transformations_data):
            try:
                if not isinstance(data, dict):
                    logger.warning("Пропускаем элемент %d: не является словарем", i)
                    continue

                # Проверяем обязательные поля
                required_fields = ["description", "expression", "type"]
                missing_fields = [
                    field for field in required_fields if field not in data
                ]
                if missing_fields:
                    logger.warning(
                        "Пропускаем элемент %d: отсутствуют поля %s", i, missing_fields
                    )
                    logger.debug("Данные элемента %d: %s", i, data)
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
                                        param_type=ParameterType(
                                            param_def_data["param_type"]
                                        ),
                                        options=param_def_data.get("options"),
                                        default_value=param_def_data.get(
                                            "default_value"
                                        ),
                                        validation_rule=param_def_data.get(
                                            "validation_rule"
                                        ),
                                        suggested_values=param_def_data.get(
                                            "suggested_values"
                                        ),
                                    )
                                    parameter_definitions.append(param_def)
                                except (KeyError, ValueError) as e:
                                    logger.warning(
                                        "Ошибка при парсинге определения параметра: %s",
                                        str(e),
                                    )

                transformation = Transformation(
                    description=data["description"],
                    expression=data["expression"],
                    type=data["type"],
                    parameter_definitions=(
                        parameter_definitions if parameter_definitions else None
                    ),
                    requires_user_input=data.get("requires_user_input", False),
                    metadata=data.get("metadata", {}),
                )
                transformations.append(transformation)
                logger.debug(
                    "Добавлено преобразование %d: %s", i, transformation.description
                )

            except Exception as e:
                logger.warning("Ошибка при обработке преобразования %d: %s", i, str(e))
                logger.debug("Проблемные данные элемента %d: %s", i, data)
                continue

        logger.info("Успешно обработано %d из %d преобразований", len(transformations), len(transformations_data))
        return transformations

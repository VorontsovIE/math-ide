# transformation_applier.py

import logging
from typing import List, Dict, Any, cast

from ..types import (
    SolutionStep,
    Transformation,
    TransformationParameter,
    ApplyResult,
)
from ..parsers import safe_json_parse
from ..prompts import PromptManager
from ..gpt_client import GPTClient

# Настройка логирования
logger = logging.getLogger(__name__)


class TransformationApplier:
    """
    Компонент для применения математических преобразований.
    Отвечает за выполнение выбранных преобразований и получение результата.
    """

    def __init__(self, client: GPTClient, prompt_manager: PromptManager) -> None:
        self.client = client
        self.prompt_manager = prompt_manager
        
        # Загружаем промпт для применения
        self.apply_prompt = self.prompt_manager.load_prompt("apply.md")
        logger.debug("TransformationApplier инициализирован")

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
                transformation_expression=self._substitute_parameters_in_text(transformation.expression, transformation.parameters or [])
            )
            
            logger.debug("Отправка запроса к GPT для применения преобразования")
            # Запрос к GPT
            response = self.client.chat_completion(
                messages=[
                    {"role": "system", "content": "Ты - эксперт по математике. Отвечай только в JSON-формате."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.3
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
            content = response.content.strip()
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
                    explanation="Не найден JSON в ответе GPT",
                    errors=["invalid_json_response"]
                )
            
            json_content = content[json_start:json_end]
            logger.debug("Извлеченный JSON: %s", json_content)
            
            try:
                # Используем безопасный парсинг JSON с автоматическим исправлением
                parsed_data = safe_json_parse(json_content)
                # Проверяем, что это словарь
                if not isinstance(parsed_data, dict):
                    logger.error("Ожидался JSON-объект, получен: %s", type(parsed_data))
                    return ApplyResult(
                        result=current_step.expression,
                        is_valid=False,
                        explanation="Неверный формат ответа",
                        errors=["invalid_response_format"]
                    )
                result_data = cast(Dict[str, Any], parsed_data)
            except Exception as e:
                logger.error("Ошибка парсинга JSON: %s", str(e))
                logger.error("Проблемный JSON: %s", json_content)
                logger.error("Полный ответ GPT: %s", content)
                return ApplyResult(
                    result=current_step.expression,
                    is_valid=False,
                    explanation="Ошибка парсинга JSON ответа",
                    errors=["json_parse_error"]
                )
            
            # Проверяем обязательные поля
            required_fields = ["result", "is_valid"]
            missing_fields = [field for field in required_fields if field not in result_data]
            if missing_fields:
                logger.warning("Отсутствуют поля в ответе: %s", missing_fields)
                return ApplyResult(
                    result=current_step.expression,
                    is_valid=False,
                    explanation="Неполный ответ от GPT",
                    errors=["incomplete_response"]
                )
            
            # Создаём результат
            result = ApplyResult(
                result=result_data["result"],
                is_valid=result_data["is_valid"],
                explanation=result_data.get("explanation", ""),
                errors=result_data.get("errors", [])
            )
            
            logger.info("Применение преобразования завершено. Результат: %s", result.result)
            return result
            
        except Exception as e:
            logger.error("Ошибка при применении преобразования: %s", str(e), exc_info=True)
            return ApplyResult(
                result=current_step.expression,
                is_valid=False,
                explanation=f"Внутренняя ошибка: {str(e)}",
                errors=["internal_error"]
            )

    def _substitute_parameters_in_text(self, text: str, parameters: List[TransformationParameter]) -> str:
        """
        Заменяет плейсхолдеры параметров в тексте на их значения.
        
        Args:
            text: Текст с плейсхолдерами вида {param_name}
            parameters: Список параметров с их значениями
            
        Returns:
            Текст с заменёнными плейсхолдерами
        """
        result = text
        for param in parameters:
            placeholder = f"{{{param.name}}}"
            result = result.replace(placeholder, str(param.value))
        return result

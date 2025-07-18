# solution_checker.py

import logging
from typing import Any, Dict

from ..gpt_client import GPTClient
from ..parsers import safe_json_parse
from ..prompts import PromptManager
from ..types import (
    CheckResult,
    SolutionStep,
)

# Настройка логирования
logger = logging.getLogger(__name__)


class SolutionChecker:
    """
    Компонент для проверки завершённости решения.
    Отвечает за определение, решена ли задача полностью.
    """

    def __init__(self, client: GPTClient, prompt_manager: PromptManager) -> None:
        self.client = client
        self.prompt_manager = prompt_manager

        # Загружаем разделенный промпт для проверки
        self.system_prompt, self.user_prompt = self.prompt_manager.load_split_prompt("check")
        logger.debug("SolutionChecker инициализирован")

    def check_solution_completeness(
        self, current_step: SolutionStep, original_task: str
    ) -> CheckResult:
        """
        Проверяет, завершено ли решение задачи.
        """
        try:
            logger.info(
                "Проверка завершённости решения для выражения: %s",
                current_step.expression,
            )

            # Форматируем разделенный промпт
            formatted_system, formatted_user = self.prompt_manager.format_split_prompt(
                self.system_prompt,
                self.user_prompt,
                original_task=original_task,
                current_state=current_step.expression,
            )
            logger.info("System промпт для GPT:\n%s", formatted_system)
            logger.info("User промпт для GPT:\n%s", formatted_user)

            logger.debug("Отправка запроса к GPT для проверки завершённости")
            # Запрос к GPT
            response = self.client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": formatted_system,
                    },
                    {"role": "user", "content": formatted_user},
                ],
                temperature=0.3,
            )

            # Логируем токены
            usage = response.usage
            logger.info(
                "Использование токенов: промпт=%d, ответ=%d, всего=%d",
                usage.prompt_tokens,
                usage.completion_tokens,
                usage.total_tokens,
            )

            # Парсим ответ
            content = response.content.strip()
            logger.debug("Получен ответ от GPT: %s", content)

            # Проверяем, что ответ не пустой
            if not content:
                logger.error("Получен пустой ответ от GPT")
                return CheckResult(
                    is_solved=False,
                    confidence=0.0,
                    explanation="Получен пустой ответ от GPT",
                    solution_type="unknown",
                )

            # Пытаемся найти JSON в ответе (на случай, если GPT добавил лишний текст)
            json_start = content.find("{")
            json_end = content.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                logger.error(
                    "Не найден JSON-объект в ответе GPT. Полный ответ: %s", content
                )
                return CheckResult(
                    is_solved=False,
                    confidence=0.0,
                    explanation="Не найден JSON в ответе GPT",
                    solution_type="unknown",
                )

            json_content = content[json_start:json_end]
            logger.debug("Извлеченный JSON: %s", json_content)

            result_data = self._parse_json_check_result(json_content)
            if not result_data:
                return CheckResult(
                    is_solved=False,
                    confidence=0.0,
                    explanation="Ошибка парсинга JSON ответа",
                    solution_type="unknown",
                )

            # Проверяем обязательные поля
            required_fields = [
                "is_solved",
                "confidence",
                "explanation",
                "solution_type",
            ]
            missing_fields = [
                field for field in required_fields if field not in result_data
            ]
            if missing_fields:
                logger.warning("Отсутствуют поля в ответе: %s", missing_fields)
                return CheckResult(
                    is_solved=False,
                    confidence=0.0,
                    explanation="Неполный ответ от GPT",
                    solution_type="unknown",
                )

            # Создаём результат
            result = CheckResult(
                is_solved=result_data["is_solved"],
                confidence=result_data["confidence"],
                explanation=result_data["explanation"],
                solution_type=result_data["solution_type"],
                next_steps=result_data.get("next_steps", []),
            )

            logger.info(
                "Проверка завершена. Решено: %s, уверенность: %.2f, тип: %s",
                result.is_solved,
                result.confidence,
                result.solution_type,
            )
            return result

        except Exception as e:
            logger.error("Ошибка при проверке завершённости: %s", str(e), exc_info=True)
            return CheckResult(
                is_solved=False,
                confidence=0.0,
                explanation=f"Внутренняя ошибка: {str(e)}",
                solution_type="unknown",
            )

    def _parse_json_check_result(self, json_content: str) -> Dict[str, Any]:
        """
        Безопасно парсит JSON-объект результата проверки. Возвращает dict или пустой dict.
        """
        try:
            parsed_data = safe_json_parse(json_content)
            if isinstance(parsed_data, dict):
                return parsed_data
            logger.error("Ожидался JSON-объект, получен: %s", type(parsed_data))
            return {}
        except Exception as e:
            logger.error("Ошибка парсинга JSON: %s", str(e))
            logger.error("Проблемный JSON: %s", json_content)
            return {}

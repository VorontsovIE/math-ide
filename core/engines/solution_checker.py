# solution_checker.py

import logging

from ..types import SolutionStep, CheckResult
from ..parsers import safe_json_parse
from ..prompts import PromptManager
from ..gpt_client import GPTClient

# Настройка логирования
logger = logging.getLogger(__name__)


class SolutionChecker:
    """
    Компонент для проверки завершённости решения.
    Определяет, достигнута ли цель задачи.
    """

    def __init__(self, client: GPTClient, prompt_manager: PromptManager):
        self.client = client
        self.prompt_manager = prompt_manager
        
        # Загружаем промпт для проверки
        self.check_prompt = self.prompt_manager.load_prompt("check.md")
        logger.debug("SolutionChecker инициализирован")

    def check_solution_completeness(self, current_step: SolutionStep, original_task: str) -> CheckResult:
        """
        Проверяет, завершено ли решение задачи.
        """
        try:
            logger.info("Проверка завершённости решения для: %s", current_step.expression)
            
            # Форматируем промпт
            formatted_prompt = self.prompt_manager.format_prompt(
                self.check_prompt,
                original_task=original_task,
                current_state=current_step.expression
            )
            
            logger.debug("Отправка запроса к GPT для проверки завершённости")
            # Запрос к GPT
            gpt_response = self.client.chat_completion(
                messages=[
                    {"role": "system", "content": "Ты - эксперт по математике. Отвечай только в JSON-формате."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.2
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
                return CheckResult(
                    is_solved=False,
                    solution_type="unknown",
                    explanation="Не удалось проверить решение",
                    confidence=0.0
                )
            
            # Пытаемся найти JSON в ответе
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("Не найден JSON-объект в ответе GPT. Полный ответ: %s", content)
                return CheckResult(
                    is_solved=False,
                    solution_type="unknown",
                    explanation="Не удалось распарсить ответ GPT",
                    confidence=0.0
                )
            
            json_content = content[json_start:json_end]
            logger.debug("Извлеченный JSON: %s", json_content)
            
            try:
                result_data = safe_json_parse(json_content)
            except Exception as e:
                logger.error("Ошибка парсинга JSON: %s", str(e))
                return CheckResult(
                    is_solved=False,
                    solution_type="unknown",
                    explanation="Ошибка парсинга ответа",
                    confidence=0.0
                )
            
            # Проверяем обязательные поля
            if not isinstance(result_data, dict):
                logger.error("Ожидался JSON-объект, получен: %s", type(result_data))
                return CheckResult(
                    is_solved=False,
                    solution_type="unknown",
                    explanation="Неверный формат ответа",
                    confidence=0.0
                )
            
            # Создаём результат
            result = CheckResult(
                is_solved=result_data.get("is_solved", False),
                solution_type=result_data.get("solution_type", "unknown"),
                explanation=result_data.get("explanation", ""),
                confidence=result_data.get("confidence", 0.0),
                next_steps=result_data.get("next_steps", [])
            )
            
            logger.info("Проверка завершена. Результат: решено=%s, тип=%s", 
                       result.is_solved, result.solution_type)
            return result
            
        except Exception as e:
            logger.error("Ошибка при проверке завершённости: %s", str(e), exc_info=True)
            return CheckResult(
                is_solved=False,
                solution_type="unknown",
                explanation=f"Внутренняя ошибка: {str(e)}",
                confidence=0.0
            )

# branching_analyzer.py

import logging
from typing import Dict, Any, cast

from ..types import (
    SolutionStep,
    SolutionType,
    SolutionBranch,
)
from ..parsers import safe_json_parse
from ..prompts import PromptManager
from ..gpt_client import GPTClient

# Настройка логирования
logger = logging.getLogger(__name__)


class BranchingAnalyzer:
    """
    Компонент для анализа ветвящихся решений.
    Отвечает за определение, требует ли решение разветвления на несколько случаев.
    """

    def __init__(self, client: GPTClient, prompt_manager: PromptManager) -> None:
        self.client = client
        self.prompt_manager = prompt_manager
        
        # Загружаем промпт для анализа ветвления
        self.branching_prompt = self.prompt_manager.load_prompt("branching.md")
        logger.debug("BranchingAnalyzer инициализирован")

    def analyze_branching_solution(self, step: SolutionStep) -> SolutionStep:
        """
        Анализирует, требует ли решение ветвления.
        """
        try:
            logger.info(
                "Анализ ветвления для выражения: %s",
                step.expression
            )
            
            # Форматируем промпт
            formatted_prompt = self.prompt_manager.format_prompt(
                self.branching_prompt,
                current_state=step.expression
            )
            
            logger.debug("Отправка запроса к GPT для анализа ветвления")
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
                return step  # Возвращаем исходный шаг без изменений
            
            # Пытаемся найти JSON в ответе (на случай, если GPT добавил лишний текст)
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("Не найден JSON-объект в ответе GPT. Полный ответ: %s", content)
                return step  # Возвращаем исходный шаг без изменений
            
            json_content = content[json_start:json_end]
            logger.debug("Извлеченный JSON: %s", json_content)
            
            try:
                # Используем безопасный парсинг JSON с автоматическим исправлением
                parsed_data = safe_json_parse(json_content)
                # Проверяем, что это словарь
                if not isinstance(parsed_data, dict):
                    logger.error("Ожидался JSON-объект, получен: %s", type(parsed_data))
                    return step  # Возвращаем исходный шаг без изменений
                result_data = cast(Dict[str, Any], parsed_data)
            except Exception as e:
                logger.error("Ошибка парсинга JSON: %s", str(e))
                logger.error("Проблемный JSON: %s", json_content)
                logger.error("Полный ответ GPT: %s", content)
                return step  # Возвращаем исходный шаг без изменений
            
            # Проверяем, требуется ли ветвление
            requires_branching = result_data.get("requires_branching", False)
            if not requires_branching:
                logger.info("Ветвление не требуется")
                return step  # Возвращаем исходный шаг без изменений
            
            # Получаем тип решения и ветви
            solution_type_str = result_data.get("solution_type", "single")
            branches_data = result_data.get("branches", [])
            
            try:
                solution_type = SolutionType(solution_type_str)
            except ValueError:
                logger.warning("Неизвестный тип решения: %s, используем SINGLE", solution_type_str)
                solution_type = SolutionType.SINGLE
            
            # Создаём ветви
            branches = []
            for i, branch_data in enumerate(branches_data):
                try:
                    if not isinstance(branch_data, dict):
                        logger.warning("Пропускаем ветвь %d: не является словарем", i)
                        continue
                    
                    branch = SolutionBranch(
                        id=f"branch_{i}",
                        name=branch_data.get("name", f"Ветвь {i+1}"),
                        expression=branch_data.get("expression", ""),
                        condition=branch_data.get("condition"),
                        is_valid=branch_data.get("is_valid", True)
                    )
                    branches.append(branch)
                except Exception as e:
                    logger.warning("Ошибка при обработке ветви %d: %s", i, str(e))
                    continue
            
            # Создаём новый шаг с ветвлением
            if branches:
                updated_step = SolutionStep(
                    expression=step.expression,
                    solution_type=solution_type,
                    branches=branches,
                    metadata=step.metadata
                )
                logger.info("Создано ветвящееся решение с %d ветвями", len(branches))
                return updated_step
            else:
                logger.warning("Ветвление требуется, но ветви не найдены")
                return step  # Возвращаем исходный шаг без изменений
            
        except Exception as e:
            logger.error("Ошибка при анализе ветвления: %s", str(e), exc_info=True)
            return step  # Возвращаем исходный шаг без изменений

# branching_analyzer.py

import logging

from ..types import SolutionStep
from ..parsers import safe_json_parse
from ..prompts import PromptManager
from ..gpt_client import GPTClient

logger = logging.getLogger(__name__)


class BranchingAnalyzer:
    """
    Компонент для анализа ветвящихся решений.
    Определяет, когда решение должно разветвляться на несколько путей.
    """

    def __init__(self, client: GPTClient, prompt_manager: PromptManager):
        self.client = client
        self.prompt_manager = prompt_manager
        self.branching_prompt = self.prompt_manager.load_prompt("branching.md")
        logger.debug("BranchingAnalyzer инициализирован")

    def analyze_branching_solution(self, step: SolutionStep) -> SolutionStep:
        """
        Анализирует, требует ли решение ветвления, и создаёт соответствующую структуру.
        """
        try:
            logger.info("Анализ ветвления для: %s", step.expression)
            
            formatted_prompt = self.prompt_manager.format_prompt(
                self.branching_prompt,
                current_expression=step.expression,
                current_solution_type=step.solution_type.value if step.solution_type else "single"
            )
            
            gpt_response = self.client.chat_completion(
                messages=[
                    {"role": "system", "content": "Ты - эксперт по математике. Отвечай только в JSON-формате."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.3
            )
            
            content = gpt_response.content
            if not content:
                logger.warning("Пустой ответ от GPT для анализа ветвления")
                return step
            
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.warning("Не найден JSON в ответе анализа ветвления")
                return step
            
            json_content = content[json_start:json_end]
            result_data = safe_json_parse(json_content)
            
            if not isinstance(result_data, dict):
                logger.warning("Неверный формат ответа анализа ветвления")
                return step
            
            # Если ветвление не требуется, возвращаем оригинальный шаг
            if not result_data.get("requires_branching", False):
                logger.info("Ветвление не требуется")
                return step
            
            # Создаём ветвящийся шаг на основе анализа GPT
            from ..types import SolutionType, SolutionBranch
            
            solution_type_str = result_data.get("solution_type", "alternatives")
            solution_type = getattr(SolutionType, solution_type_str.upper(), SolutionType.ALTERNATIVES)
            
            branches = []
            branches_data = result_data.get("branches", [])
            
            for i, branch_data in enumerate(branches_data):
                branch = SolutionBranch(
                    id=f"branch_{i}",
                    name=branch_data.get("name", f"Ветвь {i+1}"),
                    expression=branch_data.get("expression", ""),
                    condition=branch_data.get("condition"),
                    is_valid=branch_data.get("is_valid", True)
                )
                branches.append(branch)
            
            # Создаём новый шаг с ветвлением
            branching_step = SolutionStep(
                expression=result_data.get("description", step.expression),
                solution_type=solution_type,
                branches=branches,
                metadata={
                    **step.metadata,
                    "original_expression": step.expression,
                    "branching_reason": result_data.get("explanation", ""),
                    "branching_analysis": result_data
                }
            )
            
            logger.info("Создано ветвящееся решение с %d ветвями", len(branches))
            return branching_step
            
        except Exception as e:
            logger.error("Ошибка анализа ветвления: %s", str(e), exc_info=True)
            return step

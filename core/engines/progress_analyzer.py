# progress_analyzer.py

import logging
from typing import Any, Dict, List

from ..gpt_client import GPTClient
from ..parsers import safe_json_parse
from ..prompts import PromptManager
from ..types import ProgressAnalysisResult

logger = logging.getLogger(__name__)


class ProgressAnalyzer:
    """
    Компонент для анализа прогресса решения.
    Оценивает качество продвижения к цели.
    """

    def __init__(self, client: GPTClient, prompt_manager: PromptManager):
        self.client = client
        self.prompt_manager = prompt_manager
        # Загружаем разделенный промпт для анализа прогресса
        self.system_prompt, self.user_prompt = self.prompt_manager.load_split_prompt("progress_analysis")
        logger.debug("ProgressAnalyzer инициализирован")

    def analyze_progress(
        self,
        original_task: str,
        history_steps: List[Dict[str, Any]],
        current_step: str,
        steps_count: int,
    ) -> ProgressAnalysisResult:
        """
        Анализирует прогресс решения задачи и даёт рекомендации.
        """
        try:
            logger.info("Анализ прогресса решения")

            # Форматируем разделенный промпт
            formatted_system, formatted_user = self.prompt_manager.format_split_prompt(
                self.system_prompt,
                self.user_prompt,
                original_task=original_task,
                history_steps=str(history_steps),
                current_step=current_step,
                steps_count=steps_count,
            )
            logger.info("System промпт для GPT:\n%s", formatted_system)
            logger.info("User промпт для GPT:\n%s", formatted_user)

            gpt_response = self.client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": formatted_system,
                    },
                    {"role": "user", "content": formatted_user},
                ],
                temperature=0.3,
            )

            content = gpt_response.content
            logger.info("=== ОТВЕТ МОДЕЛИ (АНАЛИЗ ПРОГРЕССА) ===")
            logger.info("Содержимое ответа GPT:")
            logger.info(content)
            logger.info("=== КОНЕЦ ОТВЕТА ===")
            if not content:
                return ProgressAnalysisResult(
                    progress_assessment="unknown",
                    confidence=0.0,
                    analysis="Не удалось проанализировать прогресс",
                    recommend_rollback=False,
                )

            json_start = content.find("{")
            json_end = content.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                return ProgressAnalysisResult(
                    progress_assessment="unknown",
                    confidence=0.0,
                    analysis="Ошибка анализа",
                    recommend_rollback=False,
                )

            json_content = content[json_start:json_end]
            result_data = safe_json_parse(json_content)

            return ProgressAnalysisResult(
                progress_assessment=result_data.get("progress_assessment", "unknown"),
                confidence=result_data.get("confidence", 0.0),
                analysis=result_data.get("analysis", ""),
                recommend_rollback=result_data.get("recommend_rollback", False),
                recommended_step=result_data.get("recommended_step"),
                rollback_reason=result_data.get("rollback_reason"),
                suggestion_message=result_data.get("suggestion_message"),
            )

        except Exception as e:
            logger.error("Ошибка анализа прогресса: %s", str(e), exc_info=True)
            return ProgressAnalysisResult(
                progress_assessment="error",
                confidence=0.0,
                analysis=f"Ошибка: {str(e)}",
                recommend_rollback=False,
            )

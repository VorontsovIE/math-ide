# transformation_verifier.py

import logging
from typing import Optional

from ..gpt_client import GPTClient
from ..parsers import safe_json_parse
from ..prompts import PromptManager
from ..types import VerificationResult

logger = logging.getLogger(__name__)


class TransformationVerifier:
    """
    Компонент для верификации математических преобразований.
    Проверяет корректность выполненных преобразований.
    """

    def __init__(self, client: GPTClient, prompt_manager: PromptManager):
        self.client = client
        self.prompt_manager = prompt_manager
        self.verification_prompt = self.prompt_manager.load_prompt("verification.md")
        logger.debug("TransformationVerifier инициализирован")

    def verify_transformation(
        self,
        original_expression: str,
        transformation_description: str,
        current_result: str,
        verification_type: str,
        user_suggested_result: Optional[str] = None,
    ) -> VerificationResult:
        """
        Проверяет корректность математического преобразования.
        """
        try:
            logger.info(
                "Верификация преобразования: %s -> %s",
                original_expression,
                current_result,
            )

            formatted_prompt = self.prompt_manager.format_prompt(
                self.verification_prompt,
                original_expression=original_expression,
                transformation_description=transformation_description,
                current_result=current_result,
                verification_type=verification_type,
                user_suggested_result=user_suggested_result or "",
            )
            logger.info("Промпт для GPT (с подставленными переменными):\n%s", formatted_prompt)

            gpt_response = self.client.chat_completion(
                messages=[
                    {
                        "role": "system",
                        "content": "Ты - эксперт по математике. Отвечай только в JSON-формате.",
                    },
                    {"role": "user", "content": formatted_prompt},
                ],
                temperature=0.1,
            )

            content = gpt_response.content
            if not content:
                return VerificationResult(
                    is_correct=False,
                    corrected_result=current_result,
                    verification_explanation="Не удалось выполнить верификацию",
                )

            json_start = content.find("{")
            json_end = content.rfind("}") + 1

            if json_start == -1 or json_end == 0:
                return VerificationResult(
                    is_correct=False,
                    corrected_result=current_result,
                    verification_explanation="Ошибка парсинга ответа верификации",
                )

            json_content = content[json_start:json_end]
            result_data = safe_json_parse(json_content)

            return VerificationResult(
                is_correct=result_data.get("is_correct", False),
                corrected_result=result_data.get("corrected_result", current_result),
                verification_explanation=result_data.get(
                    "verification_explanation", ""
                ),
                errors_found=result_data.get("errors_found", []),
                step_by_step_check=result_data.get("step_by_step_check", ""),
                user_result_assessment=result_data.get("user_result_assessment"),
            )

        except Exception as e:
            logger.error("Ошибка верификации: %s", str(e), exc_info=True)
            return VerificationResult(
                is_correct=False,
                corrected_result=current_result,
                verification_explanation=f"Ошибка верификации: {str(e)}",
            )

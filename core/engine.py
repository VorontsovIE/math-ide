import json
import random
import logging
import re
from typing import List, Optional, Any, Dict
from pathlib import Path
import openai
from openai import OpenAI
import io

# Импортируем типы данных из отдельного модуля
from .types import (
    BaseTransformationType,
    TransformationParameter,
    Transformation,
    SolutionStep,
    GenerationResult,
    ApplyResult,
    CheckResult,
    ProgressAnalysisResult,
    VerificationResult,
    get_transformation_types_markdown,
)

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





class TransformationEngine:
    """
    Ядро для генерации допустимых математических преобразований.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo", preview_mode: bool = False):
        self.model = model
        self.client = OpenAI(api_key=api_key)
        self.prompt_manager = PromptManager()
        self.preview_mode = preview_mode
        
        logger.info(f"Инициализация TransformationEngine с моделью {model}")
        
        # Загружаем промпты
        logger.debug("Загрузка промптов...")
        self.generation_prompt = self.prompt_manager.load_prompt("generation.md")
        self.apply_prompt = self.prompt_manager.load_prompt("apply.md")
        self.check_prompt = self.prompt_manager.load_prompt("check.md")
        self.progress_analysis_prompt = self.prompt_manager.load_prompt("progress_analysis.md")
        self.verification_prompt = self.prompt_manager.load_prompt("verification.md")
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
                # Используем безопасный парсинг JSON с автоматическим исправлением
                transformations_data = safe_json_parse(json_content)
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
                # Используем безопасный парсинг JSON с автоматическим исправлением
                result_data = safe_json_parse(json_content)
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
                errors=result_data.get("errors", []),
                mathematical_verification=result_data.get("mathematical_verification")
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
                # Используем безопасный парсинг JSON с автоматическим исправлением
                check_data = safe_json_parse(json_content)
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
                next_steps=check_data.get("next_steps", []),
                mathematical_verification=check_data.get("mathematical_verification")
            )
            
        except Exception as e:
            logger.error("Ошибка при проверке завершённости: %s", str(e), exc_info=True)
            return CheckResult(
                is_solved=False,
                confidence=0.0,
                explanation=f"Ошибка при проверке завершённости: {str(e)}",
                solution_type="error"
            )

    def analyze_progress(self, original_task: str, history_steps: List[Dict[str, Any]], 
                        current_step: str, steps_count: int) -> ProgressAnalysisResult:
        """
        Анализирует прогресс решения задачи и определяет, стоит ли рекомендовать откат.
        
        Args:
            original_task: Исходная задача
            history_steps: История шагов решения 
            current_step: Текущее состояние
            steps_count: Количество шагов
            
        Returns:
            ProgressAnalysisResult с рекомендациями
        """
        try:
            logger.info("Анализ прогресса решения для задачи: %s", original_task)
            
            # Форматируем историю шагов в читаемый вид
            history_text = ""
            for i, step in enumerate(history_steps):
                history_text += f"- Шаг {i}: \"{step.get('expression', '')}\""
                if step.get('chosen_transformation'):
                    history_text += f" ({step['chosen_transformation'].get('description', '')})"
                history_text += "\n"
            
            # Форматируем промпт
            formatted_prompt = self.prompt_manager.format_prompt(
                self.progress_analysis_prompt,
                original_task=original_task,
                history_steps=history_text,
                current_step=current_step,
                steps_count=steps_count
            )
            
            logger.debug("Отправка запроса к GPT для анализа прогресса")
            # Запрос к GPT
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты - эксперт по математике. Отвечай только в JSON-формате."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.3,
                max_tokens=800
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
                return ProgressAnalysisResult(
                    progress_assessment="neutral",
                    confidence=0.0,
                    analysis="Не удалось получить анализ прогресса",
                    recommend_rollback=False
                )
            
            # Пытаемся найти JSON в ответе
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("Не найден JSON-объект в ответе GPT. Полный ответ: %s", content)
                return ProgressAnalysisResult(
                    progress_assessment="neutral",
                    confidence=0.0,
                    analysis="Ошибка парсинга ответа GPT",
                    recommend_rollback=False
                )
            
            json_content = content[json_start:json_end]
            logger.debug("Извлеченный JSON: %s", json_content)
            
            try:
                # Используем безопасный парсинг JSON
                analysis_data = safe_json_parse(json_content)
            except json.JSONDecodeError as e:
                logger.error("Ошибка парсинга JSON: %s", str(e))
                logger.error("Проблемный JSON: %s", json_content)
                return ProgressAnalysisResult(
                    progress_assessment="neutral",
                    confidence=0.0,
                    analysis=f"Ошибка парсинга JSON: {str(e)}",
                    recommend_rollback=False
                )
            
            # Проверяем обязательные поля
            required_fields = ["progress_assessment", "confidence", "analysis", "recommend_rollback"]
            missing_fields = [field for field in required_fields if field not in analysis_data]
            if missing_fields:
                logger.error("Отсутствуют обязательные поля в ответе: %s", missing_fields)
                return ProgressAnalysisResult(
                    progress_assessment="neutral",
                    confidence=0.0,
                    analysis=f"Отсутствуют обязательные поля: {missing_fields}",
                    recommend_rollback=False
                )
            
            logger.info(
                "Результат анализа прогресса: оценка=%s, рекомендация отката=%s",
                analysis_data["progress_assessment"],
                analysis_data["recommend_rollback"]
            )
            
            return ProgressAnalysisResult(
                progress_assessment=analysis_data["progress_assessment"],
                confidence=analysis_data["confidence"],
                analysis=analysis_data["analysis"],
                recommend_rollback=analysis_data["recommend_rollback"],
                recommended_step=analysis_data.get("recommended_step"),
                rollback_reason=analysis_data.get("rollback_reason"),
                suggestion_message=analysis_data.get("suggestion_message")
            )
            
        except Exception as e:
            logger.error("Ошибка при анализе прогресса: %s", str(e), exc_info=True)
            return ProgressAnalysisResult(
                progress_assessment="neutral",
                confidence=0.0,
                analysis=f"Ошибка при анализе прогресса: {str(e)}",
                recommend_rollback=False
            )

    def verify_transformation(self, original_expression: str, transformation_description: str,
                             current_result: str, verification_type: str,
                             user_suggested_result: Optional[str] = None) -> VerificationResult:
        """
        Проверяет корректность математического преобразования и при необходимости исправляет ошибки.
        
        Args:
            original_expression: Исходное выражение
            transformation_description: Описание применённого преобразования
            current_result: Полученный результат
            verification_type: Тип проверки (recalculate, verify_user_suggestion, verify_user_transformation)
            user_suggested_result: Предложенный пользователем результат (опционально)
            
        Returns:
            VerificationResult с результатом проверки
        """
        try:
            logger.info("Проверка преобразования: %s -> %s", original_expression, current_result)
            
            # Форматируем промпт
            formatted_prompt = self.prompt_manager.format_prompt(
                self.verification_prompt,
                original_expression=original_expression,
                transformation_description=transformation_description,
                current_result=current_result,
                verification_type=verification_type,
                user_suggested_result=user_suggested_result or ""
            )
            
            logger.debug("Отправка запроса к GPT для проверки преобразования")
            # Запрос к GPT
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Ты - эксперт по математике. Отвечай только в JSON-формате."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=0.1,  # Низкая температура для точности
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
                return VerificationResult(
                    is_correct=False,
                    corrected_result=current_result,
                    verification_explanation="Не удалось получить результат проверки",
                    errors_found=["Ошибка при обращении к GPT"]
                )
            
            # Пытаемся найти JSON в ответе
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                logger.error("Не найден JSON-объект в ответе GPT. Полный ответ: %s", content)
                return VerificationResult(
                    is_correct=False,
                    corrected_result=current_result,
                    verification_explanation="Ошибка парсинга ответа GPT",
                    errors_found=["Некорректный формат ответа"]
                )
            
            json_content = content[json_start:json_end]
            logger.debug("Извлеченный JSON: %s", json_content)
            
            try:
                # Используем безопасный парсинг JSON
                verification_data = safe_json_parse(json_content)
            except json.JSONDecodeError as e:
                logger.error("Ошибка парсинга JSON: %s", str(e))
                logger.error("Проблемный JSON: %s", json_content)
                return VerificationResult(
                    is_correct=False,
                    corrected_result=current_result,
                    verification_explanation=f"Ошибка парсинга JSON: {str(e)}",
                    errors_found=["Ошибка парсинга ответа"]
                )
            
            # Проверяем обязательные поля
            required_fields = ["is_correct", "corrected_result", "verification_explanation"]
            missing_fields = [field for field in required_fields if field not in verification_data]
            if missing_fields:
                logger.error("Отсутствуют обязательные поля в ответе: %s", missing_fields)
                return VerificationResult(
                    is_correct=False,
                    corrected_result=current_result,
                    verification_explanation=f"Отсутствуют обязательные поля: {missing_fields}",
                    errors_found=["Неполный ответ от GPT"]
                )
            
            logger.info(
                "Результат проверки: корректно=%s, исправленный результат=%s",
                verification_data["is_correct"],
                verification_data["corrected_result"]
            )
            
            return VerificationResult(
                is_correct=verification_data["is_correct"],
                corrected_result=verification_data["corrected_result"],
                verification_explanation=verification_data["verification_explanation"],
                errors_found=verification_data.get("errors_found", []),
                step_by_step_check=verification_data.get("step_by_step_check", ""),
                user_result_assessment=verification_data.get("user_result_assessment")
            )
            
        except Exception as e:
            logger.error("Ошибка при проверке преобразования: %s", str(e), exc_info=True)
            return VerificationResult(
                is_correct=False,
                corrected_result=current_result,
                verification_explanation=f"Ошибка при проверке преобразования: {str(e)}",
                errors_found=[f"Системная ошибка: {str(e)}"]
            )


def fix_latex_escapes_in_json(json_content: str) -> str:
    """
    Исправляет экранирование обратных слэшей в LaTeX-выражениях в JSON.
    
    Проблема: GPT возвращает \sin, \cos и т.д., но в JSON это должно быть \\sin, \\cos
    """
    # Список известных LaTeX-команд
    latex_commands = [
        'sin', 'cos', 'tan', 'cot', 'sec', 'csc',
        'arcsin', 'arccos', 'arctan', 'arccot', 'arcsec', 'arccsc',
        'sinh', 'cosh', 'tanh', 'coth', 'sech', 'csch',
        'log', 'ln', 'exp', 'lim', 'inf', 'infty',
        'alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta', 'eta', 'theta',
        'iota', 'kappa', 'lambda', 'mu', 'nu', 'xi', 'pi', 'rho', 'sigma',
        'tau', 'upsilon', 'phi', 'chi', 'psi', 'omega',
        'Alpha', 'Beta', 'Gamma', 'Delta', 'Epsilon', 'Zeta', 'Eta', 'Theta',
        'Iota', 'Kappa', 'Lambda', 'Mu', 'Nu', 'Xi', 'Pi', 'Rho', 'Sigma',
        'Tau', 'Upsilon', 'Phi', 'Chi', 'Psi', 'Omega',
        'partial', 'nabla', 'forall', 'exists', 'nexists', 'emptyset',
        'in', 'notin', 'subset', 'supset', 'subseteq', 'supseteq',
        'cup', 'cap', 'bigcup', 'bigcap', 'oplus', 'otimes',
        'leq', 'geq', 'neq', 'approx', 'equiv', 'propto',
        'rightarrow', 'leftarrow', 'leftrightarrow', 'Rightarrow', 'Leftarrow', 'Leftrightarrow',
        'sum', 'prod', 'int', 'oint', 'iint', 'iiint',
        'sqrt', 'cbrt', 'frac', 'over', 'binom', 'choose',
        'text', 'mathrm', 'mathbf', 'mathit', 'mathcal', 'mathfrak',
        'overline', 'underline', 'widehat', 'widetilde', 'vec', 'dot', 'ddot',
        'prime', 'doubleprime', 'dagger', 'ddagger', 'bullet', 'circ',
        'pm', 'mp', 'times', 'div', 'cdot', 'ast',
        'star', 'diamond', 'triangle', 'square', 'circle', 'ellipse'
    ]
    
    def fix_latex_in_string(content: str) -> str:
        """Исправляет LaTeX-команды в строке"""
        # Сначала обрабатываем уже экранированные команды (\\\\command)
        # Заменяем их на временные маркеры
        temp_markers = {}
        marker_counter = 0
        
        def create_marker():
            nonlocal marker_counter
            marker = f"__TEMP_MARKER_{marker_counter}__"
            marker_counter += 1
            return marker
        
        # Сохраняем уже правильно экранированные команды
        for cmd in latex_commands:
            pattern = rf'\\\\{cmd}'
            if pattern in content:
                marker = create_marker()
                temp_markers[marker] = f'\\\\{cmd}'
                content = content.replace(pattern, marker)
        
        # Теперь обрабатываем неправильно экранированные команды
        for cmd in latex_commands:
            # Ищем \command (не экранированный)
            pattern = rf'(?<!\\)\\{cmd}(?![a-zA-Z])'
            content = re.sub(pattern, rf'\\\\{cmd}', content)
        
        # Восстанавливаем сохраненные команды
        for marker, replacement in temp_markers.items():
            content = content.replace(marker, replacement)
        
        return content
    
    # Обрабатываем JSON по частям, чтобы не затронуть структуру
    result = ""
    in_string = False
    string_start = 0
    i = 0
    
    while i < len(json_content):
        char = json_content[i]
        
        if char == '"' and (i == 0 or json_content[i-1] != '\\'):
            if not in_string:
                # Начало строки
                in_string = True
                string_start = i
            else:
                # Конец строки
                in_string = False
                string_content = json_content[string_start+1:i]
                fixed_string = fix_latex_in_string(string_content)
                result += f'"{fixed_string}"'
        
        elif not in_string:
            result += char
        
        i += 1
    
    # Добавляем оставшиеся символы, если мы не в строке
    if not in_string and i < len(json_content):
        result += json_content[i:]
    
    return result


def safe_json_parse(json_content: str, fallback_attempts: int = 3) -> dict:
    """
    Безопасно парсит JSON с несколькими попытками исправления.
    
    Args:
        json_content: JSON строка для парсинга
        fallback_attempts: Количество попыток исправления
    
    Returns:
        Распарсенный JSON как словарь
        
    Raises:
        json.JSONDecodeError: Если не удалось распарсить JSON после всех попыток
    """
    attempts = []
    
    # Попытка 1: Прямой парсинг
    try:
        return json.loads(json_content)
    except json.JSONDecodeError as e:
        attempts.append(f"Прямой парсинг: {str(e)}")
    
    # Попытка 2: Исправление LaTeX-экранирования
    try:
        fixed_content = fix_latex_escapes_in_json(json_content)
        return json.loads(fixed_content)
    except json.JSONDecodeError as e:
        attempts.append(f"После исправления LaTeX: {str(e)}")
    
    # Попытка 3: Агрессивное исправление обратных слэшей
    try:
        # Заменяем все одиночные обратные слэши на двойные (кроме уже экранированных)
        aggressive_fixed = re.sub(r'(?<!\\)\\(?!\\)', r'\\\\', json_content)
        return json.loads(aggressive_fixed)
    except json.JSONDecodeError as e:
        attempts.append(f"Агрессивное исправление: {str(e)}")
    
    # Попытка 4: Удаление проблемных символов
    try:
        # Удаляем все обратные слэши, которые не являются частью экранированных последовательностей
        cleaned_content = re.sub(r'(?<!\\)\\(?!["\\/bfnrt])', '', json_content)
        return json.loads(cleaned_content)
    except json.JSONDecodeError as e:
        attempts.append(f"Очистка слэшей: {str(e)}")
    
    # Если все попытки не удались, логируем все ошибки и выбрасываем исключение
    error_msg = f"Не удалось распарсить JSON после {len(attempts)} попыток:\n"
    for i, attempt in enumerate(attempts, 1):
        error_msg += f"{i}. {attempt}\n"
    error_msg += f"Исходный JSON: {json_content}"
    
    raise json.JSONDecodeError(error_msg, json_content, 0)


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
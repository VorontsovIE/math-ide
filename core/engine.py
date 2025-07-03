# New refactored engine

import logging
from typing import Any, Callable, Dict, List, Optional, Union

# Импортируем новые компоненты
from .engines import (
    ProgressAnalyzer,
    SolutionChecker,
    TransformationGenerator,
    TransformationVerifier,
)
from .gpt_client import GPTClient
from .prompts import PromptManager

# Импортируем типы данных из отдельного модуля
from .types import (
    CheckResult,
    GenerationResult,
    ParameterDefinition,
    ProgressAnalysisResult,
    SolutionStep,
    Transformation,
    TransformationParameter,
    VerificationResult,
)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Добавляем цветной форматтер для консоли
try:
    import coloredlogs

    coloredlogs.install(
        level="INFO",
        logger=logger,
        fmt="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    )
except ImportError:
    # Если coloredlogs не установлен, используем стандартное логирование
    logger.info("coloredlogs не установлен. Используется стандартное логирование.")


class TransformationEngine:
    """
    Ядро для генерации допустимых математических преобразований.
    Координирует работу специализированных компонентов.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        preview_mode: bool = False,
    ) -> None:
        self.model = model
        self.client = GPTClient(api_key=api_key, model=model)
        self.prompt_manager = PromptManager()
        self.preview_mode = preview_mode

        logger.info(f"Инициализация TransformationEngine с моделью {model}")

        # Инициализируем компоненты
        logger.debug("Инициализация компонентов...")
        self.generator = TransformationGenerator(
            self.client, self.prompt_manager, preview_mode
        )
        self.checker = SolutionChecker(self.client, self.prompt_manager)
        self.progress_analyzer = ProgressAnalyzer(self.client, self.prompt_manager)
        self.verifier = TransformationVerifier(self.client, self.prompt_manager)

        logger.debug("Все компоненты успешно инициализированы")

    def generate_transformations(
        self, step_or_expression: Union[str, SolutionStep]
    ) -> GenerationResult:
        """
        Генерирует список возможных математических преобразований для текущего шага.
        Делегирует работу TransformationGenerator.

        Args:
            step_or_expression: SolutionStep или строка с выражением
        """
        if isinstance(step_or_expression, str):
            # Создаем временный SolutionStep для строки
            from .types import SolutionStep

            step = SolutionStep(expression=step_or_expression)
        else:
            step = step_or_expression

        return self.generator.generate_transformations(step)

    def check_solution_completeness(
        self,
        current_step_or_expression: Union[str, SolutionStep],
        original_task: str = "",
    ) -> CheckResult:
        """
        Проверяет, завершено ли решение задачи.
        Делегирует работу SolutionChecker.

        Args:
            current_step_or_expression: SolutionStep или строка с выражением
            original_task: Исходная задача
        """
        if isinstance(current_step_or_expression, str):
            # Создаем временный SolutionStep для строки
            from .types import SolutionStep

            step = SolutionStep(expression=current_step_or_expression)
            return self.checker.check_solution_completeness(
                step, original_task or current_step_or_expression
            )
        else:
            return self.checker.check_solution_completeness(
                current_step_or_expression, original_task
            )

    def analyze_progress(
        self,
        original_task: str,
        history_steps: List[Dict[str, Any]],
        current_step: str,
        steps_count: int,
    ) -> ProgressAnalysisResult:
        """
        Анализирует прогресс решения задачи и даёт рекомендации.
        Делегирует работу ProgressAnalyzer.
        """
        return self.progress_analyzer.analyze_progress(
            original_task, history_steps, current_step, steps_count
        )

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
        Делегирует работу TransformationVerifier.
        """
        return self.verifier.verify_transformation(
            original_expression,
            transformation_description,
            current_result,
            verification_type,
            user_suggested_result,
        )

    def request_parameters(
        self,
        transformation: Transformation,
        user_input_callback: Callable[[ParameterDefinition], Any],
    ) -> Transformation:
        """
        Запрашивает параметры у пользователя для параметризованного преобразования.

        Args:
            transformation: Преобразование с определениями параметров
            user_input_callback: Функция для запроса ввода у пользователя

        Returns:
            Преобразование с заполненными параметрами
        """
        if not transformation.parameter_definitions:
            return transformation

        logger.info(
            f"Запрос параметров для преобразования: {transformation.description}"
        )

        parameters = []
        for param_def in transformation.parameter_definitions:
            try:
                # Запрашиваем значение у пользователя
                user_value = user_input_callback(param_def)

                # Создаём параметр с полученным значением
                parameter = TransformationParameter(
                    name=param_def.name,
                    value=user_value,
                    param_type=param_def.param_type,
                    original_definition=param_def,
                )
                parameters.append(parameter)

                logger.debug(f"Получен параметр {param_def.name}: {user_value}")

            except Exception as e:
                logger.error(f"Ошибка при запросе параметра {param_def.name}: {str(e)}")
                # В случае ошибки используем значение по умолчанию
                if param_def.default_value is not None:
                    parameter = TransformationParameter(
                        name=param_def.name,
                        value=param_def.default_value,
                        param_type=param_def.param_type,
                        original_definition=param_def,
                    )
                    parameters.append(parameter)
                    logger.warning(
                        f"Использовано значение по умолчанию для {param_def.name}: {param_def.default_value}"
                    )

        # Создаём новое преобразование с заполненными параметрами
        updated_transformation = Transformation(
            description=transformation.description,
            expression=transformation.expression,
            parameters=parameters,
            parameter_definitions=transformation.parameter_definitions,
            metadata=transformation.metadata,
            preview_result=transformation.preview_result,
            requires_user_input=transformation.requires_user_input,
        )

        logger.info(
            f"Параметры успешно заполнены для преобразования: {updated_transformation.description}"
        )
        return updated_transformation

    def _substitute_parameters_in_text(
        self, text: str, parameters: List[TransformationParameter]
    ) -> str:
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

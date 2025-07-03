import unittest
from unittest.mock import patch

from core.engine import TransformationEngine
from core.gpt_client import GPTResponse, GPTUsage
from core.history import SolutionHistory
from core.types import (
    CheckResult,
    GenerationResult,
    ParameterDefinition,
    ParameterType,
    SolutionStep,
    Transformation,
)


class TestTransformationEngine:
    """Тесты для ядра генерации преобразований."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.engine = TransformationEngine(api_key="test_key")
        self.sample_step = SolutionStep(expression="2(x + 1) = 4")

    def test_engine_initialization(self):
        """Тест инициализации движка."""
        assert self.engine.model == "gpt-3.5-turbo"
        assert self.engine.client is not None
        assert self.engine.prompt_manager is not None
        # Проверяем что компоненты инициализированы
        assert self.engine.generator is not None
        assert self.engine.checker is not None

    @patch("core.gpt_client.GPTClient.chat_completion")
    @patch("core.prompts.PromptManager.format_prompt")
    def test_generate_transformations_success(self, mock_format, mock_chat):
        """Тест успешной генерации преобразований."""
        # Мокаем форматирование промпта
        mock_format.return_value = "Test prompt"

        # Мокаем ответ GPT
        mock_response = GPTResponse(
            content="""[
                {
                    "description": "Раскрыть скобки",
                    "expression": "2x + 2 = 4",
                    "type": "expand",
                    "metadata": {"usefulness": "good"}
                }
            ]""",
            usage=GPTUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150),
            model="gpt-3.5-turbo",
            finish_reason="stop",
        )
        mock_chat.return_value = mock_response

        result = self.engine.generate_transformations(self.sample_step)

        assert isinstance(result, GenerationResult)
        assert len(result.transformations) > 0
        assert result.transformations[0].description == "Раскрыть скобки"
        assert result.transformations[0].type == "expand"

    @patch("core.gpt_client.GPTClient.chat_completion")
    @patch("core.prompts.PromptManager.format_prompt")
    def test_generate_transformations_error(self, mock_format, mock_chat):
        """Тест обработки ошибки при генерации."""
        # Мокаем форматирование промпта
        mock_format.return_value = "Test prompt"

        # Мокаем ошибку API
        mock_chat.side_effect = Exception("API Error")

        result = self.engine.generate_transformations(self.sample_step)

        assert isinstance(result, GenerationResult)
        # При ошибке возвращается пустой список преобразований
        assert len(result.transformations) == 0

    @patch("core.gpt_client.GPTClient.chat_completion")
    @patch("core.prompts.PromptManager.format_prompt")
    def test_check_solution_completeness_solved(self, mock_format, mock_chat):
        """Тест проверки завершённости - задача решена."""
        # Мокаем форматирование промпта
        mock_format.return_value = "Test prompt"

        solved_step = SolutionStep(expression="x = 2")

        # Мокаем ответ GPT
        mock_response = GPTResponse(
            content="""{
                "is_solved": true,
                "confidence": 0.95,
                "explanation": "Переменная x выражена через число",
                "solution_type": "exact",
                "next_steps": []
            }""",
            usage=GPTUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150),
            model="gpt-3.5-turbo",
            finish_reason="stop",
        )
        mock_chat.return_value = mock_response

        result = self.engine.check_solution_completeness(
            solved_step, "Решить уравнение"
        )

        assert isinstance(result, CheckResult)
        assert result.is_solved
        assert result.confidence > 0.9
        assert result.solution_type == "exact"

    @patch("core.gpt_client.GPTClient.chat_completion")
    @patch("core.prompts.PromptManager.format_prompt")
    def test_check_solution_completeness_not_solved(self, mock_format, mock_chat):
        """Тест проверки завершённости - задача не решена."""
        # Мокаем форматирование промпта
        mock_format.return_value = "Test prompt"

        # Мокаем ответ GPT
        mock_response = GPTResponse(
            content="""{
                "is_solved": false,
                "confidence": 0.3,
                "explanation": "Уравнение упрощено, но x не выражен",
                "solution_type": "partial",
                "next_steps": ["Вычесть 2", "Разделить на 2"]
            }""",
            usage=GPTUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150),
            model="gpt-3.5-turbo",
            finish_reason="stop",
        )
        mock_chat.return_value = mock_response

        result = self.engine.check_solution_completeness(
            self.sample_step, "Решить уравнение"
        )

        assert isinstance(result, CheckResult)
        assert not result.is_solved
        assert result.confidence < 0.5
        assert result.solution_type == "partial"
        assert len(result.next_steps) > 0

    @patch("core.gpt_client.GPTClient.chat_completion")
    @patch("core.prompts.PromptManager.format_prompt")
    def test_preview_mode_enabled(self, mock_format, mock_chat):
        """Тест режима предпоказа - должен заполнять preview_result из expression."""
        # Мокаем форматирование промпта
        mock_format.return_value = "Test prompt"

        engine = TransformationEngine(api_key="test-key", preview_mode=True)
        step = SolutionStep(expression="2x + 4 = 10")

        # Мокаем ответ GPT для генерации преобразований
        mock_response = GPTResponse(
            content="""[
                {
                    "description": "Вычесть 4 из обеих частей",
                    "expression": "2x = 6",
                    "type": "subtract",
                    "metadata": {"usefullness": "good"}
                }
            ]""",
            usage=GPTUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150),
            model="gpt-3.5-turbo",
            finish_reason="stop",
        )
        mock_chat.return_value = mock_response

        result = engine.generate_transformations(step)

        # Проверяем, что результат содержит преобразования с предварительными результатами
        assert len(result.transformations) == 1
        transformation = result.transformations[0]
        assert transformation.description == "Вычесть 4 из обеих частей"
        assert transformation.expression == "2x = 6"
        assert (
            transformation.preview_result == "2x = 6"
        )  # Должен быть скопирован из expression

        # Проверяем, что был сделан только 1 вызов для генерации
        assert mock_chat.call_count == 1

    @patch("core.gpt_client.GPTClient.chat_completion")
    @patch("core.prompts.PromptManager.format_prompt")
    def test_preview_mode_disabled(self, mock_format, mock_chat):
        """Тест обычного режима - не должен генерировать предварительные результаты."""
        # Мокаем форматирование промпта
        mock_format.return_value = "Test prompt"

        engine = TransformationEngine(api_key="test-key", preview_mode=False)
        step = SolutionStep(expression="2x + 4 = 10")

        # Мокаем ответ GPT для генерации преобразований
        mock_response = GPTResponse(
            content="""[
                {
                    "description": "Вычесть 4 из обеих частей",
                    "expression": "2x = 6",
                    "type": "subtract",
                    "metadata": {"usefulness": "good"}
                }
            ]""",
            usage=GPTUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150),
            model="gpt-3.5-turbo",
            finish_reason="stop",
        )
        mock_chat.return_value = mock_response

        result = engine.generate_transformations(step)

        # Проверяем, что результат содержит преобразования без предварительных результатов
        assert len(result.transformations) == 1
        transformation = result.transformations[0]
        assert transformation.description == "Вычесть 4 из обеих частей"
        assert transformation.preview_result is None

        # Проверяем, что был сделан только 1 вызов для генерации
        assert mock_chat.call_count == 1


class TestSolutionHistory:
    """Тесты для управления историей решения."""

    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.history = SolutionHistory("Решить уравнение: 2(x + 1) = 4")

    def test_history_initialization(self):
        """Тест инициализации истории."""
        assert self.history.original_task == "Решить уравнение: 2(x + 1) = 4"
        assert self.history.is_empty()
        assert self.history.get_steps_count() == 0

    def test_add_step(self):
        """Тест добавления шага."""
        transformations = [
            {
                "description": "Раскрыть скобки",
                "type": "expand",
                "expression": "2x + 2 = 4",
            }
        ]

        self.history.add_step(
            expression="2(x + 1) = 4", available_transformations=transformations
        )

        assert not self.history.is_empty()
        assert self.history.get_steps_count() == 1

        current_step = self.history.get_current_step()
        assert current_step is not None
        assert current_step.expression == "2(x + 1) = 4"
        assert current_step.step_number == 0

    def test_add_step_with_transformation(self):
        """Тест добавления шага с выбранным преобразованием."""
        transformations = [
            {
                "description": "Раскрыть скобки",
                "type": "expand",
                "expression": "2x + 2 = 4",
            }
        ]
        chosen_transformation = transformations[0]

        self.history.add_step(
            expression="2(x + 1) = 4",
            available_transformations=transformations,
            chosen_transformation=chosen_transformation,
            result_expression="2x + 2 = 4",
        )

        current_step = self.history.get_current_step()
        assert current_step.chosen_transformation == chosen_transformation
        assert current_step.result_expression == "2x + 2 = 4"

    def test_get_step_by_id(self):
        """Тест получения шага по ID."""
        step_id = self.history.add_step(
            expression="2(x + 1) = 4", available_transformations=[]
        )

        step = self.history.get_step_by_id(step_id)
        assert step is not None
        assert step.id == step_id

    def test_get_step_by_number(self):
        """Тест получения шага по номеру."""
        self.history.add_step(expression="2(x + 1) = 4", available_transformations=[])

        step = self.history.get_step_by_number(0)
        assert step is not None
        assert step.step_number == 0

    def test_get_step_summary(self):
        """Тест получения сводки шага."""
        chosen_transformation = {
            "description": "Раскрыть скобки",
            "type": "expand",
            "expression": "2x + 2 = 4",
        }

        step_id = self.history.add_step(
            expression="2(x + 1) = 4",
            available_transformations=[chosen_transformation],
            chosen_transformation=chosen_transformation,
            result_expression="2x + 2 = 4",
        )

        step = self.history.get_step_by_id(step_id)
        summary = self.history.get_step_summary(step)

        assert summary["step_number"] == 0
        assert summary["expression"] == "2(x + 1) = 4"
        assert summary["has_chosen_transformation"]
        assert summary["has_result"]
        assert summary["chosen_transformation"]["description"] == "Раскрыть скобки"

    def test_get_full_history_summary(self):
        """Тест получения полной сводки истории."""
        # Добавляем несколько шагов
        self.history.add_step(expression="2(x + 1) = 4", available_transformations=[])
        self.history.add_step(
            expression="2x + 2 = 4",
            available_transformations=[],
            chosen_transformation={"description": "Раскрыть скобки"},
            result_expression="2x + 2 = 4",
        )

        summary = self.history.get_full_history_summary()

        assert summary["original_task"] == "Решить уравнение: 2(x + 1) = 4"
        assert summary["total_steps"] == 2
        assert summary["current_step_number"] == 2
        assert len(summary["steps"]) == 2
        assert summary["is_complete"]

    def test_export_import_history(self):
        """Тест экспорта и импорта истории."""
        # Добавляем шаг
        self.history.add_step(
            expression="2(x + 1) = 4",
            available_transformations=[],
            chosen_transformation={"description": "Раскрыть скобки"},
            result_expression="2x + 2 = 4",
        )

        # Экспортируем
        exported = self.history.export_history()

        # Создаём новую историю и импортируем
        new_history = SolutionHistory("")
        new_history.import_history(exported)

        # Проверяем, что данные совпадают
        assert new_history.original_task == self.history.original_task
        assert new_history.get_steps_count() == self.history.get_steps_count()
        assert new_history.current_step_number == self.history.current_step_number


if __name__ == "__main__":
    unittest.main([__file__])

import pytest
from unittest.mock import Mock, patch
from core.engine import (
    TransformationEngine, 
    SolutionStep, 
    Transformation, 
    BaseTransformationType,
    GenerationResult,
    ApplyResult,
    CheckResult
)
from core.history import SolutionHistory, HistoryStep


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
    
    @patch('core.engine.OpenAI')
    def test_generate_transformations_success(self, mock_openai):
        """Тест успешной генерации преобразований."""
        # Мокаем ответ GPT
        mock_response = Mock()
        mock_response.choices[0].message.content = '''[
            {
                "description": "Раскрыть скобки",
                "expression": "2x + 2 = 4",
                "type": "expand",
                "metadata": {"difficulty": "elementary school"}
            }
        ]'''
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        result = self.engine.generate_transformations(self.sample_step)
        
        assert isinstance(result, GenerationResult)
        assert len(result.transformations) > 0
        assert result.transformations[0].description == "Раскрыть скобки"
        assert result.transformations[0].type == "expand"
    
    @patch('core.engine.OpenAI')
    def test_generate_transformations_error(self, mock_openai):
        """Тест обработки ошибки при генерации."""
        # Мокаем ошибку API
        mock_openai.return_value.chat.completions.create.side_effect = Exception("API Error")
        
        result = self.engine.generate_transformations(self.sample_step)
        
        assert isinstance(result, GenerationResult)
        assert len(result.transformations) == 1  # Заглушка
        assert "заглушка" in result.transformations[0].metadata.get("reasoning", "")
    
    @patch('core.engine.OpenAI')
    def test_apply_transformation_success(self, mock_openai):
        """Тест успешного применения преобразования."""
        transformation = Transformation(
            description="Раскрыть скобки",
            expression="2x + 2 = 4",
            type="expand"
        )
        
        # Мокаем ответ GPT
        mock_response = Mock()
        mock_response.choices[0].message.content = '''{
            "result": "2x + 2 = 4",
            "is_valid": true,
            "explanation": "Применил распределительный закон"
        }'''
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        result = self.engine.apply_transformation(self.sample_step, transformation)
        
        assert isinstance(result, ApplyResult)
        assert result.is_valid
        assert result.result == "2x + 2 = 4"
        assert "распределительный" in result.explanation
    
    @patch('core.engine.OpenAI')
    def test_apply_transformation_error(self, mock_openai):
        """Тест обработки ошибки при применении."""
        transformation = Transformation(
            description="Раскрыть скобки",
            expression="2x + 2 = 4",
            type="expand"
        )
        
        # Мокаем ошибку API
        mock_openai.return_value.chat.completions.create.side_effect = Exception("API Error")
        
        result = self.engine.apply_transformation(self.sample_step, transformation)
        
        assert isinstance(result, ApplyResult)
        assert not result.is_valid
        assert "ошибка" in result.explanation.lower()
    
    @patch('core.engine.OpenAI')
    def test_check_solution_completeness_solved(self, mock_openai):
        """Тест проверки завершённости - задача решена."""
        solved_step = SolutionStep(expression="x = 2")
        
        # Мокаем ответ GPT
        mock_response = Mock()
        mock_response.choices[0].message.content = '''{
            "is_solved": true,
            "confidence": 0.95,
            "explanation": "Переменная x выражена через число",
            "solution_type": "exact",
            "next_steps": []
        }'''
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        result = self.engine.check_solution_completeness(solved_step, "Решить уравнение")
        
        assert isinstance(result, CheckResult)
        assert result.is_solved
        assert result.confidence > 0.9
        assert result.solution_type == "exact"
    
    @patch('core.engine.OpenAI')
    def test_check_solution_completeness_not_solved(self, mock_openai):
        """Тест проверки завершённости - задача не решена."""
        # Мокаем ответ GPT
        mock_response = Mock()
        mock_response.choices[0].message.content = '''{
            "is_solved": false,
            "confidence": 0.3,
            "explanation": "Уравнение упрощено, но x не выражен",
            "solution_type": "partial",
            "next_steps": ["Вычесть 2", "Разделить на 2"]
        }'''
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        result = self.engine.check_solution_completeness(self.sample_step, "Решить уравнение")
        
        assert isinstance(result, CheckResult)
        assert not result.is_solved
        assert result.confidence < 0.5
        assert result.solution_type == "partial"
        assert len(result.next_steps) > 0

    def test_preview_mode_enabled(self):
        """Тест режима предпоказа - должен заполнять preview_result из expression."""
        engine = TransformationEngine(api_key="test-key", preview_mode=True)
        step = SolutionStep(expression="2x + 4 = 10")
        
        # Мокаем ответ GPT для генерации преобразований
        with patch.object(engine.client.chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '''
            [
                {
                    "description": "Вычесть 4 из обеих частей",
                    "expression": "2x = 6",
                    "type": "subtract"
                }
            ]
            '''
            mock_response.usage = Mock(prompt_tokens=100, completion_tokens=50, total_tokens=150)
            mock_create.return_value = mock_response
            
            result = engine.generate_transformations(step)
            
            # Проверяем, что результат содержит преобразования с предварительными результатами
            self.assertEqual(len(result.transformations), 1)
            transformation = result.transformations[0]
            self.assertEqual(transformation.description, "Вычесть 4 из обеих частей")
            self.assertEqual(transformation.expression, "2x = 6")
            self.assertEqual(transformation.preview_result, "2x = 6")  # Должен быть скопирован из expression
            
            # Проверяем, что был сделан только 1 вызов для генерации (без дополнительных запросов)
            self.assertEqual(mock_create.call_count, 1)

    def test_preview_mode_disabled(self):
        """Тест обычного режима - не должен генерировать предварительные результаты."""
        engine = TransformationEngine(api_key="test-key", preview_mode=False)
        step = SolutionStep(expression="2x + 4 = 10")
        
        # Мокаем ответ GPT для генерации преобразований
        with patch.object(engine.client.chat.completions, 'create') as mock_create:
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = '''
            [
                {
                    "description": "Вычесть 4 из обеих частей",
                    "expression": "2x = 6",
                    "type": "subtract"
                }
            ]
            '''
            mock_response.usage = Mock(prompt_tokens=100, completion_tokens=50, total_tokens=150)
            mock_create.return_value = mock_response
            
            result = engine.generate_transformations(step)
            
            # Проверяем, что результат содержит преобразования без предварительных результатов
            self.assertEqual(len(result.transformations), 1)
            transformation = result.transformations[0]
            self.assertEqual(transformation.description, "Вычесть 4 из обеих частей")
            self.assertIsNone(transformation.preview_result)
            
            # Проверяем, что был сделан только 1 вызов для генерации
            self.assertEqual(mock_create.call_count, 1)


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
            {"description": "Раскрыть скобки", "type": "expand", "expression": "2x + 2 = 4"}
        ]
        
        step_id = self.history.add_step(
            expression="2(x + 1) = 4",
            available_transformations=transformations
        )
        
        assert step_id is not None
        assert not self.history.is_empty()
        assert self.history.get_steps_count() == 1
        
        current_step = self.history.get_current_step()
        assert current_step is not None
        assert current_step.expression == "2(x + 1) = 4"
        assert current_step.step_number == 0
    
    def test_add_step_with_transformation(self):
        """Тест добавления шага с выбранным преобразованием."""
        transformations = [
            {"description": "Раскрыть скобки", "type": "expand", "expression": "2x + 2 = 4"}
        ]
        chosen_transformation = transformations[0]
        
        step_id = self.history.add_step(
            expression="2(x + 1) = 4",
            available_transformations=transformations,
            chosen_transformation=chosen_transformation,
            result_expression="2x + 2 = 4"
        )
        
        current_step = self.history.get_current_step()
        assert current_step.chosen_transformation == chosen_transformation
        assert current_step.result_expression == "2x + 2 = 4"
    
    def test_get_step_by_id(self):
        """Тест получения шага по ID."""
        step_id = self.history.add_step(
            expression="2(x + 1) = 4",
            available_transformations=[]
        )
        
        step = self.history.get_step_by_id(step_id)
        assert step is not None
        assert step.id == step_id
    
    def test_get_step_by_number(self):
        """Тест получения шага по номеру."""
        self.history.add_step(
            expression="2(x + 1) = 4",
            available_transformations=[]
        )
        
        step = self.history.get_step_by_number(0)
        assert step is not None
        assert step.step_number == 0
    
    def test_get_step_summary(self):
        """Тест получения сводки шага."""
        chosen_transformation = {
            "description": "Раскрыть скобки",
            "type": "expand",
            "expression": "2x + 2 = 4"
        }
        
        step_id = self.history.add_step(
            expression="2(x + 1) = 4",
            available_transformations=[chosen_transformation],
            chosen_transformation=chosen_transformation,
            result_expression="2x + 2 = 4"
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
        self.history.add_step(
            expression="2(x + 1) = 4",
            available_transformations=[]
        )
        self.history.add_step(
            expression="2x + 2 = 4",
            available_transformations=[],
            chosen_transformation={"description": "Раскрыть скобки"},
            result_expression="2x + 2 = 4"
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
            result_expression="2x + 2 = 4"
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
    pytest.main([__file__]) 
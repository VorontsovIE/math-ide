"""
Тесты для логирования ответов модели.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from utils.logging_utils import ModelResponseLogger, get_model_response_logger


class TestModelResponseLogger:
    """Тесты для ModelResponseLogger."""

    def test_init_creates_log_dir(self):
        """Тест создания директории для логов."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = os.path.join(temp_dir, "test_logs")
            logger = ModelResponseLogger(log_dir)
            
            assert Path(log_dir).exists()
            assert Path(log_dir).is_dir()

    def test_log_request_creates_file(self):
        """Тест создания файла лога запроса."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = ModelResponseLogger(temp_dir)
            
            messages = [
                {"role": "system", "content": "Test system prompt"},
                {"role": "user", "content": "Test user message"}
            ]
            
            request_id = logger.log_request(
                model="test-model",
                messages=messages,
                temperature=0.7
            )
            
            # Проверяем, что файл создан
            log_file = Path(temp_dir) / f"{request_id}_request.json"
            assert log_file.exists()
            
            # Проверяем содержимое
            with open(log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            assert data["model"] == "test-model"
            assert data["messages"] == messages
            assert data["temperature"] == 0.7
            assert "request_id" in data
            assert "timestamp" in data

    def test_log_response_creates_file(self):
        """Тест создания файла лога ответа."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = ModelResponseLogger(temp_dir)
            
            request_id = "test_request_123"
            usage = {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150
            }
            
            logger.log_response(
                request_id=request_id,
                content="Test response content",
                usage=usage,
                model="test-model",
                finish_reason="stop"
            )
            
            # Проверяем, что файл создан
            log_file = Path(temp_dir) / f"{request_id}_response.json"
            assert log_file.exists()
            
            # Проверяем содержимое
            with open(log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            assert data["request_id"] == request_id
            assert data["content"] == "Test response content"
            assert data["usage"] == usage
            assert data["model"] == "test-model"
            assert data["finish_reason"] == "stop"
            assert data["error"] is None

    def test_log_response_with_error(self):
        """Тест логирования ответа с ошибкой."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = ModelResponseLogger(temp_dir)
            
            request_id = "test_request_123"
            usage = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            
            logger.log_response(
                request_id=request_id,
                content="",
                usage=usage,
                model="test-model",
                finish_reason="error",
                error="Test error message"
            )
            
            # Проверяем содержимое
            log_file = Path(temp_dir) / f"{request_id}_response.json"
            with open(log_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            assert data["error"] == "Test error message"
            assert data["finish_reason"] == "error"

    def test_log_complete_interaction(self):
        """Тест логирования полного взаимодействия."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = ModelResponseLogger(temp_dir)
            
            messages = [
                {"role": "user", "content": "Test message"}
            ]
            usage = {
                "prompt_tokens": 10,
                "completion_tokens": 20,
                "total_tokens": 30
            }
            
            request_id = logger.log_complete_interaction(
                model="test-model",
                messages=messages,
                temperature=0.5,
                content="Test response",
                usage=usage,
                finish_reason="stop"
            )
            
            # Проверяем, что созданы оба файла
            request_file = Path(temp_dir) / f"{request_id}_request.json"
            response_file = Path(temp_dir) / f"{request_id}_response.json"
            
            assert request_file.exists()
            assert response_file.exists()

    def test_get_model_response_logger(self):
        """Тест функции get_model_response_logger."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = get_model_response_logger(temp_dir)
            
            assert isinstance(logger, ModelResponseLogger)
            assert logger.log_dir == Path(temp_dir)


class TestModelResponseLoggerIntegration:
    """Интеграционные тесты для логирования."""

    @patch('utils.logging_utils.get_logger')
    def test_logger_uses_correct_name(self, mock_get_logger):
        """Тест, что логгер использует правильное имя."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = ModelResponseLogger(temp_dir)
            
            # Вызываем любой метод для активации логирования
            logger.log_request("test-model", [], 0.5)
            
            # Проверяем, что get_logger был вызван с правильным именем
            mock_get_logger.assert_called_with("model_responses")

    def test_request_id_format(self):
        """Тест формата ID запроса."""
        with tempfile.TemporaryDirectory() as temp_dir:
            logger = ModelResponseLogger(temp_dir)
            
            request_id = logger.log_request("test-model", [], 0.5)
            
            # Проверяем формат ID
            assert request_id.startswith("req_")
            assert len(request_id) > 10  # Должен содержать timestamp 
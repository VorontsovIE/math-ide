"""
Модуль для управления промптами GPT.
Содержит PromptManager для загрузки и форматирования промптов.
"""

import logging
from pathlib import Path
from typing import Dict, Any

from .exceptions import PromptNotFoundError, PromptFormatError

logger = logging.getLogger(__name__)


class PromptManager:
    """Управляет загрузкой и подстановкой промптов."""

    def __init__(self, prompts_dir: str = "prompts") -> None:
        self.prompts_dir = Path(prompts_dir)
        self._cache: Dict[str, str] = {}

    def load_prompt(self, filename: str) -> str:
        """Загружает промпт из файла."""
        if filename in self._cache:
            return self._cache[filename]

        prompt_path = self.prompts_dir / filename
        if not prompt_path.exists():
            raise PromptNotFoundError(f"Промпт не найден: {prompt_path}")

        with open(prompt_path, "r", encoding="utf-8") as f:
            content = f.read()
            self._cache[filename] = content
            return content

    def format_prompt(self, prompt: str, **kwargs: Any) -> str:
        """Форматирует промпт с подстановкой переменных."""
        try:
            return prompt.format(**kwargs)
        except (KeyError, ValueError) as e:
            raise PromptFormatError(f"Ошибка форматирования промпта: {str(e)}")

    def load_and_format_prompt(self, filename: str, **kwargs: Any) -> str:
        """Загружает и форматирует промпт одной операцией."""
        prompt = self.load_prompt(filename)
        return self.format_prompt(prompt, **kwargs)

    def clear_cache(self) -> None:
        """Очищает кеш промптов."""
        self._cache.clear()

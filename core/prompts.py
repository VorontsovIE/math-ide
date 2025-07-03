"""
Модуль для управления промптами GPT.
Содержит PromptManager для загрузки и форматирования промптов.
"""

import logging
from pathlib import Path
from typing import Any, Dict, Tuple

from .exceptions import PromptFormatError, PromptNotFoundError

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

    def load_split_prompt(self, base_name: str) -> Tuple[str, str]:
        """
        Загружает разделенный промпт (system и user части).
        
        Args:
            base_name: Базовое имя промпта (без расширения)
            
        Returns:
            Кортеж (system_prompt, user_prompt)
        """
        system_filename = f"{base_name}_system.md"
        user_filename = f"{base_name}_user.md"
        
        system_prompt = self.load_prompt(system_filename)
        user_prompt = self.load_prompt(user_filename)
        
        return system_prompt, user_prompt

    def format_prompt(self, prompt: str, **kwargs: Any) -> str:
        """Форматирует промпт с подстановкой переменных."""
        try:
            return prompt.format(**kwargs)
        except (KeyError, ValueError) as e:
            raise PromptFormatError(f"Ошибка форматирования промпта: {str(e)}")

    def format_split_prompt(self, system_prompt: str, user_prompt: str, **kwargs: Any) -> Tuple[str, str]:
        """
        Форматирует разделенный промпт с подстановкой переменных.
        
        Args:
            system_prompt: System часть промпта
            user_prompt: User часть промпта
            **kwargs: Переменные для подстановки
            
        Returns:
            Кортеж (formatted_system_prompt, formatted_user_prompt)
        """
        formatted_system = self.format_prompt(system_prompt, **kwargs)
        formatted_user = self.format_prompt(user_prompt, **kwargs)
        
        return formatted_system, formatted_user

    def load_and_format_prompt(self, filename: str, **kwargs: Any) -> str:
        """Загружает и форматирует промпт одной операцией."""
        prompt = self.load_prompt(filename)
        return self.format_prompt(prompt, **kwargs)

    def load_and_format_split_prompt(self, base_name: str, **kwargs: Any) -> Tuple[str, str]:
        """
        Загружает и форматирует разделенный промпт одной операцией.
        
        Args:
            base_name: Базовое имя промпта (без расширения)
            **kwargs: Переменные для подстановки
            
        Returns:
            Кортеж (formatted_system_prompt, formatted_user_prompt)
        """
        system_prompt, user_prompt = self.load_split_prompt(base_name)
        return self.format_split_prompt(system_prompt, user_prompt, **kwargs)

    def clear_cache(self) -> None:
        """Очищает кеш промптов."""
        self._cache.clear()

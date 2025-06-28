"""
Интерфейсы для взаимодействия с пользователем.
Содержит CLI, Telegram бота и веб-интерфейс.
"""

# Убираем импорт CLI чтобы не блокировать другие модули
# from .cli import MathIDECLI

from .cli import cli
from .bot_runner import run_bot

__all__: list[str] = ["cli", "run_bot"]

"""
Интерфейсы для взаимодействия с пользователем.
Содержит CLI, Telegram бота и веб-интерфейс.
"""

# Убираем импорт CLI чтобы не блокировать другие модули
# from .cli import MathIDECLI

from .cli import cli
from .telegram_bot import run_bot

__all__: list[str] = ["cli", "run_bot"]

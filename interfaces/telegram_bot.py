"""
Новый модульный Telegram бот для решения математических задач.
Использует разделенную архитектуру с отдельными модулями.
"""

import logging
import os
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

# Импорты из созданных модулей
from .telegram.handlers import (
    start,
    help_command,
    cancel,
    show_history,
    handle_task,
    handle_transformation_choice,
)
from .telegram.state import user_states
from .telegram.rate_limiter import rate_limiter
from .telegram.utils import send_status_message
from .telegram.keyboards import get_transformations_keyboard
from .telegram.renderers import render_latex_to_image

logger = logging.getLogger(__name__)


def run_bot(token: str) -> None:
    """Запуск модульного Telegram бота."""
    logger.info("Запуск модульного Telegram бота")

    # Создаем приложение
    application = Application.builder().token(token).build()

    # Регистрируем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("history", show_history))

    # Обработчик callback-запросов (кнопки)
    application.add_handler(CallbackQueryHandler(handle_transformation_choice))

    # Обработчик текстовых сообщений (задачи)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task)
    )

    logger.info("Все обработчики зарегистрированы")

    # Запускаем бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)


# Для обратной совместимости - экспортируем старые функции из модулей
from .telegram import *

if __name__ == "__main__":
    # Получаем токен из переменной окружения
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        exit(1)

    run_bot(token)

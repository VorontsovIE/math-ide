"""
Новый модульный Telegram бот для решения математических задач.
Использует разделенную архитектуру с отдельными модулями.
"""

import logging
import os

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from .telegram_bot.handlers import (
    cancel,
    handle_task,
    help_command,
    show_history,
    start,
)

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

    # Обработчик callback-запросов (кнопки) - УСТАРЕЛ, используется telegram_bot/__main__.py
    # application.add_handler(CallbackQueryHandler(handle_transformation_choice))

    # Обработчик текстовых сообщений (задачи)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task)
    )

    logger.info("Все обработчики зарегистрированы")

    # Запускаем бота
    application.run_polling()


if __name__ == "__main__":
    # Получаем токен из переменной окружения
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        exit(1)

    run_bot(token)

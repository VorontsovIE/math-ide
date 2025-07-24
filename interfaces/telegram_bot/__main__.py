"""
Точка входа для запуска Telegram бота Math IDE.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Добавляем корневую директорию в PYTHONPATH
root_dir = Path(__file__).parent.parent.parent
sys.path.append(str(root_dir))

from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from .handlers import (
    cancel,
    handle_task,
    help_command,
    show_history,
    start,
    handle_callback_query,
)
from .rate_limiter import rate_limiter
from .state import user_states

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def load_env_files() -> bool:
    """Загружает переменные окружения из .env файлов."""
    env_files = [
        ".env.local",
        ".env",
        ".env.example",
    ]

    for env_file in env_files:
        env_path = root_dir / env_file
        if env_path.exists():
            load_dotenv(env_path)
            if env_file != ".env.example":
                logger.info(f"Загружены настройки из {env_file}")
            return True

    logger.warning(".env файл не найден, используются переменные окружения системы")
    return False


async def error_handler(update, context):
    """Обработчик ошибок."""
    logger.error(f"Exception while handling an update: {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Произошла ошибка при обработке вашего запроса. Попробуйте еще раз."
        )


def main() -> None:
    """Основная функция запуска Telegram бота."""
    # Загружаем переменные окружения
    load_env_files()

    # Проверяем наличие токена бота
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN не задан в переменных окружения")
        sys.exit(1)

    # Проверяем наличие API ключа OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if not openai_key:
        logger.warning("OPENAI_API_KEY не задан, некоторые функции могут не работать")

    logger.info("Запуск Telegram бота Math IDE...")

    # Создаем приложение
    application = Application.builder().token(token).build()

    # Добавляем обработчики команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("history", show_history))

    # Обработчик callback-запросов (кнопки) - НОВЫЙ СЦЕНАРИЙ
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Обработчик текстовых сообщений (задачи)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task))

    # Добавляем обработчик ошибок
    application.add_error_handler(error_handler)

    # Запускаем бота
    logger.info("Бот запущен. Нажмите Ctrl+C для остановки.")
    try:
        application.run_polling(
            allowed_updates=["message", "callback_query"],
            drop_pending_updates=True,
        )
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки, завершаем работу...")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
        sys.exit(1)
    finally:
        # Очищаем состояние пользователей
        user_states.clear()
        logger.info("Бот остановлен")


if __name__ == "__main__":
    main()

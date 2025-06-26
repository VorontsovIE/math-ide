"""
Главный модуль Telegram бота для MathIDE.
Использует разделенные модули из interfaces/telegram/
"""

import os
import logging
from dotenv import load_dotenv

from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

from .telegram import (
    # Обработчики команд
    start,
    help_command, 
    cancel,
    show_history,
    handle_task,
    handle_transformation_choice,
    # Пока не импортируем, так как handlers.py содержит только заглушки
    # handle_rollback_suggestion,
    # handle_verification_choice,
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_bot(token: str) -> None:
    """Запускает Telegram-бота."""
    logger.info("Инициализация бота...")
    try:
        # Создаём приложение
        application = Application.builder().token(token).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("cancel", cancel))
        application.add_handler(CommandHandler("history", show_history))
        
        # Обработчик текстовых сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task))
        
        # Callback handlers - пока закомментированы, так как handlers.py неполный
        # application.add_handler(CallbackQueryHandler(handle_rollback_suggestion, pattern=r"^(rollback_|continue_current)"))
        # application.add_handler(CallbackQueryHandler(handle_verification_choice, pattern=r"^verify_"))
        application.add_handler(CallbackQueryHandler(handle_transformation_choice))
        
        logger.info("Бот успешно инициализирован")
        
        # Запускаем бота
        logger.info("Запуск бота...")
        application.run_polling()
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        raise


if __name__ == "__main__":
    # Загружаем переменные окружения
    load_dotenv()
    
    # Получаем токен бота
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.critical("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        exit(1)
    
    logger.info("Запуск Telegram-бота...")
    run_bot(token) 
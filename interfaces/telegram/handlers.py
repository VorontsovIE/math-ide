"""
Модуль обработчиков команд для Telegram бота.
Содержит основные функции-обработчики для команд и callback'ов.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes

from .state import user_states, UserState

logger = logging.getLogger(__name__)


async def start(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    """Обработчик команды /start."""
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} запустил бота")
    
    user_states[user_id] = UserState()
    
    await update.message.reply_text(
        "Привет! Я помогу вам решить математическую задачу пошагово. "
        "Отправьте мне задачу в LaTeX-формате, например:\n"
        "2(x + 1) = 4"
    )


async def help_command(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    """Обработчик команды /help."""
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} запросил помощь")
    
    await update.message.reply_text(
        "Я помогаю решать математические задачи пошагово.\n\n"
        "Доступные команды:\n"
        "/start - Начать новое решение\n"
        "/help - Показать эту справку\n"
        "/history - Показать историю решения\n"
        "/cancel - Отменить текущее решение\n\n"
        "Чтобы начать, просто отправьте мне математическую задачу."
    )


async def cancel(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    """Обработчик команды /cancel."""
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} отменил текущее решение")
    
    user_states[user_id] = UserState()
    
    await update.message.reply_text(
        "Текущее решение отменено. Отправьте новую задачу."
    )


# Заглушки для других обработчиков - будут добавлены позже 
async def handle_task(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    """Обработчик новой задачи."""
    await update.message.reply_text("⚙️ Модуль handlers создан, но handle_task еще не реализована полностью.")


async def show_history(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    """Обработчик команды /history."""
    await update.message.reply_text("⚙️ Модуль handlers создан, но show_history еще не реализована полностью.")


async def handle_transformation_choice(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    """Обработчик выбора преобразования."""
    await update.callback_query.answer("⚙️ Модуль handlers создан, но handle_transformation_choice еще не реализована полностью.")

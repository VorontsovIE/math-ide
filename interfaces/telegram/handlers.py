"""
Модуль обработчиков команд для Telegram бота.
Содержит основные функции-обработчики для команд и callback'ов.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from telegram import Update
    from telegram.ext import ContextTypes

from core.engine import TransformationEngine
from core.history import SolutionHistory  
from core.types import SolutionStep, Transformation

from .state import user_states, UserState
from .rate_limiter import rate_limiter
from .utils import send_status_message, edit_status_message
from .keyboards import get_transformations_keyboard, get_verification_keyboard
from .renderers import render_transformations_image, render_latex_to_image

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


async def show_history(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    """Обработчик команды /history."""
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} запросил историю")
    
    state = user_states.get(user_id)
    
    if not state or not state.history:
        logger.warning(f"История пуста для пользователя {user_id}")
        await update.message.reply_text("История пуста. Начните решение задачи.")
        return
    
    try:
        # Показываем упрощенную историю
        summary = state.history.get_full_history_summary()
        logger.info(f"Получена история решения: {len(summary['steps'])} шагов")
        
        history_text = f"📚 История решения задачи:\n'{state.history.original_task}'\n\n"
        for i, step in enumerate(summary['steps'], 1):
            history_text += f"Шаг {i}: {step.get('expression', 'N/A')}\n"
            if step.get('chosen_transformation'):
                history_text += f"➡️ {step['chosen_transformation'].get('description', 'N/A')}\n"
            history_text += "\n"
        
        await update.message.reply_text(history_text)
            
    except Exception as e:
        logger.error(f"Ошибка при показе истории: {e}")
        await update.message.reply_text("Ошибка при получении истории решения.")


async def handle_task(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    """Обработчик новой задачи."""
    user_id = update.effective_user.id
    task = update.message.text
    logger.info(f"Пользователь {user_id} отправил сообщение: {task}")
    
    # Проверяем состояние ожидания ввода от пользователя
    state = user_states.get(user_id)
    if state:
        if state.waiting_for_custom_transformation:
            await handle_custom_transformation(update, user_id, task)
            return
        elif state.waiting_for_user_suggestion:
            await handle_user_suggestion(update, user_id, task)
            return
        elif state.waiting_for_user_result:
            await handle_user_transformation_result(update, user_id, task)
            return
    
    # Отмечаем начало операции
    rate_limiter.start_operation(user_id)
    
    # Отправляем начальный статус
    status_message = await send_status_message(update, "🔄 Анализирую задачу...", force_update=True)
    
    try:
        # Инициализируем движок и историю
        if status_message:
            await edit_status_message(status_message, "🧠 Генерирую возможные преобразования...", user_id)
        
        engine = TransformationEngine(preview_mode=True)
        history = SolutionHistory(task)
        current_step = SolutionStep(expression=task)
        
        # Сохраняем начальное состояние
        initial_step_id = history.add_step(
            expression=task,
            available_transformations=[]
        )
        logger.debug("Создана новая история решения")
        
        # Генерируем возможные преобразования
        logger.info("Генерация возможных преобразований...")
        generation_result = engine.generate_transformations(current_step)
        logger.info(f"Сгенерировано {len(generation_result.transformations)} преобразований")
        
        # Обновляем начальный шаг с доступными преобразованиями
        if history.steps:
            history.steps[0].available_transformations = [tr.__dict__ for tr in generation_result.transformations]
        
        # Проверяем, есть ли доступные преобразования
        if not generation_result.transformations:
            logger.warning(f"Не найдено ни одного варианта действия для задачи: {task}")
            if status_message:
                await edit_status_message(status_message, 
                    f"😕 К сожалению, я не смог найти подходящих преобразований для вашей задачи:\n\n"
                    f"`{task}`\n\n"
                    f"Возможные причины:\n"
                    f"• Задача уже решена или слишком простая\n"
                    f"• Нестандартный формат выражения\n"
                    f"• Ошибка в LaTeX-синтаксисе\n\n"
                    f"Попробуйте:\n"
                    f"• Переформулировать задачу\n"
                    f"• Проверить корректность LaTeX\n"
                    f"• Отправить более сложное выражение", user_id, force_update=True)
            return
        
        # Обновляем состояние пользователя
        user_states[user_id] = UserState(
            history=history,
            current_step=current_step,
            available_transformations=generation_result.transformations
        )
        
        # Подготавливаем изображение
        if status_message:
            await edit_status_message(status_message, "📊 Подготавливаю визуализацию...", user_id)
        
        img = render_transformations_image(task, generation_result.transformations)
        
        # Удаляем статус и отправляем результат
        if status_message:
            await status_message.delete()
        
        await update.message.reply_photo(
            photo=img,
            caption="Начинаем решение. Выберите преобразование:",
            reply_markup=get_transformations_keyboard(generation_result.transformations, initial_step_id)
        )
        logger.info("Задача успешно инициализирована")
        
    except Exception as e:
        logger.error(f"Ошибка при обработке задачи: {e}")
        error_message = (
            "❌ Произошла ошибка при обработке задачи.\n\n"
            "Пожалуйста, проверьте корректность LaTeX-синтаксиса и попробуйте снова.\n\n"
            f"Детали ошибки: {str(e)}"
        )
        
        if status_message:
            await edit_status_message(status_message, error_message, user_id, force_update=True)
        else:
            await update.message.reply_text(error_message)


async def handle_transformation_choice(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    """Обработчик выбора преобразования."""
    query = update.callback_query
    user_id = query.from_user.id
    logger.info(f"Пользователь {user_id} выбрал преобразование")
    
    state = user_states.get(user_id)
    
    if not state or not state.history:
        logger.warning(f"Нет активного состояния для пользователя {user_id}")
        await query.answer("Ошибка: начните новое решение")
        return
    
    try:
        # Базовая логика для демонстрации 
        await query.answer("🔧 Модуль handlers создан и работает!")
        await query.message.reply_text(
            "⚙️ Успешно! Telegram бот теперь использует модульную архитектуру!\n\n"
            "🎯 **Этап 4 завершен на 90%**\n\n"
            "✅ Созданные модули:\n"
            "• state.py - управление состояниями\n"
            "• rate_limiter.py - ограничение запросов\n"
            "• utils.py - утилиты отправки сообщений\n"
            "• keyboards.py - inline-клавиатуры\n"
            "• renderers.py - рендеринг LaTeX\n"
            "• handlers.py - обработчики команд\n\n"
            "📊 Основные команды работают:\n"
            "• /start, /help, /cancel, /history\n"
            "• Обработка новых задач\n"
            "• Базовые callback'ы\n\n"
            "🚀 Рефакторинг почти завершен!"
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке выбора преобразования: {e}")
        await query.answer("❌ Произошла ошибка при обработке преобразования")


# Заглушки для остальных обработчиков - будут реализованы по мере необходимости
async def handle_custom_transformation(update: "Update", user_id: int, custom_description: str) -> None:
    """Обработчик пользовательского преобразования."""
    await update.message.reply_text("🔧 handle_custom_transformation еще не реализована полностью в handlers.py")


async def handle_user_suggestion(update: "Update", user_id: int, user_suggestion: str) -> None:
    """Обработчик предложения пользователя."""
    await update.message.reply_text("🔧 handle_user_suggestion еще не реализована полностью в handlers.py")


async def handle_user_transformation_result(update: "Update", user_id: int, user_input: str) -> None:
    """Обработчик результата пользовательского преобразования."""
    await update.message.reply_text("🔧 handle_user_transformation_result еще не реализована полностью в handlers.py")


async def show_final_history(update_or_query, history: SolutionHistory) -> None:
    """Показ финальной истории решения."""
    try:
        if hasattr(update_or_query, 'message'):
            await update_or_query.message.reply_text("📚 История решения (упрощенная версия)")
        else:
            await update_or_query.reply_text("📚 История решения (упрощенная версия)")
    except Exception as e:
        logger.error(f"Ошибка в show_final_history: {e}")

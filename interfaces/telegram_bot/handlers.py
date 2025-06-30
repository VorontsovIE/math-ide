"""
Модуль обработчиков команд для Telegram бота.
Содержит основные функции-обработчики для команд и callback'ов.
"""

import logging
from typing import TYPE_CHECKING, Union
import json
import base64

if TYPE_CHECKING:
    from telegram import Update, Message, CallbackQuery
    from telegram.ext import ContextTypes

from core.engines import TransformationGenerator
from core.history import SolutionHistory
from core.types import SolutionStep

from .keyboards import get_transformations_keyboard
from .rate_limiter import rate_limiter
from .renderers import render_transformations_images, render_latex_to_image
from .state import UserState, user_states
from .utils import edit_status_message, send_status_message

logger = logging.getLogger(__name__)


async def start(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    """Обработчик команды /start."""
    if not update.effective_user:
        return
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} запустил бота")

    user_states[user_id] = UserState()

    if update.message:
        await update.message.reply_text(
            "Привет! Я помогу вам решить математическую задачу пошагово. "
            "Отправьте мне задачу в LaTeX-формате, например:\n"
            "2(x + 1) = 4"
        )


async def help_command(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    """Обработчик команды /help."""
    if not update.effective_user:
        return
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} запросил помощь")

    if update.message:
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
    if not update.effective_user:
        return
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} отменил текущее решение")

    user_states[user_id] = UserState()

    if update.message:
        await update.message.reply_text(
            "Текущее решение отменено. Отправьте новую задачу."
        )


async def show_history(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    """Обработчик команды /history."""
    if not update.effective_user:
        return
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} запросил историю")

    state = user_states.get(user_id)

    if not state or not state.history:
        logger.warning(f"История пуста для пользователя {user_id}")
        if update.message:
            await update.message.reply_text("История пуста. Начните решение задачи.")
        return

    try:
        # Показываем упрощенную историю
        summary = state.history.get_full_history_summary()
        logger.info(f"Получена история решения: {len(summary['steps'])} шагов")

        history_text = (
            f"📚 История решения задачи:\n'{state.history.original_task}'\n\n"
        )
        for i, step in enumerate(summary["steps"], 1):
            history_text += f"Шаг {i}: {step.get('expression', 'N/A')}\n"
            if step.get("chosen_transformation"):
                history_text += (
                    f"➡️ {step['chosen_transformation'].get('description', 'N/A')}\n"
                )
            history_text += "\n"

        if update.message:
            await update.message.reply_text(history_text)

    except Exception as e:
        logger.error(f"Ошибка при показе истории: {e}")
        if update.message:
            await update.message.reply_text("Ошибка при получении истории решения.")


async def handle_task(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    """Обработчик новой задачи."""
    if not update.effective_user or not update.message or not update.message.text:
        return
    user_id = update.effective_user.id
    task = update.message.text
    logger.info(f"Пользователь {user_id} отправил сообщение: {task}")

    # Извлекаем математическое выражение из текста
    from .renderers import extract_math_expression
    cleaned_task = extract_math_expression(task)
    if cleaned_task != task:
        logger.info(f"Извлечено математическое выражение: {cleaned_task}")
    
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
    status_message = await send_status_message(
        update, "🔄 Анализирую задачу...", force_update=True
    )

    try:
        # Инициализируем движок и историю
        if status_message:
            await edit_status_message(
                status_message, "🧠 Генерирую возможные преобразования...", user_id
            )

        # Создаем временные объекты для демонстрации
        from core.gpt_client import GPTClient
        from core.prompts import PromptManager

        client = GPTClient()
        prompt_manager = PromptManager()
        engine = TransformationGenerator(client, prompt_manager, preview_mode=True)
        history = SolutionHistory(cleaned_task)
        current_step = SolutionStep(expression=cleaned_task)

        # Сохраняем начальное состояние
        initial_step_id = history.add_step(
            expression=cleaned_task, available_transformations=[]
        )
        logger.debug("Создана новая история решения")

        # Генерируем возможные преобразования
        logger.info("Генерация возможных преобразований...")
        generation_result = engine.generate_transformations(current_step)
        logger.info(
            f"Сгенерировано {len(generation_result.transformations)} преобразований"
        )

        # Детальное логирование для диагностики
        logger.debug("Детали результата генерации:")
        logger.debug(f"  Тип результата: {type(generation_result)}")
        logger.debug(f"  Количество преобразований: {len(generation_result.transformations)}")
        
        if generation_result.transformations:
            logger.debug("  Преобразования:")
            for i, tr in enumerate(generation_result.transformations):
                logger.debug(f"    {i}: {tr.description} ({tr.type})")
        else:
            logger.warning("  Список преобразований пуст!")

        # Обновляем начальный шаг с доступными преобразованиями
        if history.steps:
            history.steps[0].available_transformations = [
                tr.__dict__ for tr in generation_result.transformations
            ]

        # Проверяем, есть ли доступные преобразования
        if not generation_result.transformations:
            logger.warning(f"Не найдено ни одного варианта действия для задачи: {cleaned_task}")
            logger.error("ПРИЧИНА: generation_result.transformations пуст")
            logger.error("Это может быть вызвано:")
            logger.error("  1. Ошибкой парсинга JSON от GPT")
            logger.error("  2. Отсутствием обязательных полей в JSON")
            logger.error("  3. Пустым массивом от GPT")
            logger.error("  4. Ошибкой в LaTeX-синтаксисе")
            
            if status_message:
                await edit_status_message(
                    status_message,
                    f"😕 К сожалению, я не смог найти подходящих преобразований для вашей задачи:\n\n"
                    f"`{cleaned_task}`\n\n"
                    f"Возможные причины:\n"
                    f"• Задача уже решена или слишком простая\n"
                    f"• Нестандартный формат выражения\n"
                    f"• Ошибка в LaTeX-синтаксисе\n\n"
                    f"Попробуйте:\n"
                    f"• Переформулировать задачу\n"
                    f"• Проверить корректность LaTeX\n"
                    f"• Отправить более сложное выражение",
                    user_id,
                    force_update=True,
                )
            return

        # Обновляем состояние пользователя
        user_states[user_id] = UserState(
            history=history,
            current_step=current_step,
            available_transformations=generation_result.transformations,
        )

        # Подготавливаем изображения
        if status_message:
            await edit_status_message(
                status_message, "📊 Подготавливаю визуализацию...", user_id
            )

        # Создаем изображения с выражением и преобразованиями
        expression_img, transformations_img = render_transformations_images(cleaned_task, generation_result.transformations)

        # Удаляем статус
        if status_message:
            await status_message.delete()

        # Отправляем первое сообщение с исходным выражением
        await update.message.reply_photo(
            photo=expression_img,
            caption="📝 **Исходное выражение:**",
        )

        # Отправляем второе сообщение с преобразованиями
        await update.message.reply_photo(
            photo=transformations_img,
            caption="🎯 **Доступные преобразования:**\nВыберите преобразование:",
            reply_markup=get_transformations_keyboard(
                [tr.__dict__ for tr in generation_result.transformations],
                initial_step_id,
            ),
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
            await edit_status_message(
                status_message, error_message, user_id, force_update=True
            )
        elif update.message and isinstance(update.message, Message):
            # Подавление ошибки mypy из-за MaybeInaccessibleMessage (python-telegram-bot)
            await update.message.reply_text(error_message)  # type: ignore[attr-defined]


async def handle_transformation_choice(
    update: "Update", context: "ContextTypes.DEFAULT_TYPE"
) -> None:
    """Обработчик выбора преобразования."""
    if not update.callback_query:
        return
    query = update.callback_query
    if not query.from_user:
        return
    user_id = query.from_user.id
    logger.info(f"Пользователь {user_id} выбрал преобразование")

    state = user_states.get(user_id)

    if not state or not state.history:
        logger.warning(f"Нет активного состояния для пользователя {user_id}")
        await query.answer("Ошибка: начните новое решение")
        return

    try:
        # Получаем данные из callback
        callback_data = query.data
        if not callback_data:
            await query.answer("Неверный формат данных")
            return

        # Обрабатываем разные типы callback данных
        if callback_data.startswith("transform_"):
            # Обработка выбора преобразования
            await _handle_transform_choice(query, callback_data, state)
        elif callback_data.startswith("back_"):
            # Обработка кнопки "Назад"
            await _handle_back_button(query, callback_data, state)
        elif callback_data.startswith("refresh_"):
            # Обработка кнопки "Обновить"
            await _handle_refresh_button(query, callback_data, state)
        else:
            await query.answer("Неизвестный тип действия")
            return

    except Exception as e:
        logger.error(f"Ошибка при обработке выбора преобразования: {e}")
        await query.answer("❌ Произошла ошибка при обработке преобразования")


async def _handle_transform_choice(
    query: "CallbackQuery", callback_data: str, state: UserState
) -> None:
    """Обработка выбора преобразования."""
    # Извлекаем закодированные данные из callback
    try:
        encoded_data = callback_data.split("_")[2]
        result_data = json.loads(base64.b64decode(encoded_data).decode())
        transform_index = result_data["index"]
        result_expression = result_data["result"]
        transform_description = result_data["description"]
    except (IndexError, ValueError, KeyError, Exception) as e:
        logger.error(f"Ошибка декодирования данных кнопки: {e}")
        await query.answer("Неверный формат данных")
        return

    # Проверяем, что индекс в допустимых пределах
    if not state.available_transformations or transform_index >= len(state.available_transformations):
        await query.answer("Преобразование не найдено")
        return

    # Получаем выбранное преобразование
    selected_transformation = state.available_transformations[transform_index]
    
    if not state.current_step:
        await query.answer("❌ Ошибка: нет текущего шага")
        return
        
    # Создаем новый шаг с результатом
    new_step = SolutionStep(expression=result_expression)
    state.current_step = new_step
    
    # Добавляем шаг в историю
    step_id = state.history.add_step(
        expression=result_expression,
        chosen_transformation=selected_transformation.__dict__,
        available_transformations=[]
    ) if state.history else "current"
    
    # Генерируем новые преобразования для следующего шага
    logger.info("Генерация новых преобразований для следующего шага...")
    from core.engines.transformation_generator import TransformationGenerator
    from core.gpt_client import GPTClient
    from core.prompts import PromptManager
    
    client = GPTClient()
    prompt_manager = PromptManager()
    engine = TransformationGenerator(client, prompt_manager, preview_mode=True)
    generation_result = engine.generate_transformations(new_step)
    
    # Обновляем состояние с новыми преобразованиями
    state.available_transformations = generation_result.transformations
    
    # Отправляем результат пользователю
    await query.answer("✅ Преобразование применено!")
    
    if query.message:
        # Если есть новые преобразования, показываем их
        if generation_result.transformations:
            # Подготавливаем изображения с выражением и преобразованиями
            expression_img, transformations_img = render_transformations_images(result_expression, generation_result.transformations)
            
            # Отправляем изображение с выражением
            await query.message.reply_photo(
                photo=expression_img,
                caption=f"🔧 **Применено преобразование:**\n"
                        f"_{transform_description}_\n\n"
                        f"📝 **Результат:**",
            )
            
            # Отправляем изображение с преобразованиями
            await query.message.reply_photo(
                photo=transformations_img,
                caption="🎯 **Выберите следующее преобразование:**",
                reply_markup=get_transformations_keyboard(
                    [tr.__dict__ for tr in generation_result.transformations],
                    step_id,
                ),
            )
        else:
            # Если нет новых преобразований, показываем сообщение о завершении
            await query.message.reply_text(
                f"🔧 **Применено преобразование:**\n"
                f"_{transform_description}_\n\n"
                f"📝 **Результат:**\n"
                f"`{result_expression}`\n\n"
                f"🎉 **Задача решена!**\n"
                f"Отправьте новую задачу для продолжения."
            )


async def _handle_back_button(
    query: "CallbackQuery", callback_data: str, state: UserState
) -> None:
    """Обработка кнопки 'Назад'."""
    await query.answer("◀️ Возврат к предыдущему шагу")
    
    # Пока что просто показываем сообщение
    if query.message:
        await query.message.reply_text(
            "🔧 Функция 'Назад' пока не реализована.\n"
            "Отправьте новую задачу для продолжения."
        )


async def _handle_refresh_button(
    query: "CallbackQuery", callback_data: str, state: UserState
) -> None:
    """Обработка кнопки 'Обновить'."""
    await query.answer("🔄 Обновление преобразований...")
    
    if not state.current_step:
        await query.answer("❌ Ошибка: нет текущего шага")
        return
    
    try:
        # Генерируем новые преобразования
        from core.engines.transformation_generator import TransformationGenerator
        from core.gpt_client import GPTClient
        from core.prompts import PromptManager
        
        client = GPTClient()
        prompt_manager = PromptManager()
        engine = TransformationGenerator(client, prompt_manager, preview_mode=True)
        
        generation_result = engine.generate_transformations(state.current_step)
        state.available_transformations = generation_result.transformations
        
        if query.message:
            # Подготавливаем изображения с выражением и преобразованиями
            expression_img, transformations_img = render_transformations_images(state.current_step.expression, generation_result.transformations)
            
            # Отправляем изображение с выражением
            await query.message.reply_photo(
                photo=expression_img,
                caption=f"🔄 **Обновленные преобразования для:**",
            )
            
            # Отправляем изображение с преобразованиями
            await query.message.reply_photo(
                photo=transformations_img,
                caption="🎯 **Выберите преобразование:**",
                reply_markup=get_transformations_keyboard(
                    [tr.__dict__ for tr in generation_result.transformations],
                    state.history.get_current_step().id if state.history and state.history.get_current_step() else "current",
                ),
            )
    except Exception as e:
        logger.error(f"Ошибка при обновлении преобразований: {e}")
        await query.answer("❌ Ошибка при обновлении")
        if query.message:
            await query.message.reply_text(
                "❌ **Ошибка при обновлении преобразований**\n"
                "Попробуйте еще раз или отправьте новую задачу."
            )


# Заглушки для остальных обработчиков - будут реализованы по мере необходимости
async def handle_custom_transformation(
    update: "Update", user_id: int, custom_description: str
) -> None:
    """Обработчик пользовательского преобразования."""
    if update.message:
        await update.message.reply_text(
            "🔧 handle_custom_transformation еще не реализована полностью в handlers.py"
        )


async def handle_user_suggestion(
    update: "Update", user_id: int, user_suggestion: str
) -> None:
    """Обработчик предложения пользователя."""
    if update.message:
        await update.message.reply_text(
            "🔧 handle_user_suggestion еще не реализована полностью в handlers.py"
        )


async def handle_user_transformation_result(
    update: "Update", user_id: int, user_input: str
) -> None:
    """Обработчик результата пользовательского преобразования."""
    if update.message:
        await update.message.reply_text(
            "🔧 handle_user_transformation_result еще не реализована полностью в handlers.py"
        )


async def show_final_history(
    update_or_query: Union["Update", "Message"], history: SolutionHistory
) -> None:
    """Показ финальной истории решения."""
    try:
        if hasattr(update_or_query, "message") and update_or_query.message:
            await update_or_query.message.reply_text(
                "📚 История решения (упрощенная версия)"
            )
        elif hasattr(update_or_query, "reply_text"):
            await update_or_query.reply_text("📚 История решения (упрощенная версия)")
        else:
            logger.warning("Неподдерживаемый тип для show_final_history")
    except Exception as e:
        logger.error(f"Ошибка в show_final_history: {e}")

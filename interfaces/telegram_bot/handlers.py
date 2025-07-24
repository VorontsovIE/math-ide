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
from core.engine import TransformationEngine

from .keyboards import get_transformations_keyboard, get_transformations_description_text
from .rate_limiter import rate_limiter
from .renderers import render_transformations_results_image, render_latex_to_image, render_expression_image
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
    logger.info("DEBUG: handle_task called")
    try:
        if not update.effective_user or not update.message or not update.message.text:
            logger.info("DEBUG: early return, no user/message/text")
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
        logger.info(f"DEBUG: user state on entry: {state}")
        if state:
            if state.waiting_for_user_result and hasattr(state, 'last_chosen_transformation_id'):
                logger.info("DEBUG: entering manual result check branch")
                # Проверка результата через LLM
                transformation_id = state.last_chosen_transformation_id
                selected_transformation = state.transformation_storage.get_transformation(transformation_id)
                expr = state.current_step.expression if state.current_step else ""
                user_result = update.message.text.strip()
                from core.engine import TransformationEngine
                engine = TransformationEngine()
                verification = engine.verifier.verify_transformation(
                    expr,
                    selected_transformation.description if selected_transformation else "",
                    user_result,
                    verification_type="application_verification",
                )
                state.total_free_answers += 1
                if verification.is_correct:
                    state.correct_free_answers += 1
                    await update.message.reply_text("✅ Верно! Ваш результат принят как новый исходный.")
                    state.current_step = SolutionStep(expression=user_result)
                    state.waiting_for_user_result = False
                    logger.info("DEBUG: manual result correct, moving to next step")
                    await next_step_after_result(user_id, state, update)
                else:
                    await update.message.reply_text("❌ Неверно! Теперь выберите правильный вариант из списка.")
                    logger.info("DEBUG: manual result incorrect, triggering show_variants_")
                    # Переводим в режим ожидания выбора варианта и вызываем show_variants_
                    state.waiting_for_user_result = False
                    # Генерируем/получаем варианты и показываем их
                    step_number = state.student_step_number
                    cache_key = (step_number, transformation_id)
                    if cache_key in state.result_variants_cache:
                        variants = state.result_variants_cache[cache_key]
                    else:
                        from core.engine import TransformationEngine
                        from core.gpt_client import GPTClient
                        from core.prompts import PromptManager
                        engine = TransformationEngine(GPTClient(), PromptManager())
                        variants = engine.generate_result_variants(expr, selected_transformation.description)
                        state.result_variants_cache[cache_key] = variants
                    # Показываем варианты
                    from .renderers import render_transformations_results_image
                    latex_variants = [v["expression"] for v in variants]
                    img = render_transformations_results_image([
                        type('FakeTr', (), {"preview_result": v["expression"]}) for v in variants
                    ])
                    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
                    keyboard = [[InlineKeyboardButton(str(i+1), callback_data=f"choose_variant_{transformation_id}_{i}") for i in range(len(variants))]]
                    await update.message.reply_photo(
                        photo=img,
                        caption="Выберите номер правильного результата:",
                        reply_markup=InlineKeyboardMarkup(keyboard),
                    )
                logger.info("DEBUG: return after manual result branch")
                return
            logger.info("DEBUG: state exists but not waiting_for_user_result")
        logger.info("DEBUG: main branch, new task initialization")
        # Отмечаем начало операции
        rate_limiter.start_operation(user_id)

        # СРАЗУ отправляем изображение с исходным выражением
        try:
            # Создаем изображение с исходным выражением
            expression_img = render_expression_image(cleaned_task)
            
            # Отправляем изображение с исходным выражением
            await update.message.reply_photo(
                photo=expression_img,
                caption="📝 Исходное выражение:",
            )
        except Exception as e:
            logger.error(f"Ошибка при генерации изображения с выражением: {e}")

        # Отправляем начальный статус ПОСЛЕ изображения
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
                    logger.debug(f"    {i}: {tr.description}")
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

            # Сохраняем преобразования в хранилище
            transformation_ids = user_states[user_id].transformation_storage.add_transformations(
                initial_step_id, generation_result.transformations
            )

            # Формируем текст с описаниями преобразований
            transformations_text = get_transformations_description_text(generation_result.transformations)
            
            # Сразу отправляем текст с описаниями и клавиатурой
            await update.message.reply_text(
                f"🎯 <b>Доступные преобразования:</b>\n\n{transformations_text}\n\nВыберите преобразование:",
                reply_markup=get_transformations_keyboard(transformation_ids, initial_step_id, generation_result.transformations),
                parse_mode='HTML',
            )
            
            # Удаляем статус
            if status_message:
                await status_message.delete()
            
            # Асинхронно генерируем и отправляем изображение с результатами преобразований
            # async def send_transformations_image():
            #     try:
            #         # Создаем изображение с результатами преобразований
            #         transformations_img = render_transformations_results_image(generation_result.transformations)
                    
            #         # Отправляем изображение с результатами
            #         await update.message.reply_photo(
            #             photo=transformations_img,
            #             caption="📊 Результаты преобразований:",
            #         )
            #     except Exception as e:
            #         logger.error(f"Ошибка при генерации изображения с преобразованиями: {e}")
            
            # Запускаем генерацию изображения с преобразованиями в фоне
            # import asyncio
            # asyncio.create_task(send_transformations_image())
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
    except Exception as e:
        logger.error(f"ERROR in handle_task: {e}", exc_info=True)


# --- Новый сценарий Telegram-бота ---

# Глобальный движок для LLM (можно вынести в init)
engine = TransformationEngine()

async def handle_transformation_choice(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    """Обработчик выбора преобразования (новый сценарий)."""
    if not update.callback_query:
        return
    query = update.callback_query
    if not query.from_user:
        return
    user_id = query.from_user.id
    logger.info(f"Пользователь {user_id} выбрал преобразование (новый сценарий)")
    state = user_states.get(user_id)
    if not state or not state.history:
        logger.warning(f"Нет активного состояния для пользователя {user_id}")
        await query.answer("Ошибка: начните новое решение")
        return
    try:
        callback_data = query.data
        if not callback_data or not callback_data.startswith("transform_"):
            await query.answer("Неверный формат данных")
            return
        transformation_id = callback_data.split("_")[1]
        selected_transformation = state.transformation_storage.get_transformation(transformation_id)
        if not selected_transformation:
            await query.answer("Преобразование не найдено")
            return
        # --- Новый шаг ---
        state.student_step_number += 1
        logger.info(f"student_step_number={state.student_step_number}")
        # Показываем статистику
        stats = (
            f"\n\n<b>Статистика:</b>\n"
            f"Шаг: {state.student_step_number}\n"
            f"Свободная форма: {state.correct_free_answers} из {state.total_free_answers}\n"
            f"Выбор результата: {state.correct_choice_answers} из {state.total_choice_answers}"
        )
        # Если это первый шаг — сразу показываем новые преобразования
        if state.student_step_number == 1:
            await query.message.reply_text(
                f"Вы выбрали преобразование: {selected_transformation.description}" + stats,
                parse_mode='HTML',
            )
            # ... (логика генерации новых преобразований, как раньше)
            # (оставить только генерацию новых преобразований и return)
            # ... existing code ...
            return
        # Если шаг не первый — предлагаем ввести результат вручную или посмотреть варианты
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = [
            [
                InlineKeyboardButton("✏️ Ввести результат вручную", callback_data=f"manual_result_{transformation_id}"),
                InlineKeyboardButton("👀 Посмотреть варианты ответа", callback_data=f"show_variants_{transformation_id}"),
            ]
        ]
        await query.message.reply_text(
            f"Вы выбрали преобразование: {selected_transformation.description}" + stats +
            "\n\nКакой будет результат этого преобразования?",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='HTML',
        )
        # Сохраняем в состоянии, что ждём действия пользователя
        state.waiting_for_user_result = True
        state.last_chosen_transformation_id = transformation_id
        return
    except Exception as e:
        logger.error(f"Ошибка в новом сценарии выбора преобразования: {e}")
        await query.answer("❌ Произошла ошибка")


async def _handle_transform_choice(
    query: "CallbackQuery", callback_data: str, state: UserState
) -> None:
    """Обработка выбора преобразования."""
    # Извлекаем идентификатор преобразования из callback
    try:
        transformation_id = callback_data.split("_")[1]
        selected_transformation = state.transformation_storage.get_transformation(transformation_id)
        
        if not selected_transformation:
            await query.answer("Преобразование не найдено")
            return
            
        if not selected_transformation.preview_result:
            await query.answer("Преобразование не содержит результата")
            return

        result_expression = selected_transformation.preview_result
        
    except (IndexError, Exception) as e:
        logger.error(f"Ошибка обработки данных кнопки: {e}")
        await query.answer("Неверный формат данных")
        return

    # Проверяем, что есть текущий шаг
    if not state.current_step:
        await query.answer("❌ Ошибка: нет текущего шага")
        return
        
    # НЕМЕДЛЕННО отвечаем на callback query
    await query.answer("✅ Преобразование применено!")
    
    # СРАЗУ отправляем изображение с результатом выбранного преобразования
    if query.message:
        try:
            # Создаем изображение с результатом выбранного преобразования
            result_img = render_latex_to_image(result_expression)
            
            # Отправляем изображение с результатом выбранного преобразования
            await query.message.reply_photo(
                photo=result_img,
                caption="📝 Результат выбранного преобразования:",
            )
        except Exception as e:
            logger.error(f"Ошибка при генерации изображения с результатом: {e}")
    
    # Создаем новый шаг с результатом
    new_step = SolutionStep(expression=result_expression)
    state.current_step = new_step
    
    # Добавляем шаг в историю
    step_id = state.history.add_step(
        expression=result_expression,
        chosen_transformation=selected_transformation.__dict__,
        available_transformations=[]
    ) if state.history else "current"
    
    # Асинхронно выполняем тяжелые операции
    if query.message:
        # Отправляем промежуточное сообщение
        processing_msg = await query.message.reply_text(
            f"🔧 <b>Применено преобразование:</b>\n"
            f"<i>{selected_transformation.description}</i>\n\n"
            f"📝 <b>Результат:</b>\n"
            f"<code>{result_expression}</code>\n\n"
            f"⏳ Генерирую новые преобразования...",
            parse_mode='HTML',
        )
        
        try:
            # Генерируем новые преобразования для следующего шага
            logger.info("Генерация новых преобразований для следующего шага...")
            from core.engines.transformation_generator import TransformationGenerator
            from core.gpt_client import GPTClient
            from core.prompts import PromptManager
            
            client = GPTClient()
            prompt_manager = PromptManager()
            engine = TransformationGenerator(client, prompt_manager, preview_mode=True)
            generation_result = engine.generate_transformations(new_step)
            
            # Сохраняем новые преобразования в хранилище
            new_transformation_ids = state.transformation_storage.add_transformations(
                step_id, generation_result.transformations
            )
            
            # Обновляем состояние с новыми преобразованиями
            state.available_transformations = generation_result.transformations

            # Удаляем промежуточное сообщение
            await processing_msg.delete()
            
            # Если есть новые преобразования, показываем их
            if generation_result.transformations:
                # Формируем текст с описаниями преобразований
                transformations_text = get_transformations_description_text(generation_result.transformations)
                
                # Сразу отправляем текст с описаниями и клавиатурой
                await query.message.reply_text(
                    f"🔧 <b>Применено преобразование:</b>\n"
                        f"<i>{selected_transformation.description}</i>\n\n"
                        f"📝 <b>Результат:</b>\n"
                        f"<code>{result_expression}</code>\n\n"
                        f"🎯 <b>Доступные преобразования:</b>\n\n{transformations_text}\n\nВыберите преобразование:",
                    reply_markup=get_transformations_keyboard(new_transformation_ids, step_id, generation_result.transformations),
                    parse_mode='HTML',
                )
                
                # Асинхронно генерируем и отправляем изображение с результатами преобразований
                # async def send_transformations_image():
                #     try:
                #         # Подготавливаем изображение с результатами всех преобразований
                #         transformations_img = render_transformations_results_image(generation_result.transformations)
                        
                #         # Отправляем изображение с результатами всех преобразований
                #         await query.message.reply_photo(
                #             photo=transformations_img,
                #             caption="📊 Результаты всех доступных преобразований следующего шага:",
                #         )
                #     except Exception as e:
                #         logger.error(f"Ошибка при генерации изображения с преобразованиями: {e}")
                
                # Запускаем генерацию изображения с преобразованиями в фоне
                # import asyncio
                # asyncio.create_task(send_transformations_image())
            else:
                # Если нет новых преобразований, показываем сообщение о завершении
                await query.message.reply_text(
                    f"🔧 <b>Применено преобразование:</b>\n"
                    f"<i>{selected_transformation.description}</i>\n\n"
                    f"📝 <b>Результат:</b>\n"
                    f"<code>{result_expression}</code>\n\n"
                    f"🎉 <b>Задача решена!</b>\n"
                    f"Отправьте новую задачу для продолжения.",
                    parse_mode='HTML',
                )
                
                # Асинхронно отправляем изображение с финальным результатом
                async def send_final_image():
                    try:
                        # Подготавливаем изображение с финальным результатом
                        result_img = render_latex_to_image(result_expression)
                        
                        # Отправляем изображение с финальным результатом
                        await query.message.reply_photo(
                            photo=result_img,
                            caption="🎉 Финальный результат:",
                        )
                    except Exception as e:
                        logger.error(f"Ошибка при генерации финального изображения: {e}")
                
                # Запускаем генерацию финального изображения в фоне
                # import asyncio
                # asyncio.create_task(send_final_image())
        except Exception as e:
            logger.error(f"Ошибка при генерации новых преобразований: {e}")
            # Обновляем промежуточное сообщение с ошибкой
            await processing_msg.edit_text(
                f"🔧 <b>Применено преобразование:</b>\n"
                f"<i>{selected_transformation.description}</i>\n\n"
                f"📝 <b>Результат:</b>\n"
                f"<code>{result_expression}</code>\n\n"
                f"❌ <b>Ошибка при генерации новых преобразований</b>\n"
                f"Попробуйте еще раз или отправьте новую задачу.",
                parse_mode='HTML',
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
    # НЕМЕДЛЕННО отвечаем на callback query
    await query.answer("🔄 Обновление преобразований...")
    
    if not state.current_step:
        await query.answer("❌ Ошибка: нет текущего шага")
        return
    
    # Асинхронно выполняем тяжелые операции
    if query.message:
        # Отправляем промежуточное сообщение
        processing_msg = await query.message.reply_text(
            f"⏳ Генерирую новые преобразования для:\n"
            f"<code>{state.current_step.expression}</code>",
            parse_mode='HTML',
        )
        
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
            
            # Удаляем промежуточное сообщение
            await processing_msg.delete()
            
            # Сохраняем новые преобразования в хранилище
            refresh_transformation_ids = state.transformation_storage.add_transformations(
                state.history.get_current_step().id if state.history and state.history.get_current_step() else "current",
                generation_result.transformations
            )
            
            # Формируем текст с описаниями преобразований
            transformations_text = get_transformations_description_text(generation_result.transformations)
            
            # Сразу отправляем текст с описаниями и клавиатурой
            await query.message.reply_text(
                f"🔄 <b>Обновленные преобразования для:</b>\n\n{transformations_text}\n\nВыберите преобразование:",
                reply_markup=get_transformations_keyboard(
                    refresh_transformation_ids,
                    state.history.get_current_step().id if state.history and state.history.get_current_step() else "current",
                    generation_result.transformations,
                ),
                parse_mode='HTML',
            )
            
            # Асинхронно генерируем и отправляем изображение
            # async def send_image():
            #     try:
            #         # Подготавливаем изображение с результатами преобразований
            #         transformations_img = render_transformations_results_image(generation_result.transformations)
                        
            #         # Отправляем изображение с результатами
            #         await query.message.reply_photo(
            #             photo=transformations_img,
            #             caption="📊 Результаты преобразований:",
            #         )
            #     except Exception as e:
            #         logger.error(f"Ошибка при генерации изображения: {e}")
            
            # Запускаем генерацию изображения в фоне
            # import asyncio
            # asyncio.create_task(send_image())
        except Exception as e:
            logger.error(f"Ошибка при обновлении преобразований: {e}")
            # Обновляем промежуточное сообщение с ошибкой
            await processing_msg.edit_text(
                f"❌ <b>Ошибка при обновлении преобразований</b>\n"
                f"Попробуйте еще раз или отправьте новую задачу.",
                parse_mode='HTML',
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


# --- Новый сценарий Telegram-бота (продолжение) ---

async def handle_callback_query(update: "Update", context: "ContextTypes.DEFAULT_TYPE") -> None:
    """Общий обработчик для новых callback'ов: ручной ввод результата и показ вариантов."""
    if not update.callback_query:
        return
    query = update.callback_query
    user_id = query.from_user.id
    state = user_states.get(user_id)
    if not state:
        await query.answer("Нет состояния пользователя")
        return
    data = query.data or ""
    logger.info(f"Callback: {data}")
    
    # Обработка выбора преобразования (transform_)
    if data.startswith("transform_"):
        logger.info(f"DEBUG: Обработка transform_ callback: {data}")
        transformation_id = data.split("_")[1]
        selected_transformation = state.transformation_storage.get_transformation(transformation_id)
        
        if not selected_transformation:
            await query.answer("Преобразование не найдено")
            return
            
        # Инкрементируем номер шага студента
        state.student_step_number += 1
        state.last_chosen_transformation_id = transformation_id
        
        await query.answer(f"✅ Выбрано преобразование: {selected_transformation.description}")
        
        # Для первого шага - сразу переходим к следующему этапу
        if state.student_step_number == 2:  # После инкремента первый шаг становится 2
            logger.info(f"DEBUG: Первый шаг (student_step_number=2), сразу применяем преобразование")
            # Применяем преобразование и переходим к следующему шагу
            result_expression = selected_transformation.preview_result
            new_step = SolutionStep(expression=result_expression)
            state.current_step = new_step
            await next_step_after_result(user_id, state, query)
        else:
            logger.info(f"DEBUG: Не первый шаг, показываем варианты ввода")
            # Показываем кнопки "ввести вручную" / "показать варианты"
            keyboard = [
                [
                    InlineKeyboardButton("✏️ Ввести результат вручную", callback_data=f"manual_result_{transformation_id}"),
                    InlineKeyboardButton("👀 Посмотреть варианты ответа", callback_data=f"show_variants_{transformation_id}"),
                ]
            ]
            stats = (
                f"\n\n<b>Статистика:</b>\n"
                f"Шаг: {state.student_step_number}\n"
                f"Свободная форма: {state.correct_free_answers} из {state.total_free_answers}\n"
                f"Выбор результата: {state.correct_choice_answers} из {state.total_choice_answers}"
            )
            await query.message.reply_text(
                f"🔧 <b>Выбрано преобразование:</b>\n<i>{selected_transformation.description}</i>\n\nКакой будет результат этого преобразования?" + stats,
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='HTML',
            )
        return
    
    # Ручной ввод результата
    if data.startswith("manual_result_"):
        transformation_id = data.split("_")[2]
        state.waiting_for_user_result = True
        state.last_chosen_transformation_id = transformation_id
        await query.message.reply_text(
            "Введите результат преобразования в LaTeX-формате (одной строкой):"
        )
        await query.answer()
        return
    # Показ вариантов ответа
    if data.startswith("show_variants_"):
        transformation_id = data.split("_")[2]
        step_number = state.student_step_number
        cache_key = (step_number, transformation_id)
        # Если есть кэш — используем
        if cache_key in state.result_variants_cache:
            variants = state.result_variants_cache[cache_key]
            logger.info(f"Используем кэш для вариантов результата: {cache_key}")
        else:
            # Генерируем варианты через LLM
            selected_transformation = state.transformation_storage.get_transformation(transformation_id)
            if not selected_transformation:
                await query.answer("Преобразование не найдено")
                return
            expr = state.current_step.expression if state.current_step else ""
            from core.engine import TransformationEngine
            from core.gpt_client import GPTClient
            from core.prompts import PromptManager
            engine = TransformationEngine(GPTClient(), PromptManager())
            variants = engine.generate_result_variants(expr, selected_transformation.description)
            state.result_variants_cache[cache_key] = variants
            logger.info(f"Сгенерировано {len(variants)} вариантов результата через LLM")
        # Рендерим варианты (номера на кнопках, LaTeX — картинкой)
        from .renderers import render_transformations_results_image
        from io import BytesIO
        # Формируем список выражений для картинки
        latex_variants = [v["expression"] for v in variants]
        # Картинка с вариантами
        img = render_transformations_results_image([
            type('FakeTr', (), {"preview_result": v["expression"]}) for v in variants
        ])
        # Кнопки — только номера
        keyboard = [[InlineKeyboardButton(str(i+1), callback_data=f"choose_variant_{transformation_id}_{i}") for i in range(len(variants))]]
        await query.message.reply_photo(
            photo=img,
            caption="Выберите номер правильного результата:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )
        state.waiting_for_user_result = False
        state.waiting_for_choice = (transformation_id, step_number)
        await query.answer()
        return
    # Выбор варианта
    if data.startswith("choose_variant_"):
        _, transformation_id, idx = data.split("_")
        idx = int(idx)
        step_number = state.student_step_number
        cache_key = (step_number, transformation_id)
        variants = state.result_variants_cache.get(cache_key, [])
        if not variants or idx >= len(variants):
            await query.answer("Вариант не найден")
            return
        chosen = variants[idx]
        state.total_choice_answers += 1
        if chosen.get("correctness"):
            state.correct_choice_answers += 1
            msg = "✅ Верно!"
        else:
            msg = f"❌ Неверно!\nПравильный вариант: "
            for i, v in enumerate(variants):
                if v.get("correctness"):
                    msg += f"\n{str(i+1)}: {v['expression']}"
                    break
        await query.message.reply_text(msg)
        await next_step_after_result(user_id, state, query)
        await query.answer()
        return

async def next_step_after_result(user_id: int, state: UserState, update_or_query):
    from core.engines import TransformationGenerator
    from core.gpt_client import GPTClient
    from core.prompts import PromptManager
    client = GPTClient()
    prompt_manager = PromptManager()
    engine = TransformationGenerator(client, prompt_manager, preview_mode=True)
    current_step = state.current_step
    if not current_step:
        logger.error("Нет current_step для пользователя %s", user_id)
        return
    generation_result = engine.generate_transformations(current_step)
    state.available_transformations = generation_result.transformations
    step_id = state.history.add_step(
        expression=current_step.expression,
        available_transformations=[tr.__dict__ for tr in generation_result.transformations]
    ) if state.history else "current"
    transformation_ids = state.transformation_storage.add_transformations(
        step_id, generation_result.transformations
    )
    transformations_text = get_transformations_description_text(generation_result.transformations)
    stats = (
        f"\n\n<b>Статистика:</b>\n"
        f"Шаг: {state.student_step_number}\n"
        f"Свободная форма: {state.correct_free_answers} из {state.total_free_answers}\n"
        f"Выбор результата: {state.correct_choice_answers} из {state.total_choice_answers}"
    )
    # --- Клавиатура ---
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    # После применения преобразования всегда показываем transform_ кнопки для новых преобразований
    reply_markup = get_transformations_keyboard(transformation_ids, step_id, generation_result.transformations)
    text = f"🎯 <b>Доступные преобразования:</b>\n\n{transformations_text}\n\nВыберите преобразование:" + stats
    # --- Отправка только текста и клавиатуры ---
    if hasattr(update_or_query, "message") and update_or_query.message:
        await update_or_query.message.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML',
        )
    elif hasattr(update_or_query, "reply_text"):
        await update_or_query.reply_text(
            text,
            reply_markup=reply_markup,
            parse_mode='HTML',
        )
    # --- Больше не отправляем картинку с результатами преобразований! ---

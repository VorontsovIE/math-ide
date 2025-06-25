import io
import logging
import time
from typing import Dict, Optional, List
import asyncio
from dataclasses import dataclass, field

import matplotlib.pyplot as plt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

from core.engine import TransformationEngine, SolutionStep, Transformation
from core.history import SolutionHistory

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Добавляем цветной форматтер для консоли
try:
    import coloredlogs
    coloredlogs.install(
        level='INFO',
        logger=logger,
        fmt="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )
except ImportError:
    logger.info("coloredlogs не установлен. Используется стандартное логирование.")

# Константы для защиты от превышения лимитов API
MIN_STATUS_UPDATE_INTERVAL = 2.0  # Увеличиваем минимальный интервал между обновлениями статуса (в секундах)
MAX_STATUS_UPDATES_PER_MINUTE = 20  # Уменьшаем максимальное количество обновлений статуса в минуту
PROGRESS_UPDATE_INTERVAL = 3.0  # Интервал для обновления прогресса

@dataclass
class UserState:
    """Состояние пользователя в боте."""
    history: Optional[SolutionHistory] = None
    current_step: Optional[SolutionStep] = None
    available_transformations: List[Transformation] = field(default_factory=list)
    last_status_update: float = 0.0  # Время последнего обновления статуса
    status_update_count: int = 0  # Счетчик обновлений статуса в текущей минуте
    status_reset_time: float = 0.0  # Время сброса счетчика обновлений
    current_operation_start: float = 0.0  # Время начала текущей операции

# Хранилище состояний пользователей
user_states: Dict[int, UserState] = {}

class RateLimiter:
    """Класс для управления лимитами API."""
    
    def __init__(self):
        self.global_last_update = 0.0
        self.global_update_count = 0
        self.global_reset_time = time.time()
    
    def can_update_status(self, user_id: int, force_update: bool = False) -> bool:
        """Проверяет, можно ли обновить статус для пользователя."""
        current_time = time.time()
        
        # Получаем состояние пользователя
        state = user_states.get(user_id)
        if not state:
            return True
        
        # Принудительное обновление (для важных сообщений)
        if force_update:
            return True
        
        # Проверяем минимальный интервал
        if current_time - state.last_status_update < MIN_STATUS_UPDATE_INTERVAL:
            logger.debug(f"Слишком частое обновление для пользователя {user_id}")
            return False
        
        # Сбрасываем счетчик, если прошла минута
        if current_time - state.status_reset_time >= 60:
            state.status_update_count = 0
            state.status_reset_time = current_time
        
        # Проверяем лимит обновлений в минуту
        if state.status_update_count >= MAX_STATUS_UPDATES_PER_MINUTE:
            logger.warning(f"Превышен лимит обновлений статуса для пользователя {user_id}")
            return False
        
        return True
    
    def should_show_progress(self, user_id: int) -> bool:
        """Проверяет, нужно ли показать прогресс для длительных операций."""
        current_time = time.time()
        state = user_states.get(user_id)
        
        if not state:
            return False
        
        # Показываем прогресс, если операция длится больше 3 секунд
        return current_time - state.current_operation_start >= PROGRESS_UPDATE_INTERVAL
    
    def record_status_update(self, user_id: int) -> None:
        """Записывает обновление статуса."""
        current_time = time.time()
        
        # Обновляем глобальные счетчики
        if current_time - self.global_reset_time >= 60:
            self.global_update_count = 0
            self.global_reset_time = current_time
        
        self.global_update_count += 1
        self.global_last_update = current_time
        
        # Обновляем счетчики пользователя
        state = user_states.get(user_id)
        if state:
            state.last_status_update = current_time
            state.status_update_count += 1
    
    def start_operation(self, user_id: int) -> None:
        """Отмечает начало новой операции."""
        current_time = time.time()
        state = user_states.get(user_id)
        if state:
            state.current_operation_start = current_time

# Глобальный экземпляр rate limiter
rate_limiter = RateLimiter()

def get_progress_indicator(operation_time: float) -> str:
    """Генерирует индикатор прогресса на основе времени операции."""
    if operation_time < 5:
        return "🔄"
    elif operation_time < 10:
        return "⏳"
    elif operation_time < 15:
        return "⏰"
    else:
        return "🐌"

async def send_status_message(update: Update, message: str, force_update: bool = False) -> Optional[Message]:
    """Отправляет сообщение со статусом с проверкой лимитов."""
    user_id = update.effective_user.id
    
    if not rate_limiter.can_update_status(user_id, force_update):
        logger.debug(f"Пропущено обновление статуса для пользователя {user_id} из-за лимитов")
        return None
    
    try:
        result = await update.message.reply_text(message)
        rate_limiter.record_status_update(user_id)
        return result
    except Exception as e:
        logger.error(f"Ошибка при отправке статуса: {e}")
        return None

async def edit_status_message(message: Message, new_text: str, user_id: int, force_update: bool = False) -> bool:
    """Редактирует сообщение со статусом с проверкой лимитов."""
    if not rate_limiter.can_update_status(user_id, force_update):
        logger.debug(f"Пропущено редактирование статуса для пользователя {user_id} из-за лимитов")
        return False
    
    try:
        await message.edit_text(new_text)
        rate_limiter.record_status_update(user_id)
        return True
    except Exception as e:
        logger.error(f"Ошибка при редактировании статуса: {e}")
        return False

async def update_status_with_progress(message: Message, base_text: str, user_id: int) -> bool:
    """Обновляет статус с индикатором прогресса для длительных операций."""
    if not rate_limiter.should_show_progress(user_id):
        return False
    
    current_time = time.time()
    state = user_states.get(user_id)
    if not state:
        return False
    
    operation_time = current_time - state.current_operation_start
    progress_indicator = get_progress_indicator(operation_time)
    
    # Добавляем информацию о времени выполнения
    if operation_time > 5:
        progress_text = f"{base_text}\n\n⏱️ Выполняется уже {int(operation_time)} сек..."
    else:
        progress_text = base_text
    
    return await edit_status_message(message, progress_text, user_id)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} запустил бота")
    
    # Инициализируем состояние пользователя
    user_states[user_id] = UserState()
    
    await update.message.reply_text(
        "Привет! Я помогу вам решить математическую задачу пошагово. "
        "Отправьте мне задачу в LaTeX-формате, например:\n"
        "2(x + 1) = 4"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /cancel."""
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} отменил текущее решение")
    
    user_states[user_id] = UserState()
    
    await update.message.reply_text(
        "Текущее решение отменено. Отправьте новую задачу."
    )

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /history."""
    user_id = update.effective_user.id
    logger.info(f"Пользователь {user_id} запросил историю")
    
    state = user_states.get(user_id)
    
    if not state or not state.history:
        logger.warning(f"История пуста для пользователя {user_id}")
        await update.message.reply_text("История пуста. Начните решение задачи.")
        return
    
    try:
        # Получаем сводку истории
        summary = state.history.get_full_history_summary()
        logger.info(f"Получена история решения: {len(summary['steps'])} шагов")
        
        # Отправляем каждый шаг отдельным сообщением
        for step in summary["steps"]:
            # Рендерим выражение
            img = render_latex_to_image(step["expression"])
            
            # Формируем описание шага
            description = f"Шаг {step['step_number']}"
            if step["has_chosen_transformation"]:
                description += f": {step['chosen_transformation']['description']}"
            
            await update.message.reply_photo(
                photo=img,
                caption=description
            )
            
    except Exception as e:
        logger.error(f"Ошибка при показе истории: {e}")
        await update.message.reply_text("Ошибка при получении истории решения.")

def render_latex_to_image(latex_expression: str) -> io.BytesIO:
    """Рендерит LaTeX-выражение в изображение."""
    try:
        # Создаём фигуру matplotlib
        fig, ax = plt.subplots(figsize=(10, 2))
        ax.text(0.5, 0.5, f"${latex_expression}$", 
                horizontalalignment='center', verticalalignment='center',
                fontsize=16, transform=ax.transAxes)
        ax.axis('off')
        
        # Сохраняем в BytesIO
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150)
        img_buffer.seek(0)
        plt.close(fig)
        
        return img_buffer
    except Exception as e:
        logger.error(f"Ошибка при рендеринге LaTeX: {e}")
        # Возвращаем простое текстовое изображение в случае ошибки
        fig, ax = plt.subplots(figsize=(10, 2))
        ax.text(0.5, 0.5, latex_expression, 
                horizontalalignment='center', verticalalignment='center',
                fontsize=14, transform=ax.transAxes)
        ax.axis('off')
        
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150)
        img_buffer.seek(0)
        plt.close(fig)
        
        return img_buffer

async def handle_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик новой задачи с улучшенной системой статусов."""
    user_id = update.effective_user.id
    task = update.message.text
    logger.info(f"Пользователь {user_id} отправил задачу: {task}")
    
    # Отмечаем начало операции
    rate_limiter.start_operation(user_id)
    
    # Отправляем начальный статус
    status_message = await send_status_message(update, "🔄 Анализирую задачу...", force_update=True)
    
    try:
        # Инициализируем движок и историю
        if status_message:
            await edit_status_message(status_message, "🔧 Инициализирую движок решения...", user_id)
        
        engine = TransformationEngine()
        history = SolutionHistory(task)
        current_step = SolutionStep(expression=task)
        
        # Сохраняем начальное состояние
        history.add_step(
            expression=task,
            available_transformations=[]
        )
        logger.debug("Создана новая история решения")
        
        # Генерируем возможные преобразования
        if status_message:
            await edit_status_message(status_message, "🧠 Генерирую возможные преобразования...", user_id)
        
        logger.info("Генерация возможных преобразований...")
        generation_result = engine.generate_transformations(current_step)
        logger.info(f"Сгенерировано {len(generation_result.transformations)} преобразований")
        
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
        
        img = render_latex_to_image(task)
        
        # Удаляем статус и отправляем результат
        if status_message:
            await status_message.delete()
        
        await update.message.reply_photo(
            photo=img,
            caption="Начинаем решение. Выберите преобразование:",
            reply_markup=get_transformations_keyboard(generation_result.transformations)
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

def get_transformations_keyboard(transformations: List[Transformation]) -> InlineKeyboardMarkup:
    """Создаёт клавиатуру с доступными преобразованиями."""
    keyboard = []
    for idx, tr in enumerate(transformations):
        keyboard.append([
            InlineKeyboardButton(
                f"{idx + 1}. {tr.description}",
                callback_data=f"transform_{idx}"
            )
        ])
    return InlineKeyboardMarkup(keyboard)

async def handle_transformation_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик выбора преобразования с улучшенной системой статусов."""
    query = update.callback_query
    user_id = query.from_user.id
    logger.info(f"Пользователь {user_id} выбрал преобразование")
    
    state = user_states.get(user_id)
    
    if not state or not state.current_step or not state.available_transformations:
        logger.warning(f"Нет активного состояния для пользователя {user_id}")
        await query.answer("Ошибка: начните новое решение")
        return
    
    try:
        # Получаем индекс выбранного преобразования
        idx = int(query.data.split("_")[1])
        chosen = state.available_transformations[idx]
        logger.info(f"Выбрано преобразование: {chosen.description}")
        
        # Отмечаем начало операции
        rate_limiter.start_operation(user_id)
        
        # Отправляем статус о применении преобразования
        await query.answer("🔄 Применяю преобразование...")
        
        # Применяем преобразование
        engine = TransformationEngine()
        logger.info("Применение преобразования...")
        apply_result = engine.apply_transformation(state.current_step, chosen)
        
        if apply_result.is_valid:
            logger.info("Преобразование успешно применено")
            # Обновляем историю
            if state.history:
                state.history.add_step(
                    expression=state.current_step.expression,
                    available_transformations=[tr.__dict__ for tr in state.available_transformations],
                    chosen_transformation=chosen.__dict__,
                    result_expression=apply_result.result
                )
            
            # Обновляем текущий шаг
            state.current_step = SolutionStep(expression=apply_result.result)
            
            # Проверяем завершённость
            await query.answer("🔍 Проверяю завершённость решения...")
            logger.info("Проверка завершённости решения...")
            original_task = state.history.original_task if state.history else "Неизвестная задача"
            check_result = engine.check_solution_completeness(
                state.current_step,
                original_task
            )
            
            # Отправляем результат
            img = render_latex_to_image(apply_result.result)
            if check_result.is_solved:
                logger.info("Задача решена!")
                await query.message.reply_photo(
                    photo=img,
                    caption=f"✅ Задача решена!\n{check_result.explanation}"
                )
            else:
                # Генерируем новые преобразования
                await query.answer("🧠 Генерирую новые преобразования...")
                logger.info("Генерация новых преобразований...")
                generation_result = engine.generate_transformations(state.current_step)
                state.available_transformations = generation_result.transformations
                logger.info(f"Сгенерировано {len(generation_result.transformations)} новых преобразований")
                
                # Проверяем, есть ли доступные преобразования
                if not generation_result.transformations:
                    logger.warning(f"Не найдено ни одного варианта действия для выражения: {state.current_step.expression}")
                    await query.message.reply_text(
                        f"😕 К сожалению, я не смог найти подходящих преобразований для текущего выражения:\n\n"
                        f"`{state.current_step.expression}`\n\n"
                        f"Возможные причины:\n"
                        f"• Задача уже решена или близка к решению\n"
                        f"• Нестандартный формат выражения\n"
                        f"• Требуется другой подход к решению\n\n"
                        f"Попробуйте:\n"
                        f"• Начать новое решение с другой формулировки\n"
                        f"• Использовать команду /history для просмотра прогресса\n"
                        f"• Отправить более детальное описание задачи"
                    )
                    return
                
                await query.message.reply_photo(
                    photo=img,
                    caption=f"Выберите следующее преобразование:",
                    reply_markup=get_transformations_keyboard(generation_result.transformations)
                )
        else:
            logger.error(f"Ошибка при применении преобразования: {apply_result.explanation}")
            await query.answer(f"❌ Ошибка: {apply_result.explanation}")
    except Exception as e:
        logger.error(f"Ошибка при обработке выбора преобразования: {e}")
        await query.answer("❌ Произошла ошибка при обработке преобразования")
    
    await query.answer()

def run_bot(token: str) -> None:
    """Запускает Telegram-бота."""
    logger.info("Инициализация бота...")
    try:
        # Создаём приложение
        application = Application.builder().token(token).build()
        
        # Добавляем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("cancel", cancel))
        application.add_handler(CommandHandler("history", show_history))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task))
        application.add_handler(CallbackQueryHandler(handle_transformation_choice))
        
        logger.info("Бот успешно инициализирован")
        
        # Запускаем бота
        logger.info("Запуск бота...")
        application.run_polling()
    except Exception as e:
        logger.critical(f"Критическая ошибка при запуске бота: {e}")
        raise

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    # Загружаем переменные окружения
    load_dotenv()
    
    # Получаем токен бота
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.critical("TELEGRAM_BOT_TOKEN не найден в переменных окружения")
        exit(1)
    
    logger.info("Запуск Telegram-бота...")
    run_bot(token)
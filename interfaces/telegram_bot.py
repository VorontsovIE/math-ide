import io
import logging
from typing import Dict, Optional, List
import asyncio
from dataclasses import dataclass

import matplotlib.pyplot as plt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
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

@dataclass
class UserState:
    """Состояние пользователя в боте."""
    history: Optional[SolutionHistory] = None
    current_step: Optional[SolutionStep] = None
    available_transformations: List[Transformation] = None

# Хранилище состояний пользователей
user_states: Dict[int, UserState] = {}

def render_latex_to_image(latex: str) -> io.BytesIO:
    """Рендерит LaTeX-выражение в изображение."""
    logger.debug(f"Начало рендеринга LaTeX: {latex}")
    try:
        plt.figure(figsize=(10, 1))
        plt.text(0.5, 0.5, f"${latex}$", size=14, ha='center', va='center')
        plt.axis('off')
        
        # Сохраняем в буфер
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight', dpi=300)
        plt.close()
        
        buf.seek(0)
        logger.debug("LaTeX успешно отрендерен")
        return buf
    except Exception as e:
        logger.error(f"Ошибка при рендеринге LaTeX: {e}")
        raise

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
                tr = step["chosen_transformation"]
                description += f"\nПреобразование: {tr['description']} ({tr['type']})"
            
            # Отправляем изображение с описанием
            await update.message.reply_photo(
                photo=img,
                caption=description
            )
            logger.debug(f"Отправлен шаг {step['step_number']}")
    except Exception as e:
        logger.error(f"Ошибка при отображении истории: {e}")
        await update.message.reply_text("Произошла ошибка при отображении истории.")

async def handle_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик новой задачи."""
    user_id = update.effective_user.id
    task = update.message.text
    logger.info(f"Пользователь {user_id} отправил задачу: {task}")
    
    try:
        # Инициализируем движок и историю
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
        logger.info("Генерация возможных преобразований...")
        generation_result = engine.generate_transformations(current_step)
        logger.info(f"Сгенерировано {len(generation_result.transformations)} преобразований")
        
        # Обновляем состояние пользователя
        user_states[user_id] = UserState(
            history=history,
            current_step=current_step,
            available_transformations=generation_result.transformations
        )
        
        # Отправляем текущее выражение
        img = render_latex_to_image(task)
        await update.message.reply_photo(
            photo=img,
            caption="Начинаем решение. Выберите преобразование:",
            reply_markup=get_transformations_keyboard(generation_result.transformations)
        )
        logger.info("Задача успешно инициализирована")
    except Exception as e:
        logger.error(f"Ошибка при обработке задачи: {e}")
        await update.message.reply_text(
            "Произошла ошибка при обработке задачи. "
            "Пожалуйста, проверьте корректность LaTeX-синтаксиса и попробуйте снова."
        )

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
    """Обработчик выбора преобразования."""
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
        
        # Применяем преобразование
        engine = TransformationEngine()
        logger.info("Применение преобразования...")
        apply_result = engine.apply_transformation(state.current_step, chosen)
        
        if apply_result.is_valid:
            logger.info("Преобразование успешно применено")
            # Обновляем историю
            state.history.add_step(
                expression=state.current_step.expression,
                available_transformations=[tr.__dict__ for tr in state.available_transformations],
                chosen_transformation=chosen.__dict__,
                result_expression=apply_result.result
            )
            
            # Обновляем текущий шаг
            state.current_step = SolutionStep(expression=apply_result.result)
            
            # Проверяем завершённость
            logger.info("Проверка завершённости решения...")
            check_result = engine.check_solution_completeness(
                state.current_step,
                state.history.original_task
            )
            
            # Отправляем результат
            img = render_latex_to_image(apply_result.result)
            if check_result.is_solved:
                logger.info("Задача решена!")
                await query.message.reply_photo(
                    photo=img,
                    caption=f"Задача решена!\n{check_result.explanation}"
                )
            else:
                # Генерируем новые преобразования
                logger.info("Генерация новых преобразований...")
                generation_result = engine.generate_transformations(state.current_step)
                state.available_transformations = generation_result.transformations
                logger.info(f"Сгенерировано {len(generation_result.transformations)} новых преобразований")
                
                await query.message.reply_photo(
                    photo=img,
                    caption=f"Выберите следующее преобразование:",
                    reply_markup=get_transformations_keyboard(generation_result.transformations)
                )
        else:
            logger.error(f"Ошибка при применении преобразования: {apply_result.explanation}")
            await query.answer(f"Ошибка: {apply_result.explanation}")
    except Exception as e:
        logger.error(f"Ошибка при обработке выбора преобразования: {e}")
        await query.answer("Произошла ошибка при обработке преобразования")
    
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
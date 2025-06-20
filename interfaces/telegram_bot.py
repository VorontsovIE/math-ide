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
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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
    plt.figure(figsize=(10, 1))
    plt.text(0.5, 0.5, f"${latex}$", size=14, ha='center', va='center')
    plt.axis('off')
    
    # Сохраняем в буфер
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=300)
    plt.close()
    
    buf.seek(0)
    return buf

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start."""
    user_id = update.effective_user.id
    
    # Инициализируем состояние пользователя
    user_states[user_id] = UserState()
    
    await update.message.reply_text(
        "Привет! Я помогу вам решить математическую задачу пошагово. "
        "Отправьте мне задачу в LaTeX-формате, например:\n"
        "2(x + 1) = 4"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /help."""
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
    user_states[user_id] = UserState()
    
    await update.message.reply_text(
        "Текущее решение отменено. Отправьте новую задачу."
    )

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /history."""
    user_id = update.effective_user.id
    state = user_states.get(user_id)
    
    if not state or not state.history:
        await update.message.reply_text("История пуста. Начните решение задачи.")
        return
    
    # Получаем сводку истории
    summary = state.history.get_full_history_summary()
    
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

async def handle_task(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик новой задачи."""
    user_id = update.effective_user.id
    task = update.message.text
    
    # Инициализируем движок и историю
    engine = TransformationEngine()
    history = SolutionHistory(task)
    current_step = SolutionStep(expression=task)
    
    # Сохраняем начальное состояние
    history.add_step(
        expression=task,
        available_transformations=[]
    )
    
    # Генерируем возможные преобразования
    generation_result = engine.generate_transformations(current_step)
    
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
    state = user_states.get(user_id)
    
    if not state or not state.current_step or not state.available_transformations:
        await query.answer("Ошибка: начните новое решение")
        return
    
    # Получаем индекс выбранного преобразования
    idx = int(query.data.split("_")[1])
    chosen = state.available_transformations[idx]
    
    # Применяем преобразование
    engine = TransformationEngine()
    apply_result = engine.apply_transformation(state.current_step, chosen)
    
    if apply_result.is_valid:
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
        check_result = engine.check_solution_completeness(
            state.current_step,
            state.history.original_task
        )
        
        # Отправляем результат
        img = render_latex_to_image(apply_result.result)
        if check_result.is_solved:
            await query.message.reply_photo(
                photo=img,
                caption=f"Задача решена!\n{check_result.explanation}"
            )
        else:
            # Генерируем новые преобразования
            generation_result = engine.generate_transformations(state.current_step)
            state.available_transformations = generation_result.transformations
            
            await query.message.reply_photo(
                photo=img,
                caption=f"Выберите следующее преобразование:",
                reply_markup=get_transformations_keyboard(generation_result.transformations)
            )
    else:
        await query.answer(f"Ошибка: {apply_result.explanation}")
    
    await query.answer()

def run_bot(token: str) -> None:
    """Запускает Telegram-бота."""
    # Создаём приложение
    application = Application.builder().token(token).build()
    
    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("cancel", cancel))
    application.add_handler(CommandHandler("history", show_history))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task))
    application.add_handler(CallbackQueryHandler(handle_transformation_choice))
    
    # Запускаем бота
    application.run_polling()
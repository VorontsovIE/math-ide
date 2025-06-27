"""
Модуль рендеринга LaTeX для Telegram бота.
Содержит функции для создания изображений из LaTeX выражений.
"""

import io
import logging
from typing import TYPE_CHECKING, Any, List, Optional

import matplotlib.pyplot as plt
import re

if TYPE_CHECKING:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    from core.types import Transformation

logger = logging.getLogger(__name__)

# Настройка matplotlib для корректного отображения LaTeX
plt.rcParams.update(
    {
        "text.usetex": True,
        "font.family": "serif",
        "font.serif": ["Computer Modern Roman"],
        "text.latex.preamble": r"\usepackage{amsmath} \usepackage{amssymb}",
    }
)


def contains_cyrillic(text: str) -> bool:
    """Проверяет, содержит ли текст кириллические символы."""
    cyrillic_pattern = re.compile(r'[а-яё]', re.IGNORECASE)
    return bool(cyrillic_pattern.search(text))


def extract_math_expression(text: str) -> str:
    """Извлекает математическое выражение из текста, убирая русские слова."""
    # Паттерны для поиска математических выражений
    math_patterns = [
        r'[0-9+\-*/()=<>≤≥≠±√∫∑∏∞θαβγδεζηθικλμνξοπρστυφχψω]+',  # Базовые математические символы
        r'[a-zA-Z]+[0-9+\-*/()=<>≤≥≠±√∫∑∏∞θαβγδεζηθικλμνξοπρστυφχψω]*',  # Переменные с математическими символами
        r'[0-9]+\s*[+\-*/]\s*[0-9]+',  # Простые арифметические операции
        r'[a-zA-Z]+\s*[+\-*/=]\s*[0-9a-zA-Z]+',  # Уравнения с переменными
    ]
    
    # Ищем математические выражения
    math_expressions = []
    for pattern in math_patterns:
        matches = re.findall(pattern, text)
        math_expressions.extend(matches)
    
    if math_expressions:
        # Возвращаем самое длинное найденное выражение
        return max(math_expressions, key=len)
    
    # Если ничего не найдено, возвращаем исходный текст
    return text


def fix_latex_expression(latex_expr: str) -> str:
    """Исправляет распространенные проблемы в LaTeX-выражениях."""
    # Сначала извлекаем математическое выражение
    latex_expr = extract_math_expression(latex_expr)
    
    # Удаляем лишние пробелы и переводы строк
    latex_expr = " ".join(latex_expr.split())

    # Исправляем проблему с неполными командами \\frac
    latex_expr = latex_expr.replace("\\rac{", "\\frac{")

    # Исправляем другие распространенные проблемы
    latex_expr = (
        latex_expr.replace("\\sin{", "\\sin(")
        .replace("\\cos{", "\\cos(")
        .replace("\\tan{", "\\tan(")
    )
    
    # Экранируем специальные символы, которые могут вызвать проблемы в LaTeX
    # но только если они не являются частью LaTeX команд
    import re
    
    def escape_special_chars(match):
        char = match.group(0)
        # Не экранируем символы, которые уже являются частью LaTeX команд
        if match.start() > 0 and latex_expr[match.start()-1] == '\\':
            return char
        # Экранируем специальные символы
        if char in ['_', '^', '%', '&', '#', '{', '}']:
            return f"\\{char}"
        return char
    
    # Экранируем специальные символы, но не в LaTeX командах
    latex_expr = re.sub(r'[_^%&#{}]', escape_special_chars, latex_expr)
    
    return latex_expr


def render_latex_to_image(latex_expression: str) -> io.BytesIO:
    """Рендерит LaTeX-выражение в изображение."""
    try:
        # Исправляем проблемы с LaTeX
        cleaned_expression = fix_latex_expression(latex_expression)

        # Создаём фигуру matplotlib
        fig, ax = plt.subplots(figsize=(10, 2))
        ax.text(
            0.5,
            0.5,
            f"${cleaned_expression}$",
            horizontalalignment="center",
            verticalalignment="center",
            fontsize=16,
            transform=ax.transAxes,
        )
        ax.axis("off")

        # Сохраняем в BytesIO
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format="png", bbox_inches="tight", dpi=150)
        img_buffer.seek(0)
        plt.close(fig)

        return img_buffer
    except Exception as e:
        logger.error(f"Ошибка при рендеринге LaTeX: {e}")
        # Возвращаем простое текстовое изображение в случае ошибки
        fig, ax = plt.subplots(figsize=(10, 2))
        ax.text(
            0.5,
            0.5,
            latex_expression,
            horizontalalignment="center",
            verticalalignment="center",
            fontsize=14,
            transform=ax.transAxes,
        )
        ax.axis("off")

        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format="png", bbox_inches="tight", dpi=150)
        img_buffer.seek(0)
        plt.close(fig)

        return img_buffer


def render_transformations_image(
    current_expression: str, transformations: "List[Transformation]"
) -> io.BytesIO:
    """Рендерит изображение с текущим выражением и всеми доступными преобразованиями."""
    try:
        # Вычисляем размер изображения на основе количества преобразований
        num_transformations = len(transformations)
        fig_height = (
            2 + num_transformations * 0.8
        )  # Базовая высота + высота для каждого преобразования

        fig, ax = plt.subplots(figsize=(12, fig_height))
        ax.axis("off")

        # Отображаем текущее выражение вверху
        ax.text(
            0.5,
            0.95,
            "Current expression:",
            horizontalalignment="center",
            verticalalignment="top",
            fontsize=14,
            fontweight="bold",
            transform=ax.transAxes,
        )

        # Отображаем математическое выражение как обычный текст (НЕ LaTeX)
        ax.text(
            0.5,
            0.88,
            current_expression,
            horizontalalignment="center",
            verticalalignment="top",
            fontsize=16,
            transform=ax.transAxes,
            usetex=False,
        )

        # Добавляем разделительную линию
        ax.axhline(
            y=0.82,
            xmin=0.1,
            xmax=0.9,
            color="gray",
            linestyle="-",
            alpha=0.5,
        )

        # Отображаем доступные преобразования
        ax.text(
            0.5,
            0.78,
            "Available actions:",
            horizontalalignment="center",
            verticalalignment="top",
            fontsize=14,
            fontweight="bold",
            transform=ax.transAxes,
        )

        # Отображаем каждое преобразование
        start_y = 0.72
        for idx, tr in enumerate(transformations):
            y_pos = start_y - idx * 0.12

            # Номер и описание преобразования
            ax.text(
                0.05,
                y_pos,
                f"{idx + 1}.",
                horizontalalignment="left",
                verticalalignment="center",
                fontsize=12,
                fontweight="bold",
                transform=ax.transAxes,
            )

            # Отображаем описание как обычный текст (НЕ LaTeX)
            description_text = tr.description
            ax.text(
                0.1,
                y_pos,
                description_text,
                horizontalalignment="left",
                verticalalignment="center",
                fontsize=12,
                transform=ax.transAxes,
            )

            # Стрелка
            ax.text(
                0.75,
                y_pos,
                "→",
                horizontalalignment="center",
                verticalalignment="center",
                fontsize=14,
                fontweight="bold",
                transform=ax.transAxes,
            )

            # Предварительный результат - отображаем как обычный текст
            if tr.preview_result:
                ax.text(
                    0.8,
                    y_pos,
                    tr.preview_result,
                    horizontalalignment="left",
                    verticalalignment="center",
                    fontsize=11,
                    transform=ax.transAxes,
                    usetex=False,
                )

        # Сохраняем в BytesIO
        img_buffer = io.BytesIO()
        plt.savefig(
            img_buffer, format="png", bbox_inches="tight", dpi=150, facecolor="white"
        )
        img_buffer.seek(0)
        plt.close(fig)

        return img_buffer

    except Exception as e:
        logger.error(f"Ошибка при рендеринге изображения с преобразованиями: {e}", exc_info=True)
        # Возвращаем простое изображение с текстом
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(
            0.5,
            0.5,
            f"Current expression:\n{current_expression}\n\nAvailable {len(transformations)} transformations",
            horizontalalignment="center",
            verticalalignment="center",
            fontsize=12,
            transform=ax.transAxes,
            usetex=False,
        )
        ax.axis("off")

        img_buffer = io.BytesIO()
        plt.savefig(
            img_buffer, format="png", bbox_inches="tight", dpi=150, facecolor="white"
        )
        img_buffer.seek(0)
        plt.close(fig)

        return img_buffer


async def check_and_suggest_rollback(
    engine: Any,
    state: Any,
    update_or_query: Any,
    caption: str,
    new_step_id: Optional[str] = None,
) -> bool:
    """
    Проверяет прогресс и при необходимости предлагает мягкую рекомендацию возврата к прошлому шагу.

    Returns:
        True если была отправлена рекомендация возврата, False в противном случае
    """
    try:
        # Проверяем, что есть история и достаточно шагов для анализа
        if not state.history or len(state.history.steps) < 4:
            return False

        # Подготавливаем данные для анализа
        original_task = state.history.original_task
        current_step = state.current_step.expression if state.current_step else ""
        steps_count = len(state.history.steps)

        # Преобразуем шаги истории в нужный формат
        history_steps = []
        for step in state.history.steps:
            step_data = {
                "expression": step.expression,
                "chosen_transformation": step.chosen_transformation,
            }
            history_steps.append(step_data)

        # Анализируем прогресс
        logger.info("Анализ прогресса для возможной рекомендации возврата")
        progress_result = engine.analyze_progress(
            original_task=original_task,
            history_steps=history_steps,
            current_step=current_step,
            steps_count=steps_count,
        )

        # Если рекомендуется откат и есть сообщение для пользователя
        if (
            progress_result.recommend_rollback
            and progress_result.suggestion_message
            and progress_result.recommended_step is not None
        ):

            logger.info(
                f"Отправка рекомендации возврата к шагу {progress_result.recommended_step}"
            )

            # Создаем кнопки для рекомендации
            rollback_keyboard = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            f"🔙 Вернуться к шагу {progress_result.recommended_step}",
                            callback_data=f"rollback_{progress_result.recommended_step}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "➡️ Продолжить текущий путь",
                            callback_data="continue_current",
                        )
                    ],
                ]
            )

            # Отправляем рекомендацию
            suggestion_text = (
                f"🤔 **Рекомендация:**\n\n{progress_result.suggestion_message}"
            )

            if hasattr(update_or_query, "message"):
                # Это query
                await update_or_query.message.reply_text(
                    suggestion_text,
                    reply_markup=rollback_keyboard,
                    parse_mode="Markdown",
                )
            else:
                # Это update
                await update_or_query.message.reply_text(
                    suggestion_text,
                    reply_markup=rollback_keyboard,
                    parse_mode="Markdown",
                )

            return True

    except Exception as e:
        logger.error(f"Ошибка при анализе прогресса: {e}")

    return False

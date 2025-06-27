"""
Модуль рендеринга LaTeX для Telegram бота.
Содержит функции для создания изображений из LaTeX выражений.
"""

import io
import logging
from typing import TYPE_CHECKING, Any, List, Optional

import matplotlib.pyplot as plt

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


def fix_latex_expression(latex_expr: str) -> str:
    """Исправляет распространенные проблемы в LaTeX-выражениях."""
    # Удаляем лишние пробелы и переводы строк
    latex_expr = " ".join(latex_expr.split())

    # Исправляем проблему с неполными командами \frac
    latex_expr = latex_expr.replace("\\rac{", "\\frac{")

    # Исправляем другие распространенные проблемы
    latex_expr = (
        latex_expr.replace("\\sin{", "\\sin(")
        .replace("\\cos{", "\\cos(")
        .replace("\\tan{", "\\tan(")
    )

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

        # Исправляем LaTeX в текущем выражении
        cleaned_current = fix_latex_expression(current_expression)

        # Отображаем текущее выражение вверху
        ax.text(
            0.5,
            0.95,
            "Текущее выражение:",
            horizontalalignment="center",
            verticalalignment="top",
            fontsize=14,
            fontweight="bold",
            transform=ax.transAxes,
        )

        ax.text(
            0.5,
            0.88,
            f"${cleaned_current}$",
            horizontalalignment="center",
            verticalalignment="top",
            fontsize=16,
            transform=ax.transAxes,
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
            "Доступные действия:",
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

            ax.text(
                0.1,
                y_pos,
                tr.description,
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

            # Предварительный результат
            if tr.preview_result:
                cleaned_preview = fix_latex_expression(tr.preview_result)
                try:
                    ax.text(
                        0.8,
                        y_pos,
                        f"${cleaned_preview}$",
                        horizontalalignment="left",
                        verticalalignment="center",
                        fontsize=11,
                        transform=ax.transAxes,
                    )
                except Exception:
                    # Если LaTeX не рендерится, показываем как текст
                    ax.text(
                        0.8,
                        y_pos,
                        cleaned_preview,
                        horizontalalignment="left",
                        verticalalignment="center",
                        fontsize=11,
                        transform=ax.transAxes,
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
        logger.error(f"Ошибка при рендеринге изображения с преобразованиями: {e}")
        # Возвращаем простое изображение с текстом
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.text(
            0.5,
            0.5,
            f"Текущее выражение:\n{current_expression}\n\nДоступно {len(transformations)} преобразований",
            horizontalalignment="center",
            verticalalignment="center",
            fontsize=12,
            transform=ax.transAxes,
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

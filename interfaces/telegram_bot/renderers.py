"""
Модуль рендеринга LaTeX для Telegram бота.
Содержит функции для создания изображений из LaTeX выражений.
"""

import io
import logging
from typing import TYPE_CHECKING, Any, List, Optional

import matplotlib.pyplot as plt
import matplotlib.offsetbox as offsetbox
import re

if TYPE_CHECKING:
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup

    from core.types import Transformation

logger = logging.getLogger(__name__)

# Настройка matplotlib для корректного отображения LaTeX
custom_preamble = {
    "text.usetex": True,
    "font.family": "serif",
    "font.serif": ["Computer Modern Roman"],
    "text.latex.preamble": r"\usepackage{amsmath} \usepackage{amssymb} \renewcommand{\familydefault}{\rmdefault}",
}
plt.rcParams.update(custom_preamble)


def contains_cyrillic(text: str) -> bool:
    """Проверяет, содержит ли текст кириллические символы."""
    cyrillic_pattern = re.compile(r'[а-яё]', re.IGNORECASE)
    return bool(cyrillic_pattern.search(text))


def extract_math_expression(text: str) -> str:
    """Очищает и нормализует математическое выражение."""
    
    # Убираем пробелы по краям
    result = text.strip()
    
    # Преобразуем надстрочные/подстрочные символы
    result = convert_superscript_subscript_to_latex(result)
    
    return result


def convert_superscript_subscript_to_latex(text: str) -> str:
    """Преобразует надстрочные и подстрочные символы в LaTeX формат."""
    
    # Словарь для преобразования надстрочных символов
    superscript_map = {
        '²': '^2', '³': '^3', '⁴': '^4', '⁵': '^5', '⁶': '^6',
        '⁷': '^7', '⁸': '^8', '⁹': '^9', '⁰': '^0', '¹': '^1'
    }
    
    # Словарь для преобразования подстрочных символов
    subscript_map = {
        '₂': '_2', '₃': '_3', '₄': '_4', '₅': '_5', '₆': '_6',
        '₇': '_7', '₈': '_8', '₉': '_9', '₀': '_0', '₁': '_1'
    }
    
    # Преобразуем надстрочные символы
    for sup_char, latex_char in superscript_map.items():
        text = text.replace(sup_char, latex_char)
    
    # Преобразуем подстрочные символы
    for sub_char, latex_char in subscript_map.items():
        text = text.replace(sub_char, latex_char)
    
    # Обрабатываем последовательные надстрочные/подстрочные символы
    # Например: ³² → ^{32}
    text = re.sub(r'\^(\d+)\^(\d+)', r'^{\1\2}', text)
    text = re.sub(r'_(\d+)_(\d+)', r'_{\1\2}', text)
    
    return text


def fix_latex_expression(latex_expr: str) -> str:
    """
    Исправляет LaTeX-выражение для корректного рендеринга.
    """
    # Заменяем русские слова на английские эквиваленты
    replacements = {
        'или': '\\text{ or }',
        'и': '\\text{ and }',
        'равно': '=',
        'плюс': '+',
        'минус': '-',
        'умножить': '\\times',
        'делить': '\\div',
        'корень': '\\sqrt',
        'степень': '^',
        'дробь': '\\frac',
        'квадрат': '^2',
        'куб': '^3',
    }
    
    result = latex_expr
    for russian, english in replacements.items():
        # Используем replace только один раз для каждого слова
        result = result.replace(russian, english, 1)
    
    return result


def render_latex_to_image(latex_expression: str) -> io.BytesIO:
    """Рендерит LaTeX-выражение в изображение."""
    logger.info(f"Начало рендеринга LaTeX: '{latex_expression}'")
    
    try:
        # Исправляем проблемы с LaTeX
        logger.info("Применяем fix_latex_expression...")
        cleaned_expression = fix_latex_expression(latex_expression)
        logger.info(f"Очищенное выражение: '{cleaned_expression}'")

        # Создаём фигуру matplotlib
        logger.info("Создаём matplotlib фигуру...")
        fig, ax = plt.subplots(figsize=(10, 2))
        
        display_text = f"${cleaned_expression}$"
        logger.info(f"Текст для отображения: '{display_text}'")
        
        ax.text(
            0.5,
            0.5,
            display_text,
            horizontalalignment="center",
            verticalalignment="center",
            fontsize=16,
            transform=ax.transAxes,
            usetex=True,
        )
        ax.axis("off")
        plt.tight_layout(pad=0.1)

        # Сохраняем в BytesIO
        logger.info("Сохраняем изображение...")
        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format="png", bbox_inches="tight", pad_inches=0.05, dpi=150)
        img_buffer.seek(0)
        plt.close(fig)
        
        logger.info("Рендеринг LaTeX успешно завершён")
        return img_buffer
        
    except Exception as e:
        logger.error(f"Ошибка при рендеринге LaTeX: {e}", exc_info=True)
        logger.info("Пробуем создать простое текстовое изображение...")
        
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
        plt.tight_layout(pad=0.1)

        img_buffer = io.BytesIO()
        plt.savefig(img_buffer, format="png", bbox_inches="tight", pad_inches=0.05, dpi=150)
        img_buffer.seek(0)
        plt.close(fig)
        
        logger.info("Создано простое текстовое изображение")
        return img_buffer


def render_expression_image(current_expression: str) -> io.BytesIO:
    """Рендерит изображение только с текущим выражением."""
    try:
        # Создаём фигуру matplotlib
        expression_fig, expression_ax = plt.subplots(figsize=(8, 1.5))  # Немного уменьшаем высоту
        expression_ax.axis("off")
        
        # Используем offsetbox для корректного рендеринга LaTeX
        latex_expression = f"${current_expression}$"
        logger.info(f"Рендеринг изображения с выражением: {repr(latex_expression)}")
        ob = offsetbox.AnchoredText(latex_expression, loc='center', prop=dict(size=16))
        ob.patch.set(alpha=0.0)  # Прозрачный фон
        expression_ax.add_artist(ob)
        
        plt.tight_layout(pad=0.05)  # Уменьшаем отступы

        # Сохраняем изображение с меньшими отступами
        expression_buffer = io.BytesIO()
        plt.savefig(
            expression_buffer, 
            format="png", 
            bbox_inches="tight", 
            pad_inches=0.03,  # Уменьшаем отступы
            dpi=150, 
            facecolor="white"
        )
        expression_buffer.seek(0)
        plt.close(expression_fig)

        return expression_buffer

    except Exception as e:
        logger.error(f"Ошибка при рендеринге изображения выражения: {e}", exc_info=True)
        
        # Создаём простое изображение в случае ошибки
        error_fig, error_ax = plt.subplots(figsize=(8, 1.5))
        
        # Используем offsetbox для корректного рендеринга LaTeX
        latex_expression = f"${current_expression}$"
        ob = offsetbox.AnchoredText(latex_expression, loc='center', prop=dict(size=14))
        ob.patch.set(alpha=0.0)  # Прозрачный фон
        error_ax.add_artist(ob)
        
        error_ax.axis("off")
        plt.tight_layout(pad=0.05)

        error_buffer = io.BytesIO()
        plt.savefig(error_buffer, format="png", bbox_inches="tight", pad_inches=0.03, dpi=150, facecolor="white")
        error_buffer.seek(0)
        plt.close(error_fig)

        return error_buffer


def render_transformations_image(transformations: "List[Transformation]") -> io.BytesIO:
    """Рендерит изображение только с доступными преобразованиями."""
    try:
        # Создаем изображение с преобразованиями
        num_transformations = len(transformations)
        # Уменьшаем высоту, так как теперь все в одной формуле
        fig_height = 1.0 + num_transformations * 0.3

        transformations_fig, transformations_ax = plt.subplots(figsize=(8, fig_height))
        transformations_ax.axis("off")
        plt.tight_layout(pad=0.05)  # Уменьшаем отступы

        # Создаем единую многострочную LaTeX-формулу с нумерацией
        if transformations:
            # Собираем все преобразования в одну формулу
            latex_lines = []
            for idx, tr in enumerate(transformations):
                if tr.preview_result:
                    # Применяем fix_latex_expression для замены русских слов
                    logger.info(f"Исходное преобразование {idx + 1}: {repr(tr.preview_result)}")
                    fixed_result = fix_latex_expression(tr.preview_result)
                    logger.info(f"Исправленное преобразование {idx + 1}: {repr(fixed_result)}")
                    # Для первой строки добавляем \\hspace{-1.25em} чтобы убрать отступ
                    if idx == 0:
                        latex_lines.append(f"\\hspace{{-1.25em}}({idx + 1}) \\quad {fixed_result}")
                    else:
                        latex_lines.append(f"({idx + 1}) \\quad {fixed_result}")
            
            if latex_lines:
                # Создаем простой список строк вместо окружения align*
                latex_formula = " \\\\[1.5em] ".join(latex_lines)
                
                # Логгируем формулу для отладки
                logger.info(f"Создана LaTeX-формула для преобразований:")
                logger.info(f"Количество строк: {len(latex_lines)}")
                logger.info(f"Строки: {latex_lines}")
                logger.info(f"Финальная формула: {repr(latex_formula)}")
                
                # Проверяем на кириллицу после применения fix_latex_expression
                has_cyrillic = any(contains_cyrillic(fix_latex_expression(tr.preview_result)) for tr in transformations if tr.preview_result)
                logger.info(f"Содержит кириллицу: {has_cyrillic}")
                
                if not has_cyrillic:
                    # Используем обычный text для простых LaTeX-формул
                    logger.info("Используем ax.text для рендеринга простой формулы")
                    transformations_ax.text(
                        0.5,  # Возвращаем в центр
                        0.5,
                        f"${latex_formula}$",  # Возвращаем $...$ для простых формул
                        horizontalalignment="center",  # Возвращаем центрирование
                        verticalalignment="center",
                        fontsize=12,
                        transform=transformations_ax.transAxes,
                        usetex=True,
                    )
                else:
                    # Для текста с кириллицей используем обычный текст
                    logger.info("Используем обычный текст (есть кириллица)")
                    transformations_ax.text(
                        0.5,  # Возвращаем в центр
                        0.5,
                        latex_formula,
                        horizontalalignment="center",  # Возвращаем центрирование
                        verticalalignment="center",
                        fontsize=12,
                        transform=transformations_ax.transAxes,
                        usetex=False,
                    )
            else:
                # Если нет преобразований с результатами
                transformations_ax.text(
                    0.5,
                    0.5,
                    "Нет доступных преобразований",
                    horizontalalignment="center",
                    verticalalignment="center",
                    fontsize=12,
                    transform=transformations_ax.transAxes,
                )
        else:
            # Если нет преобразований вообще
            transformations_ax.text(
                0.5,
                0.5,
                "Нет доступных преобразований",
                horizontalalignment="center",
                verticalalignment="center",
                fontsize=12,
                transform=transformations_ax.transAxes,
            )

        # Сохраняем изображение с меньшими отступами
        transformations_buffer = io.BytesIO()
        plt.savefig(
            transformations_buffer, 
            format="png", 
            bbox_inches="tight", 
            pad_inches=0.03,  # Уменьшаем отступы
            dpi=150, 
            facecolor="white"
        )
        transformations_buffer.seek(0)
        plt.close(transformations_fig)

        return transformations_buffer

    except Exception as e:
        logger.error(f"Ошибка при рендеринге изображения преобразований: {e}", exc_info=True)
        
        # Создаём простое изображение в случае ошибки
        num_transformations = len(transformations)
        fig_height = 1.0 + num_transformations * 0.3

        error_fig, error_ax = plt.subplots(figsize=(8, fig_height))
        error_ax.axis("off")
        plt.tight_layout(pad=0.05)

        # Создаем единую многострочную LaTeX-формулу с нумерацией
        if transformations:
            # Собираем все преобразования в одну формулу
            latex_lines = []
            for idx, tr in enumerate(transformations):
                if tr.preview_result:
                    # Применяем fix_latex_expression для замены русских слов
                    logger.info(f"Исходное преобразование {idx + 1}: {repr(tr.preview_result)}")
                    fixed_result = fix_latex_expression(tr.preview_result)
                    logger.info(f"Исправленное преобразование {idx + 1}: {repr(fixed_result)}")
                    # Добавляем \\quad для всех строк для единообразия
                    latex_lines.append(f"({idx + 1}) \\quad {fixed_result}")
            
            if latex_lines:
                # Создаем простой список строк вместо окружения align*
                latex_formula = " \\\\[1.5em] ".join(latex_lines)
                
                # Логгируем формулу для отладки
                logger.info(f"Создана LaTeX-формула для преобразований:")
                logger.info(f"Количество строк: {len(latex_lines)}")
                logger.info(f"Строки: {latex_lines}")
                logger.info(f"Финальная формула: {repr(latex_formula)}")
                
                # Проверяем на кириллицу после применения fix_latex_expression
                has_cyrillic = any(contains_cyrillic(fix_latex_expression(tr.preview_result)) for tr in transformations if tr.preview_result)
                logger.info(f"Содержит кириллицу: {has_cyrillic}")
                
                if not has_cyrillic:
                    # Используем обычный text для простых LaTeX-формул
                    logger.info("Используем ax.text для рендеринга простой формулы")
                    error_ax.text(
                        0.5,  # Возвращаем в центр
                        0.5,
                        f"${latex_formula}$",  # Возвращаем $...$ для простых формул
                        horizontalalignment="center",  # Возвращаем центрирование
                        verticalalignment="center",
                        fontsize=12,
                        transform=error_ax.transAxes,
                        usetex=True,
                    )
                else:
                    # Для текста с кириллицей используем обычный текст
                    logger.info("Используем обычный текст (есть кириллица)")
                    error_ax.text(
                        0.5,  # Возвращаем в центр
                        0.5,
                        latex_formula,
                        horizontalalignment="center",  # Возвращаем центрирование
                        verticalalignment="center",
                        fontsize=12,
                        transform=error_ax.transAxes,
                        usetex=False,
                    )
            else:
                # Если нет преобразований с результатами
                error_ax.text(
                    0.5,
                    0.5,
                    "Нет доступных преобразований",
                    horizontalalignment="center",
                    verticalalignment="center",
                    fontsize=12,
                    transform=error_ax.transAxes,
                )
        else:
            # Если нет преобразований вообще
            error_ax.text(
                0.5,
                0.5,
                "Нет доступных преобразований",
                horizontalalignment="center",
                verticalalignment="center",
                fontsize=12,
                transform=error_ax.transAxes,
            )

        error_buffer = io.BytesIO()
        plt.savefig(error_buffer, format="png", bbox_inches="tight", pad_inches=0.03, dpi=150, facecolor="white")
        error_buffer.seek(0)
        plt.close(error_fig)

        return error_buffer


def render_transformations_images(
    current_expression: str, transformations: "List[Transformation]"
) -> tuple[io.BytesIO, io.BytesIO]:
    """Рендерит два изображения: одно с текущим выражением, другое с преобразованиями."""
    # Используем новые отдельные функции
    expression_buffer = render_expression_image(current_expression)
    transformations_buffer = render_transformations_image(transformations)
    
    return expression_buffer, transformations_buffer


def render_transformations_results_image(
    transformations: "List[Transformation]"
) -> io.BytesIO:
    """Рендерит изображение только с результатами преобразований (без описаний)."""
    try:
        # Создаем изображение с результатами преобразований
        num_transformations = len(transformations)
        fig_height = 1.0 + num_transformations * 0.3

        fig, ax = plt.subplots(figsize=(8, fig_height))
        ax.axis("off")
        plt.tight_layout(pad=0.05)

        # Создаем единую многострочную LaTeX-формулу с нумерацией
        if transformations:
            # Собираем все преобразования в одну формулу
            latex_lines = []
            for idx, tr in enumerate(transformations):
                if tr.preview_result:
                    # Применяем fix_latex_expression для замены русских слов
                    logger.info(f"Исходное преобразование {idx + 1}: {repr(tr.preview_result)}")
                    fixed_result = fix_latex_expression(tr.preview_result)
                    logger.info(f"Исправленное преобразование {idx + 1}: {repr(fixed_result)}")
                    # Для первой строки добавляем \\hspace{-1.25em} чтобы убрать отступ
                    if idx == 0:
                        latex_lines.append(f"\\hspace{{-1.25em}}({idx + 1}) \\quad {fixed_result}")
                    else:
                        latex_lines.append(f"({idx + 1}) \\quad {fixed_result}")
            
            if latex_lines:
                # Создаем простой список строк вместо окружения align*
                latex_formula = " \\\\[1.5em] ".join(latex_lines)
                
                # Логгируем формулу для отладки
                logger.info(f"Создана LaTeX-формула для преобразований:")
                logger.info(f"Количество строк: {len(latex_lines)}")
                logger.info(f"Строки: {latex_lines}")
                logger.info(f"Финальная формула: {repr(latex_formula)}")
                
                # Проверяем на кириллицу после применения fix_latex_expression
                has_cyrillic = any(contains_cyrillic(fix_latex_expression(tr.preview_result)) for tr in transformations if tr.preview_result)
                logger.info(f"Содержит кириллицу: {has_cyrillic}")
                
                if not has_cyrillic:
                    # Используем обычный text для простых LaTeX-формул
                    logger.info("Используем ax.text для рендеринга простой формулы")
                    ax.text(
                        0.5,  # Возвращаем в центр
                        0.5,
                        f"${latex_formula}$",  # Возвращаем $...$ для простых формул
                        horizontalalignment="center",  # Возвращаем центрирование
                        verticalalignment="center",
                        fontsize=12,
                        transform=ax.transAxes,
                        usetex=True,
                    )
                else:
                    # Для текста с кириллицей используем обычный текст
                    logger.info("Используем обычный текст (есть кириллица)")
                    ax.text(
                        0.5,  # Возвращаем в центр
                        0.5,
                        latex_formula,
                        horizontalalignment="center",  # Возвращаем центрирование
                        verticalalignment="center",
                        fontsize=12,
                        transform=ax.transAxes,
                        usetex=False,
                    )
            else:
                # Если нет преобразований с результатами
                ax.text(
                    0.5,
                    0.5,
                    "Нет доступных преобразований",
                    horizontalalignment="center",
                    verticalalignment="center",
                    fontsize=12,
                    transform=ax.transAxes,
                )
        else:
            # Если нет преобразований вообще
            ax.text(
                0.5,
                0.5,
                "Нет доступных преобразований",
                horizontalalignment="center",
                verticalalignment="center",
                fontsize=12,
                transform=ax.transAxes,
            )

        # Сохраняем изображение с меньшими отступами
        buffer = io.BytesIO()
        plt.savefig(
            buffer, 
            format="png", 
            bbox_inches="tight", 
            pad_inches=0.03,  # Уменьшаем отступы
            dpi=150, 
            facecolor="white"
        )
        buffer.seek(0)
        plt.close(fig)

        return buffer

    except Exception as e:
        logger.error(f"Ошибка при рендеринге изображения результатов: {e}", exc_info=True)
        
        # Создаём простое изображение в случае ошибки
        error_fig, error_ax = plt.subplots(figsize=(8, 2))
        error_ax.axis("off")
        plt.tight_layout(pad=0.05)

        error_ax.text(
            0.5,
            0.5,
            "Ошибка при рендеринге результатов",
            horizontalalignment="center",
            verticalalignment="center",
            fontsize=12,
            transform=error_ax.transAxes,
        )

        error_buffer = io.BytesIO()
        plt.savefig(error_buffer, format="png", bbox_inches="tight", pad_inches=0.03, dpi=150, facecolor="white")
        error_buffer.seek(0)
        plt.close(error_fig)

        return error_buffer

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

"""
Утилиты для настройки логирования.
Содержит функции для настройки цветного логирования и форматирования.
"""

import logging
import sys


def setup_logging(level: str = "INFO", use_colors: bool = True) -> None:
    """
    Настраивает логирование для приложения.
    
    Args:
        level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
        use_colors: Использовать цветное логирование
    """
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
        level=getattr(logging, level.upper())
    )
    
    if use_colors:
        try:
            import coloredlogs
            coloredlogs.install(
                level=level.upper(),
                fmt="%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
            )
        except ImportError:
            logging.getLogger(__name__).info("coloredlogs не установлен. Используется стандартное логирование.")


def get_logger(name: str) -> logging.Logger:
    """
    Создает логгер с заданным именем.
    
    Args:
        name: Имя логгера
        
    Returns:
        Настроенный логгер
    """
    return logging.getLogger(name)

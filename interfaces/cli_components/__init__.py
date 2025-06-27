"""
Пакет cli_components содержит специализированные компоненты для CLI интерфейса.
Каждый компонент отвечает за свою область:
- LatexRenderer: рендеринг LaTeX в терминале
- InputHandler: обработка пользовательского ввода и запрос параметров
- DisplayManager: отображение таблиц, преобразований и истории
- SolutionProcessor: основной цикл решения задач
"""

from .latex_renderer import LatexRenderer
from .input_handler import InputHandler
from .display_manager import DisplayManager
from .solution_processor import SolutionProcessor

__all__ = ["LatexRenderer", "InputHandler", "DisplayManager", "SolutionProcessor"]

"""
Пакет engines содержит специализированные компоненты для обработки математических преобразований.
Каждый компонент отвечает за свою область:
- TransformationGenerator: генерация преобразований (включая готовые результаты)
- SolutionChecker: проверка завершённости решения
- ProgressAnalyzer: анализ прогресса решения
- TransformationVerifier: верификация преобразований
"""

from .progress_analyzer import ProgressAnalyzer
from .solution_checker import SolutionChecker
from .transformation_generator import TransformationGenerator
from .transformation_verifier import TransformationVerifier

__all__ = [
    "TransformationGenerator",
    "SolutionChecker",
    "ProgressAnalyzer",
    "TransformationVerifier",
]

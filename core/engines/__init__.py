"""
Пакет engines содержит специализированные компоненты для обработки математических преобразований.
Каждый компонент отвечает за свою область:
- TransformationGenerator: генерация преобразований
- TransformationApplier: применение преобразований
- SolutionChecker: проверка завершённости решения
- ProgressAnalyzer: анализ прогресса решения
- TransformationVerifier: верификация преобразований
- BranchingAnalyzer: анализ ветвящихся решений
"""

from .branching_analyzer import BranchingAnalyzer
from .progress_analyzer import ProgressAnalyzer
from .solution_checker import SolutionChecker
from .transformation_applier import TransformationApplier
from .transformation_generator import TransformationGenerator
from .transformation_verifier import TransformationVerifier

__all__ = [
    "TransformationGenerator",
    "TransformationApplier",
    "SolutionChecker",
    "ProgressAnalyzer",
    "TransformationVerifier",
    "BranchingAnalyzer",
]

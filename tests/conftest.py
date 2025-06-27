"""
Конфигурация pytest для тестов MathIDE.
"""

import sys
from pathlib import Path

# Добавляем корневую директорию в sys.path для импорта модулей
sys.path.insert(0, str(Path(__file__).parent.parent))

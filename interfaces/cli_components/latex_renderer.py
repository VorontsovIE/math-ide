from rich.text import Text


class LatexRenderer:
    """
    Компонент для рендеринга LaTeX-выражений в терминале.
    Конвертирует основные LaTeX-команды в Unicode-символы.
    """
    
    def __init__(self):
        # Словарь замен LaTeX-команд на Unicode-символы
        self.replacements = {
            r'\times': '×',
            r'\div': '÷',
            r'\pm': '±',
            r'\mp': '∓',
            r'\leq': '≤',
            r'\geq': '≥',
            r'\neq': '≠',
            r'\approx': '≈',
            r'\equiv': '≡',
            r'\sum': '∑',
            r'\prod': '∏',
            r'\int': '∫',
            r'\infty': '∞',
            r'\alpha': 'α',
            r'\beta': 'β',
            r'\gamma': 'γ',
            r'\delta': 'δ',
            r'\epsilon': 'ε',
            r'\theta': 'θ',
            r'\lambda': 'λ',
            r'\mu': 'μ',
            r'\pi': 'π',
            r'\sigma': 'σ',
            r'\omega': 'ω',
            r'\sqrt': '√',
            r'\frac': '/',  # Упрощённое представление дроби
            r'\left': '',   # Игнорируем команды для скобок
            r'\right': '',
            r'\cdot': '·',
            r'\partial': '∂',
            r'\nabla': '∇',
            r'\in': '∈',
            r'\notin': '∉',
            r'\subset': '⊂',
            r'\supset': '⊃',
            r'\cup': '∪',
            r'\cap': '∩',
            r'\forall': '∀',
            r'\exists': '∃',
            r'\neg': '¬',
            r'\wedge': '∧',
            r'\vee': '∨',
        }

    def render_latex(self, latex: str) -> Text:
        """
        Рендерит LaTeX-выражение в формате, подходящем для терминала.
        
        Args:
            latex: LaTeX-выражение для рендеринга
            
        Returns:
            Стилизованный текст для отображения в терминале
        """
        result = latex
        
        # Применяем замены LaTeX-команд на Unicode-символы
        for tex_command, unicode_symbol in self.replacements.items():
            result = result.replace(tex_command, unicode_symbol)
        
        # Удаляем оставшиеся LaTeX-команды и фигурные скобки
        result = result.replace('{', '').replace('}', '')
        
        # Создаём стилизованный текст
        return Text(result, style="bold blue")

    def render_plain(self, latex: str) -> str:
        """
        Рендерит LaTeX-выражение в простой текстовый формат без стилизации.
        
        Args:
            latex: LaTeX-выражение для рендеринга
            
        Returns:
            Обычная строка с Unicode-символами
        """
        result = latex
        
        # Применяем замены LaTeX-команд на Unicode-символы
        for tex_command, unicode_symbol in self.replacements.items():
            result = result.replace(tex_command, unicode_symbol)
        
        # Удаляем оставшиеся LaTeX-команды и фигурные скобки
        result = result.replace('{', '').replace('}', '')
        
        return result 
import click
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.text import Text

from core.engine import TransformationEngine, SolutionStep, Transformation
from core.history import SolutionHistory

console = Console()

def render_latex(latex: str) -> Text:
    """
    Рендерит LaTeX-выражение в формате, подходящем для терминала.
    Использует Unicode-символы для базовых математических операций.
    """
    # Заменяем базовые LaTeX-команды на Unicode-символы
    replacements = {
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
    
    result = latex
    for tex, unicode in replacements.items():
        result = result.replace(tex, unicode)
    
    # Удаляем оставшиеся LaTeX-команды и фигурные скобки
    result = result.replace('{', '').replace('}', '')
    
    # Создаём стилизованный текст
    return Text(result, style="bold blue")


class MathIDECLI:
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo", preview_mode: bool = False):
        self.engine = TransformationEngine(api_key=api_key, model=model, preview_mode=preview_mode)
        self.history: Optional[SolutionHistory] = None
        
    def display_transformations(self, transformations: list[Transformation]) -> None:
        """Отображает список доступных преобразований."""
        table = Table(title="Доступные преобразования")
        table.add_column("№", justify="right", style="cyan")
        table.add_column("Описание", style="green")
        table.add_column("Тип", style="blue")
        table.add_column("Выражение", style="magenta")
        
        # Добавляем колонку для предварительного результата, если он есть у хотя бы одного преобразования
        has_previews = any(tr.preview_result is not None for tr in transformations)
        if has_previews:
            table.add_column("Результат", style="yellow")
        
        for idx, tr in enumerate(transformations, 1):
            row = [
                str(idx),
                tr.description,
                tr.type,
                render_latex(tr.expression)
            ]
            
            # Добавляем предварительный результат, если он есть
            if has_previews:
                if tr.preview_result:
                    row.append(render_latex(tr.preview_result))
                else:
                    row.append("-")
            
            table.add_row(*row)
        
        console.print(table)
    
    def display_history(self) -> None:
        """Отображает историю решения."""
        if not self.history:
            return
            
        summary = self.history.get_full_history_summary()
        table = Table(title="История решения")
        table.add_column("Шаг", justify="right", style="cyan")
        table.add_column("Выражение", style="green")
        table.add_column("Преобразование", style="blue")
        table.add_column("Результат", style="magenta")
        
        for step in summary["steps"]:
            transformation = "-"
            if step["has_chosen_transformation"]:
                tr = step["chosen_transformation"]
                transformation = f"{tr['description']} ({tr['type']})"
            
            result = step["result_expression"] if step["has_result"] else "-"
            
            table.add_row(
                str(step["step_number"]),
                render_latex(step["expression"]),
                transformation,
                render_latex(result) if result != "-" else result
            )
        
        console.print(table)
    
    def solve_task(self, task: str) -> None:
        """Основной процесс решения задачи."""
        self.history = SolutionHistory(task)
        current_step = SolutionStep(expression=task)
        
        # Добавляем начальный шаг
        self.history.add_step(
            expression=task,
            available_transformations=[]
        )
        
        while True:
            # Генерируем возможные преобразования
            generation_result = self.engine.generate_transformations(current_step)
            
            # Отображаем текущее состояние
            console.print(Panel.fit(
                render_latex(current_step.expression),
                title="Текущее выражение",
                border_style="green"
            ))
            
            # Отображаем доступные преобразования
            self.display_transformations(generation_result.transformations)
            
            # Запрашиваем выбор пользователя
            choice = click.prompt(
                "Выберите преобразование (номер) или введите 'h' для истории, 'q' для выхода",
                type=str
            )
            
            if choice.lower() == 'q':
                break
            elif choice.lower() == 'h':
                self.display_history()
                continue
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(generation_result.transformations):
                    chosen = generation_result.transformations[idx]
                    
                    # Применяем преобразование
                    apply_result = self.engine.apply_transformation(current_step, chosen)
                    
                    if apply_result.is_valid:
                        # Обновляем текущий шаг
                        self.history.add_step(
                            expression=current_step.expression,
                            available_transformations=[tr.__dict__ for tr in generation_result.transformations],
                            chosen_transformation=chosen.__dict__,
                            result_expression=apply_result.result
                        )
                        
                        current_step = SolutionStep(expression=apply_result.result)
                        console.print(Panel.fit(
                            f"[green]Применено успешно![/green]\n{apply_result.explanation}\n\nРезультат:\n{render_latex(apply_result.result)}",
                            border_style="green"
                        ))
                        
                        # Проверяем завершённость
                        check_result = self.engine.check_solution_completeness(current_step, self.history.original_task)
                        if check_result.is_solved:
                            console.print(Panel.fit(
                                f"[green]Задача решена![/green]\n{check_result.explanation}\n\nИтоговый результат:\n{render_latex(current_step.expression)}",
                                border_style="green"
                            ))
                            break
                    else:
                        console.print(Panel.fit(
                            f"[red]Ошибка:[/red] {apply_result.explanation}",
                            border_style="red"
                        ))
                else:
                    console.print("[red]Неверный номер преобразования[/red]")
            except ValueError:
                console.print("[red]Неверный ввод[/red]")


@click.command()
@click.option('--api-key', envvar='OPENAI_API_KEY', help='OpenAI API ключ')
@click.option('--model', default='gpt-3.5-turbo', help='Модель GPT для использования')
@click.option('--preview/--no-preview', default=False, help='Включить режим предпоказа результатов')
def main(api_key: Optional[str], model: str, preview: bool):
    """Интерактивная математическая IDE с поддержкой пошагового решения задач."""
    cli = MathIDECLI(api_key=api_key, model=model, preview_mode=preview)
    
    if preview:
        console.print("[yellow]Режим предпоказа включен - будут показаны результаты преобразований[/yellow]")
    
    task = click.prompt("Введите математическую задачу", type=str)
    cli.solve_task(task)


if __name__ == '__main__':
    main()
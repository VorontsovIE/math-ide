from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.types import (
    SolutionStep, 
    Transformation, 
    SolutionType, 
    SolutionBranch
)
from core.history import SolutionHistory
from .latex_renderer import LatexRenderer

console = Console()


class DisplayManager:
    """
    Компонент для отображения информации в CLI интерфейсе.
    Управляет отображением преобразований, истории и состояния решения.
    """
    
    def __init__(self):
        self.latex_renderer = LatexRenderer()
    
    def display_transformations(self, transformations: list[Transformation]) -> None:
        """Отображает список доступных преобразований."""
        table = Table(title="Доступные преобразования")
        table.add_column("№", justify="right", style="cyan")
        table.add_column("Описание", style="green")
        table.add_column("Тип", style="blue")
        table.add_column("Выражение", style="magenta")
        table.add_column("Параметры", style="yellow")
        
        # Добавляем колонку для предварительного результата, если он есть у хотя бы одного преобразования
        has_previews = any(tr.preview_result is not None for tr in transformations)
        if has_previews:
            table.add_column("Результат", style="yellow")
        
        for idx, tr in enumerate(transformations, 1):
            # Определяем статус параметров
            params_status = "-"
            if tr.requires_user_input and tr.parameter_definitions:
                params_status = f"Требуется {len(tr.parameter_definitions)} параметр(ов)"
            elif tr.parameters:
                params_status = f"Заполнено {len(tr.parameters)} параметр(ов)"
            
            row = [
                str(idx),
                tr.description,
                tr.type,
                self.latex_renderer.render_latex(tr.expression),
                params_status
            ]
            
            # Добавляем предварительный результат, если он есть
            if has_previews:
                if tr.preview_result:
                    row.append(self.latex_renderer.render_latex(tr.preview_result))
                else:
                    row.append("-")
            
            table.add_row(*row)
        
        console.print(table)
    
    def display_branching_step(self, step: SolutionStep) -> None:
        """Отображает ветвящийся шаг решения."""
        if step.solution_type == SolutionType.SINGLE:
            # Обычное отображение для одиночного шага
            console.print(Panel.fit(
                self.latex_renderer.render_latex(step.expression),
                title="Текущее выражение",
                border_style="green"
            ))
            return
        
        # Отображение ветвящегося решения
        type_descriptions = {
            SolutionType.SYSTEM: "Система уравнений/неравенств",
            SolutionType.CASES: "Разбор случаев", 
            SolutionType.ALTERNATIVES: "Альтернативные методы решения",
            SolutionType.UNION: "Объединение решений",
            SolutionType.INTERSECTION: "Пересечение решений"
        }
        
        title = type_descriptions.get(step.solution_type, "Ветвящееся решение")
        
        console.print(Panel.fit(
            step.expression,
            title=title,
            border_style="blue"
        ))
        
        # Создаем таблицу для ветвей
        table = Table(title="Ветви решения")
        table.add_column("№", justify="right", style="cyan")
        table.add_column("Название", style="green")
        table.add_column("Выражение", style="magenta")
        if any(branch.condition for branch in step.branches):
            table.add_column("Условие", style="yellow")
        
        for idx, branch in enumerate(step.branches, 1):
            row = [
                str(idx),
                branch.name,
                self.latex_renderer.render_latex(branch.expression)
            ]
            
            if any(b.condition for b in step.branches):
                row.append(branch.condition or "-")
            
            table.add_row(*row)
        
        console.print(table)
    
    def display_history(self, history: SolutionHistory) -> None:
        """Отображает историю решения."""
        if not history:
            return
            
        summary = history.get_full_history_summary()
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
                self.latex_renderer.render_latex(step["expression"]),
                transformation,
                self.latex_renderer.render_latex(result) if result != "-" else result
            )
        
        console.print(table)
    
    def display_interactive_history(self, history: SolutionHistory) -> Optional[int]:
        """
        Отображает интерактивную историю с возможностью возврата к произвольному шагу.
        
        Args:
            history: История решения
            
        Returns:
            Номер шага для возврата или None если возврат не нужен
        """
        if not history or history.is_empty():
            console.print("[yellow]История пуста[/yellow]")
            return None
        
        if not history.can_rollback():
            console.print("[yellow]Недостаточно шагов для возврата[/yellow]") 
            return None
        
        summary = history.get_full_history_summary()
        
        # Отображаем историю с номерами для возврата
        table = Table(title="История решения (интерактивная)")
        table.add_column("№ для возврата", justify="right", style="cyan", width=12)
        table.add_column("Шаг", justify="right", style="cyan")
        table.add_column("Выражение", style="green")
        table.add_column("Преобразование", style="blue")
        table.add_column("Результат", style="magenta")
        table.add_column("Статус", style="white")
        
        current_step_number = len(summary["steps"]) - 1
        
        for idx, step in enumerate(summary["steps"]):
            transformation = "-"
            if step["has_chosen_transformation"]:
                tr = step["chosen_transformation"]
                transformation = f"{tr['description']} ({tr['type']})"
            
            result = step["result_expression"] if step["has_result"] else "-"
            
            # Определяем статус шага
            if idx == current_step_number:
                status = "[bold green]← Текущий[/bold green]"
            elif idx < current_step_number:
                status = "Можно вернуться"
            else:
                status = "Будущий"
            
            # Номер для возврата (только для прошлых шагов)
            rollback_num = str(idx) if idx < current_step_number else "-"
            
            table.add_row(
                rollback_num,
                str(step["step_number"]),
                self.latex_renderer.render_latex(step["expression"]),
                transformation,
                self.latex_renderer.render_latex(result) if result != "-" else result,
                status
            )
        
        console.print(table)
        return None  # Возвращаем None, так как сама логика обработки ввода вынесена отдельно
    
    def display_success_message(self, message: str, result: str = None) -> None:
        """Отображает сообщение об успехе."""
        content = f"[green]{message}[/green]"
        if result:
            content += f"\n\nРезультат:\n{self.latex_renderer.render_latex(result)}"
        
        console.print(Panel.fit(
            content,
            border_style="green"
        ))
    
    def display_error_message(self, message: str) -> None:
        """Отображает сообщение об ошибке."""
        console.print(Panel.fit(
            f"[red]Ошибка:[/red] {message}",
            border_style="red"
        ))
    
    def display_warning_message(self, message: str) -> None:
        """Отображает предупреждение."""
        console.print(f"[yellow]{message}[/yellow]")
    
    def display_info_message(self, message: str) -> None:
        """Отображает информационное сообщение."""
        console.print(f"[cyan]{message}[/cyan]")
    
    def display_solution_complete(self, explanation: str, result: str) -> None:
        """Отображает сообщение о завершении решения."""
        console.print(Panel.fit(
            f"[green]Задача решена![/green]\n{explanation}\n\nИтоговый результат:\n{self.latex_renderer.render_latex(result)}",
            border_style="green"
        )) 
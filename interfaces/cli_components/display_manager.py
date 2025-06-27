"""
Модуль для отображения информации в CLI интерфейсе.
Содержит функции для красивого вывода математических выражений и преобразований.
"""

from typing import Any, List, Optional, cast

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.history import SolutionHistory
from core.types import SolutionStep, SolutionType, Transformation

from .latex_renderer import LatexRenderer


class DisplayManager:
    """
    Менеджер отображения для CLI.
    Отвечает за красивый вывод различных типов информации.
    """

    def __init__(
        self,
        console: Optional[Console] = None,
        latex_renderer: Optional[LatexRenderer] = None,
    ) -> None:
        self.console = console or Console()
        self.latex_renderer = latex_renderer or LatexRenderer()

    def display_transformations(self, transformations: List[Transformation]) -> None:
        """Отображает список доступных преобразований."""
        if not transformations:
            self.console.print("[yellow]Нет доступных преобразований[/yellow]")
            return

        table = Table(title="Доступные преобразования")
        table.add_column("№", justify="right", style="cyan")
        table.add_column("Описание", style="green")
        table.add_column("Тип", style="blue")
        table.add_column("Выражение", style="magenta")
        table.add_column("Параметры", style="yellow")

        for idx, transformation in enumerate(transformations, 1):
            # Формируем строку параметров
            params_str = "-"
            if transformation.parameter_definitions:
                param_names = [
                    param.name for param in transformation.parameter_definitions
                ]
                params_str = ", ".join(param_names)

            # Добавляем строку в таблицу
            row = [
                str(idx),
                transformation.description,
                transformation.type,
                self.latex_renderer.render_latex(transformation.expression),
                params_str,
            ]
            table.add_row(*cast(List[Any], row))

        self.console.print(table)

    def display_branching_step(self, step: SolutionStep) -> None:
        """Отображает ветвящийся шаг решения."""
        if step.solution_type == SolutionType.SINGLE:
            # Обычное отображение для одиночного шага
            self.console.print(
                Panel.fit(
                    self.latex_renderer.render_latex(step.expression),
                    title="Текущее выражение",
                    border_style="green",
                )
            )
            return

        # Отображение ветвящегося решения
        type_descriptions = {
            SolutionType.SYSTEM: "Система уравнений/неравенств",
            SolutionType.CASES: "Разбор случаев",
            SolutionType.ALTERNATIVES: "Альтернативные методы решения",
            SolutionType.UNION: "Объединение решений",
            SolutionType.INTERSECTION: "Пересечение решений",
        }

        title = type_descriptions.get(step.solution_type, "Ветвящееся решение")

        self.console.print(Panel.fit(step.expression, title=title, border_style="blue"))

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
                self.latex_renderer.render_latex(branch.expression),
            ]

            if any(b.condition for b in step.branches):
                row.append(branch.condition or "-")

            table.add_row(*cast(List[Any], row))

        self.console.print(table)

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
                self.latex_renderer.render_latex(result) if result != "-" else result,
            )

        self.console.print(table)

    def display_interactive_history(self, history: SolutionHistory) -> Optional[int]:
        """
        Отображает интерактивную историю с возможностью возврата к произвольному шагу.

        Args:
            history: История решения

        Returns:
            Номер шага для возврата или None если возврат не нужен
        """
        if not history or history.is_empty():
            self.console.print("[yellow]История пуста[/yellow]")
            return None

        if not history.can_rollback():
            self.console.print("[yellow]Недостаточно шагов для возврата[/yellow]")
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
                status,
            )

        self.console.print(table)
        return None  # Возвращаем None, так как сама логика обработки ввода вынесена отдельно

    def display_success_message(
        self, message: str, result: Optional[str] = None
    ) -> None:
        """Отображает сообщение об успехе."""
        content = f"[green]{message}[/green]"
        if result:
            content += f"\n\nРезультат:\n{self.latex_renderer.render_latex(result)}"

        self.console.print(Panel.fit(content, border_style="green"))

    def display_error_message(self, message: str) -> None:
        """Отображает сообщение об ошибке."""
        self.console.print(
            Panel.fit(f"[red]Ошибка:[/red] {message}", border_style="red")
        )

    def display_warning_message(self, message: str) -> None:
        """Отображает предупреждение."""
        self.console.print(f"[yellow]{message}[/yellow]")

    def display_info_message(self, message: str) -> None:
        """Отображает информационное сообщение."""
        self.console.print(f"[cyan]{message}[/cyan]")

    def display_solution_complete(self, explanation: str, result: str) -> None:
        """Отображает сообщение о завершении решения."""
        content = (
            f"[green]Задача решена![/green]\n{explanation}\n\n"
            f"Итоговый результат:\n{self.latex_renderer.render_latex(result)}"
        )
        self.console.print(
            Panel.fit(
                content,
                border_style="green",
            )
        )

    def show_welcome(self) -> None:
        """Show welcome message."""
        self.console.print(
            Panel.fit(
                "[bold blue]Math IDE - Интерактивный решатель математических задач[/bold blue]\n"
                "Система пошагового решения с поддержкой ветвящихся решений и "
                "параметризованных трансформаций",
                border_style="blue",
            )
        )

    def show_problem(self, problem: str) -> None:
        """Show the problem to be solved."""
        self.console.print("\n[bold green]Задача:[/bold green]")
        self.console.print(
            Panel(self.latex_renderer.render_plain(problem), border_style="green")
        )

    def show_completion_message(self) -> None:
        """Show completion message when problem is solved."""
        self.console.print("\n[bold green]🎉 Задача решена![/bold green]")
        self.console.print("[green]Все необходимые преобразования выполнены.[/green]")

    def show_error(self, message: str) -> None:
        """Show error message."""
        self.console.print(f"\n[bold red]Ошибка:[/bold red] {message}")

    def show_info(self, message: str) -> None:
        """Show info message."""
        self.console.print(f"\n[cyan]{message}[/cyan]")

    def show_transformations(self, transformations: List[Transformation]) -> None:
        """Show available transformations."""
        if not transformations:
            self.console.print("[yellow]Нет доступных преобразований[/yellow]")
            return

        table = Table(title="Доступные преобразования")
        table.add_column("№", justify="right", style="cyan")
        table.add_column("Описание", style="green")
        table.add_column("Тип", style="blue")
        table.add_column("Выражение", style="magenta")

        for idx, transformation in enumerate(transformations, 1):
            table.add_row(
                str(idx),
                transformation.description,
                transformation.type,
                self.latex_renderer.render_latex(transformation.expression),
            )

        self.console.print(table)

    def show_branching_analysis(self, analysis: Any) -> None:
        """Show branching analysis results."""
        self.console.print("[blue]Анализ ветвления завершён[/blue]")
        # Дополнительная логика отображения результатов анализа

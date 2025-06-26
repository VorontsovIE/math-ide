import click
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.text import Text

from core.engine import TransformationEngine
from core.history import SolutionHistory
from core.types import (
    SolutionStep, 
    Transformation, 
    SolutionType, 
    SolutionBranch,
    ParameterDefinition,
    ParameterType
)

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
                render_latex(tr.expression),
                params_status
            ]
            
            # Добавляем предварительный результат, если он есть
            if has_previews:
                if tr.preview_result:
                    row.append(render_latex(tr.preview_result))
                else:
                    row.append("-")
            
            table.add_row(*row)
        
        console.print(table)
    
    def request_parameter_value(self, param_def: ParameterDefinition) -> str:
        """
        Запрашивает значение параметра у пользователя.
        
        Args:
            param_def: Определение параметра
            
        Returns:
            Введенное пользователем значение
        """
        # Формируем заголовок запроса
        console.print(Panel.fit(
            f"[bold]Параметр: {param_def.name}[/bold]\n{param_def.prompt}",
            title="Ввод параметра",
            border_style="cyan"
        ))
        
        # Показываем дополнительную информацию, если есть
        info_lines = []
        if param_def.param_type:
            info_lines.append(f"Тип: {param_def.param_type.value}")
        
        if param_def.default_value is not None:
            info_lines.append(f"По умолчанию: {param_def.default_value}")
        
        if param_def.suggested_values:
            info_lines.append(f"Предлагаемые значения: {', '.join(map(str, param_def.suggested_values))}")
        
        if param_def.validation_rule:
            info_lines.append(f"Правило валидации: {param_def.validation_rule}")
        
        if info_lines:
            console.print(Panel.fit(
                "\n".join(info_lines),
                title="Дополнительная информация",
                border_style="yellow"
            ))
        
        # Обрабатываем разные типы параметров
        if param_def.param_type == ParameterType.CHOICE and param_def.options:
            # Для выбора из вариантов показываем пронумерованный список
            table = Table(title="Выберите вариант")
            table.add_column("№", justify="right", style="cyan")
            table.add_column("Значение", style="green")
            
            for idx, option in enumerate(param_def.options, 1):
                table.add_row(str(idx), str(option))
            
            console.print(table)
            
            while True:
                try:
                    choice = click.prompt("Выберите номер варианта", type=int)
                    if 1 <= choice <= len(param_def.options):
                        return str(param_def.options[choice - 1])
                    else:
                        console.print(f"[red]Выберите номер от 1 до {len(param_def.options)}[/red]")
                except (ValueError, click.Abort):
                    console.print("[red]Введите корректный номер[/red]")
        
        else:
            # Для остальных типов - простой ввод текста
            prompt_text = f"Введите значение для {param_def.name}"
            if param_def.default_value is not None:
                prompt_text += f" (по умолчанию: {param_def.default_value})"
            
            try:
                value = click.prompt(prompt_text, default=param_def.default_value)
                return str(value)
            except click.Abort:
                # Если пользователь отменил ввод, используем значение по умолчанию
                if param_def.default_value is not None:
                    console.print(f"[yellow]Используется значение по умолчанию: {param_def.default_value}[/yellow]")
                    return str(param_def.default_value)
                else:
                    raise click.ClickException("Отменен ввод параметра без значения по умолчанию")
    
    def display_branching_step(self, step: SolutionStep) -> None:
        """Отображает ветвящийся шаг решения."""
        if step.solution_type == SolutionType.SINGLE:
            # Обычное отображение для одиночного шага
            console.print(Panel.fit(
                render_latex(step.expression),
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
                render_latex(branch.expression)
            ]
            
            if any(b.condition for b in step.branches):
                row.append(branch.condition or "-")
            
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
    
    def display_interactive_history(self) -> Optional[int]:
        """
        Отображает интерактивную историю с возможностью возврата к произвольному шагу.
        
        Returns:
            Номер шага для возврата или None если возврат не нужен
        """
        if not self.history or self.history.is_empty():
            console.print("[yellow]История пуста[/yellow]")
            return None
        
        if not self.history.can_rollback():
            console.print("[yellow]Недостаточно шагов для возврата[/yellow]") 
            return None
        
        summary = self.history.get_full_history_summary()
        
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
                render_latex(step["expression"]),
                transformation,
                render_latex(result) if result != "-" else result,
                status
            )
        
        console.print(table)
        
        # Запрашиваем у пользователя выбор
        max_rollback_step = current_step_number - 1
        if max_rollback_step < 0:
            console.print("[yellow]Нет доступных шагов для возврата[/yellow]")
            return None
        
        console.print(f"\n[cyan]Доступные команды:[/cyan]")
        console.print(f"• Введите номер шага (0-{max_rollback_step}) для возврата")
        console.print(f"• 'c' - отменить возврат и продолжить")
        console.print(f"• 'q' - выйти из программы")
        
        while True:
            try:
                choice = click.prompt("Ваш выбор", type=str).strip().lower()
                
                if choice == 'c':
                    return None
                elif choice == 'q':
                    return -1  # Специальное значение для выхода
                else:
                    step_num = int(choice)
                    if 0 <= step_num <= max_rollback_step:
                        return step_num
                    else:
                        console.print(f"[red]Введите номер от 0 до {max_rollback_step}[/red]")
            except ValueError:
                console.print("[red]Введите корректный номер шага, 'c' или 'q'[/red]")
            except click.Abort:
                return None
    
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
            # Анализируем на предмет ветвящихся решений
            analyzed_step = self.engine.analyze_branching_solution(current_step)
            
            # Отображаем текущее состояние (с учетом ветвления)
            self.display_branching_step(analyzed_step)
            
            # Если есть ветвящееся решение, предлагаем пользователю выбрать ветвь
            if analyzed_step.solution_type != SolutionType.SINGLE:
                choice = click.prompt(
                    "Выберите ветвь для продолжения (номер), 'a' для анализа всех ветвей, 'h' для истории, 'r' для возврата к шагу, 'q' для выхода",
                    type=str
                )
                
                if choice.lower() == 'q':
                    break
                elif choice.lower() == 'h':
                    self.display_history()
                    continue
                elif choice.lower() == 'r':
                    # Интерактивный возврат к произвольному шагу
                    rollback_step = self.display_interactive_history()
                    if rollback_step == -1:  # Выход из программы
                        break
                    elif rollback_step is not None:
                        # Выполняем возврат
                        if self.history.rollback_to_step(rollback_step):
                            console.print(f"[green]Возврат к шагу {rollback_step} выполнен успешно![/green]")
                            # Обновляем текущий шаг на основе истории
                            current_step = SolutionStep(expression=self.history.get_current_expression())
                        else:
                            console.print(f"[red]Ошибка возврата к шагу {rollback_step}[/red]")
                    continue
                elif choice.lower() == 'a':
                    console.print("[yellow]Анализ всех ветвей пока не реализован[/yellow]")
                    continue
                
                try:
                    branch_idx = int(choice) - 1
                    if 0 <= branch_idx < len(analyzed_step.branches):
                        chosen_branch = analyzed_step.branches[branch_idx]
                        current_step = SolutionStep(expression=chosen_branch.expression)
                        console.print(f"[green]Выбрана ветвь: {chosen_branch.name}[/green]")
                        
                        # Добавляем в историю
                        self.history.add_step(
                            expression=analyzed_step.expression,
                            available_transformations=[],
                            chosen_transformation={
                                "description": f"Выбрана ветвь: {chosen_branch.name}",
                                "type": "branch_selection",
                                "expression": chosen_branch.expression
                            },
                            result_expression=chosen_branch.expression
                        )
                        continue
                    else:
                        console.print("[red]Неверный номер ветви[/red]")
                        continue
                except ValueError:
                    console.print("[red]Введите корректный номер ветви[/red]")
                    continue
            
            # Обычный процесс для одиночных шагов
            # Генерируем возможные преобразования
            generation_result = self.engine.generate_transformations(current_step)
            
            # Отображаем доступные преобразования
            self.display_transformations(generation_result.transformations)
            
            # Запрашиваем выбор пользователя
            choice = click.prompt(
                "Выберите преобразование (номер) или введите 'h' для истории, 'r' для возврата к шагу, 'q' для выхода",
                type=str
            )
            
            if choice.lower() == 'q':
                break
            elif choice.lower() == 'h':
                self.display_history()
                continue
            elif choice.lower() == 'r':
                # Интерактивный возврат к произвольному шагу
                rollback_step = self.display_interactive_history()
                if rollback_step == -1:  # Выход из программы
                    break
                elif rollback_step is not None:
                    # Выполняем возврат
                    if self.history.rollback_to_step(rollback_step):
                        console.print(f"[green]Возврат к шагу {rollback_step} выполнен успешно![/green]")
                        # Обновляем текущий шаг на основе истории
                        current_step = SolutionStep(expression=self.history.get_current_expression())
                    else:
                        console.print(f"[red]Ошибка возврата к шагу {rollback_step}[/red]")
                continue
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(generation_result.transformations):
                    chosen = generation_result.transformations[idx]
                    
                    # Проверяем, требует ли преобразование параметры
                    if chosen.requires_user_input and chosen.parameter_definitions:
                        console.print("[cyan]Это преобразование требует дополнительных параметров.[/cyan]")
                        try:
                            # Запрашиваем параметры у пользователя
                            chosen = self.engine.request_parameters(chosen, self.request_parameter_value)
                            console.print("[green]Параметры успешно заполнены![/green]")
                        except Exception as e:
                            console.print(f"[red]Ошибка при заполнении параметров: {str(e)}[/red]")
                            continue
                    
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
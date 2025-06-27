"""Command Line Interface for Math IDE."""

import click
from typing import Optional
from rich.console import Console
from rich.panel import Panel

from core.engines import (
    TransformationGenerator,
    TransformationApplier,
    SolutionChecker,
)
from core.types import SolutionStep, SolutionType
from core.history import SolutionHistory
from core.gpt_client import GPTClient
from core.prompts import PromptManager

from .cli_components.display_manager import DisplayManager
from .cli_components.input_handler import InputHandler
from .cli_components.latex_renderer import LatexRenderer
from .cli_components.solution_processor import SolutionProcessor

console = Console()


@click.group()
def cli() -> None:
    """Math IDE - Интерактивная система решения математических задач."""
    pass


@cli.command()
@click.argument("problem")
@click.option(
    "--model", default="gpt-4o-mini", help="GPT model to use (default: gpt-4o-mini)"
)
@click.option("--debug", is_flag=True, help="Enable debug mode")
def solve(problem: str, model: str, debug: bool) -> None:
    """Solve a mathematical problem interactively."""
    try:
        # Initialize components
        gpt_client = GPTClient(model=model)
        prompt_manager = PromptManager()

        # Initialize engines
        transformation_generator = TransformationGenerator(gpt_client, prompt_manager)
        transformation_applier = TransformationApplier(gpt_client, prompt_manager)
        solution_checker = SolutionChecker(gpt_client, prompt_manager)

        history = SolutionHistory(problem)

        latex_renderer = LatexRenderer()
        display_manager = DisplayManager(console, latex_renderer)
        input_handler = InputHandler(console)
        solution_processor = SolutionProcessor(
            transformation_generator,
            transformation_applier,
            solution_checker,
            history,
            input_handler,
            display_manager,
        )

        display_manager.show_welcome()
        display_manager.show_problem(problem)

        # Main solving loop
        current_problem = problem
        while True:
            try:
                # Check if solved
                is_solved = solution_checker.check_solution_completeness(
                    current_problem, problem
                )
                if is_solved.is_solved:
                    display_manager.show_completion_message()
                    break

                # Generate transformations
                transformations = transformation_generator.generate_transformations(
                    current_problem
                )
                if not transformations or not transformations.transformations:
                    display_manager.show_error("Не удалось сгенерировать трансформации")
                    break

                # Show available transformations
                display_manager.show_transformations(transformations.transformations)

                # Get user choice
                choice = input_handler.get_user_choice(
                    "Выберите преобразование (номер): ",
                    [str(i + 1) for i in range(len(transformations.transformations))],
                )

                if not choice:
                    break

                try:
                    choice_index = int(choice) - 1
                    if 0 <= choice_index < len(transformations.transformations):
                        selected_transformation = transformations.transformations[
                            choice_index
                        ]
                    else:
                        display_manager.show_error("Неверный номер преобразования")
                        continue
                except ValueError:
                    display_manager.show_error("Введите число")
                    continue

                # Apply transformation
                current_step = SolutionStep(
                    expression=current_problem, solution_type=SolutionType.SINGLE
                )
                result = transformation_applier.apply_transformation(
                    current_step, selected_transformation
                )
                if not result or not result.is_valid:
                    display_manager.show_error("Не удалось применить преобразование")
                    continue

                # Add step to history
                history.add_step(
                    expression=current_problem,
                    available_transformations=[
                        t.__dict__ for t in transformations.transformations
                    ],
                    chosen_transformation=selected_transformation.__dict__,
                    result_expression=result.result,
                )

                # Show step result
                display_manager.display_success_message(
                    f"Применено: {selected_transformation.description}", result.result
                )

                # Update current problem
                current_problem = result.result

                # Ask user what to do next
                action = input_handler.get_user_choice(
                    "Выберите действие (1-4): ", ["1", "2", "3", "4"]
                )

                if action == "1":
                    continue
                elif action == "2":
                    solution_processor.show_solution_summary()
                    if not input_handler.confirm_action("Продолжить решение?"):
                        break
                elif action == "3":
                    if solution_processor.handle_rollback():
                        steps = history.get_steps()
                        if steps:
                            current_problem = steps[-1].expression
                        else:
                            current_problem = problem
                else:
                    break

            except KeyboardInterrupt:
                display_manager.show_info("\nПрерывание пользователем")
                if input_handler.confirm_action(
                    "Показать текущее решение перед выходом?"
                ):
                    solution_processor.show_solution_summary()
                break
            except Exception as e:
                if debug:
                    display_manager.show_error(f"Неожиданная ошибка: {e}")
                    import traceback

                    display_manager.show_error(traceback.format_exc())
                else:
                    display_manager.show_error(f"Произошла ошибка: {e}")

                if not input_handler.confirm_action("Попробовать продолжить?"):
                    break

        # Show final solution
        display_manager.show_info("\n" + "=" * 50)
        display_manager.show_info("ИТОГОВОЕ РЕШЕНИЕ")
        solution_processor.show_solution_summary()

    except Exception as e:
        if debug:
            import traceback

            console.print(f"[red]Критическая ошибка: {e}[/red]")
            console.print(traceback.format_exc())
        else:
            console.print(f"[red]Не удалось запустить решение: {e}[/red]")


@cli.command()
def interactive() -> None:
    """Start interactive problem-solving session."""
    console.print(
        Panel.fit(
            "[bold blue]Math IDE - Интерактивный режим[/bold blue]\n"
            "Введите математическую задачу для решения",
            border_style="blue",
        )
    )

    try:
        # Initialize components
        gpt_client = GPTClient()
        prompt_manager = PromptManager()

        # Initialize engines
        transformation_generator = TransformationGenerator(gpt_client, prompt_manager)
        transformation_applier = TransformationApplier(gpt_client, prompt_manager)
        solution_checker = SolutionChecker(gpt_client, prompt_manager)

        history = SolutionHistory()

        latex_renderer = LatexRenderer()
        display_manager = DisplayManager(console, latex_renderer)
        input_handler = InputHandler(console)
        solution_processor = SolutionProcessor(
            transformation_generator,
            transformation_applier,
            solution_checker,
            history,
            input_handler,
            display_manager,
        )

        while True:
            try:
                problem = input_handler.get_problem_input()
                if not problem:
                    continue

                # Reset history for new problem
                history = SolutionHistory(problem)
                solution_processor.history = history

                display_manager.show_problem(problem)

                # Solve the problem
                current_problem = problem
                while True:
                    should_continue = solution_processor.process_solution_step(
                        current_problem
                    )

                    if not should_continue:
                        break

                    # Update current problem
                    steps = history.get_steps()
                    if steps:
                        current_problem = steps[-1].expression

                    # Ask user what to do next
                    if not input_handler.confirm_action(
                        "Продолжить решение этой задачи?"
                    ):
                        break

                # Show final solution
                solution_processor.show_solution_summary()

                if not input_handler.confirm_action("Решить ещё одну задачу?"):
                    break

            except KeyboardInterrupt:
                console.print("\n[yellow]Сессия прервана пользователем[/yellow]")
                break
            except Exception as e:
                console.print(f"[red]Ошибка: {e}[/red]")

                if not input_handler.confirm_action("Продолжить интерактивную сессию?"):
                    break

    except Exception as e:
        console.print(f"[red]Не удалось запустить интерактивный режим: {e}[/red]")


@cli.command()
@click.argument("problem")
@click.option("--steps", "-s", type=int, help="Maximum number of solution steps")
@click.option("--model", default="gpt-4o-mini", help="GPT model to use")
def auto(problem: str, steps: Optional[int], model: str) -> None:
    """Automatically solve problem without user interaction."""
    try:
        gpt_client = GPTClient(model=model)
        prompt_manager = PromptManager()

        # Initialize engines
        transformation_generator = TransformationGenerator(gpt_client, prompt_manager)
        transformation_applier = TransformationApplier(gpt_client, prompt_manager)
        solution_checker = SolutionChecker(gpt_client, prompt_manager)

        history = SolutionHistory(problem)

        latex_renderer = LatexRenderer()
        display_manager = DisplayManager(console, latex_renderer)

        display_manager.show_welcome()
        display_manager.show_problem(problem)

        current_problem = problem
        step_count = 0
        max_steps = steps or 10

        while step_count < max_steps:
            # Create current step
            current_step = SolutionStep(
                expression=current_problem, solution_type=SolutionType.SINGLE
            )

            # Check if solved
            is_solved = solution_checker.check_solution_completeness(
                current_step, problem
            )
            if is_solved.is_solved:
                display_manager.show_completion_message()
                break

            # Generate and apply best transformation
            transformations = transformation_generator.generate_transformations(
                current_step
            )
            if not transformations or not transformations.transformations:
                display_manager.show_error("Не удалось сгенерировать трансформации")
                break

            # Use first (presumably best) transformation
            best_transformation = transformations.transformations[0]

            # Skip parameterized transformations in auto mode
            if best_transformation.requires_user_input:
                display_manager.show_info(
                    f"Пропуск параметризованной трансформации: {best_transformation.description}"
                )
                if len(transformations.transformations) > 1:
                    best_transformation = transformations.transformations[1]
                else:
                    display_manager.show_info(
                        "Нет доступных непараметризованных трансформаций"
                    )
                    break

            result = transformation_applier.apply_transformation(
                current_step, best_transformation
            )
            if not result or not result.is_valid:
                display_manager.show_error("Не удалось применить трансформацию")
                break

            # Add to history
            history.add_step(
                expression=current_problem,
                available_transformations=[
                    t.__dict__ for t in transformations.transformations
                ],
                chosen_transformation=best_transformation.__dict__,
                result_expression=result.result,
            )

            display_manager.display_success_message(
                f"Применено: {best_transformation.description}", result.result
            )

            current_problem = result.result
            step_count += 1

        # Show final solution
        console.print("\n" + "=" * 50)
        console.print("[bold]АВТОМАТИЧЕСКОЕ РЕШЕНИЕ ЗАВЕРШЕНО[/bold]")

        steps_list = history.get_steps()
        if steps_list:
            display_manager.display_history(history)
        else:
            console.print("[yellow]Решение не найдено[/yellow]")

    except Exception as e:
        console.print(f"[red]Ошибка автоматического решения: {e}[/red]")


if __name__ == "__main__":
    cli()

"""
Модуль для обработки пользовательского ввода в CLI.
Содержит InputHandler для работы с различными типами ввода.
"""

import click
from typing import Optional, Any, List, Union, cast
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.types import ParameterDefinition, ParameterType

console = Console()


class InputHandler:
    """
    Обработчик пользовательского ввода для CLI.
    Поддерживает различные типы ввода: текст, числа, выбор из списка.
    """
    
    def __init__(self, console: Optional[Console] = None) -> None:
        """Initialize InputHandler with console."""
        self.console = console or Console()
    
    def request_parameter_value(self, param_def: ParameterDefinition) -> str:
        """
        Запрашивает значение параметра у пользователя.
        
        Args:
            param_def: Определение параметра
            
        Returns:
            Значение параметра в виде строки
        """
        try:
            if param_def.param_type == ParameterType.CHOICE:
                return self._handle_choice_parameter(param_def)
            elif param_def.param_type == ParameterType.NUMBER:
                return self._handle_numeric_parameter(param_def)
            elif param_def.param_type == ParameterType.EXPRESSION:
                return self._handle_expression_parameter(param_def)
            else:
                return self._handle_text_parameter(param_def)
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Ввод отменён[/yellow]")
            raise
    
    def _handle_choice_parameter(self, param_def: ParameterDefinition) -> str:
        """Обрабатывает параметр типа CHOICE."""
        if not param_def.options:
            return self._handle_text_parameter(param_def)
        
        self.console.print(f"\n{param_def.prompt}")
        for i, option in enumerate(param_def.options, 1):
            self.console.print(f"{i}. {option}")
        
        while True:
            try:
                choice = self.console.input(f"Выберите вариант (1-{len(param_def.options)}): ")
                choice_num = int(choice) - 1
                if 0 <= choice_num < len(param_def.options):
                    return str(param_def.options[choice_num])
                else:
                    self.console.print(f"[red]Выберите число от 1 до {len(param_def.options)}[/red]")
            except ValueError:
                self.console.print("[red]Введите корректное число[/red]")
            except KeyboardInterrupt:
                raise
    
    def _handle_numeric_parameter(self, param_def: ParameterDefinition) -> str:
        """Обрабатывает параметр типа NUMBER."""
        while True:
            try:
                value = self.console.input(f"{param_def.prompt} (число): ")
                # Проверяем, что это число
                float(value)  # Пробуем преобразовать в float
                return value
            except ValueError:
                self.console.print("[red]Введите корректное число[/red]")
            except KeyboardInterrupt:
                raise
    
    def _handle_expression_parameter(self, param_def: ParameterDefinition) -> str:
        """Обрабатывает параметр типа EXPRESSION."""
        try:
            value = self.console.input(f"{param_def.prompt} (выражение): ")
            return value
        except KeyboardInterrupt:
            raise
    
    def _handle_text_parameter(self, param_def: ParameterDefinition) -> str:
        """Обрабатывает параметр типа TEXT."""
        try:
            value = cast(str, self.console.input(f"{param_def.prompt}: "))
            return value
        except KeyboardInterrupt:
            return ""
    
    def get_user_choice(self, prompt: str, choices: Optional[List[str]] = None) -> str:
        """
        Запрашивает выбор пользователя с определёнными вариантами.
        
        Args:
            prompt: Текст запроса
            choices: Список допустимых вариантов (если указан)
            
        Returns:
            Выбор пользователя
        """
        while True:
            try:
                choice = cast(str, click.prompt(prompt, type=str)).strip().lower()
                
                if choices is None:
                    return choice
                
                # Проверяем, есть ли выбор среди допустимых
                for valid_choice in choices:
                    if choice == valid_choice.lower():
                        return choice
                
                self.console.print(f"[red]Допустимые варианты: {', '.join(choices)}[/red]")
                
            except click.Abort:
                return "q"  # По умолчанию выход при отмене
    
    def get_numeric_choice(self, prompt: str, min_value: int, max_value: int) -> int:
        """
        Запрашивает числовой выбор в указанном диапазоне.
        
        Args:
            prompt: Текст запроса
            min_value: Минимальное значение
            max_value: Максимальное значение
            
        Returns:
            Выбранное число
        """
        while True:
            try:
                choice = cast(int, click.prompt(prompt, type=int))
                
                if min_value <= choice <= max_value:
                    return choice
                else:
                    self.console.print(f"[red]Введите число от {min_value} до {max_value}[/red]")
                    
            except (ValueError, click.Abort):
                self.console.print("[red]Введите корректное число[/red]")
    
    def confirm_action(self, message: str) -> bool:
        """
        Запрашивает подтверждение действия у пользователя.
        
        Args:
            message: Сообщение для подтверждения
            
        Returns:
            True если пользователь подтвердил, False иначе
        """
        return bool(click.confirm(message))
    
    def get_transformation_choice(self, num_transformations: int) -> Optional[int]:
        """Get user's transformation choice."""
        while True:
            try:
                choice = self.console.input(f"Выберите преобразование (1-{num_transformations}, 0-выход): ")
                
                if choice == '0':
                    return None
                
                choice_num = int(choice) - 1
                if 0 <= choice_num < num_transformations:
                    return choice_num
                else:
                    self.console.print(f"[red]Выберите число от 1 до {num_transformations}[/red]")
            except ValueError:
                self.console.print("[red]Введите корректное число[/red]")
            except KeyboardInterrupt:
                return None
    
    def confirm_branching(self) -> bool:
        """Ask user to confirm branching approach."""
        return self.confirm_action("Использовать ветвящийся подход к решению?")
    
    def get_branch_choice(self, branches: List[Any]) -> Optional[int]:
        """Get user's choice of branch to continue with."""
        if not branches:
            return None
        
        self.console.print("\nДоступные ветви:")
        for i, branch in enumerate(branches, 1):
            self.console.print(f"{i}. {branch.description}")
        
        while True:
            try:
                choice = self.console.input(f"Выберите ветвь (1-{len(branches)}, 0-отмена): ")
                
                if choice == '0':
                    return None
                
                choice_num = int(choice) - 1
                if 0 <= choice_num < len(branches):
                    return choice_num
                else:
                    self.console.print(f"[red]Выберите число от 1 до {len(branches)}[/red]")
            except ValueError:
                self.console.print("[red]Введите корректное число[/red]")
            except KeyboardInterrupt:
                return None
    
    def get_rollback_choice(self, num_steps: int) -> Optional[int]:
        """Get user's choice for rollback step."""
        if num_steps == 0:
            return None
        
        self.console.print(f"\nДоступно шагов для отката: {num_steps}")
        
        while True:
            try:
                choice = self.console.input(f"К какому шагу откатиться? (1-{num_steps}, 0-отмена): ")
                
                if choice == '0':
                    return None
                
                choice_num = int(choice) - 1  # Convert to 0-based
                if 0 <= choice_num < num_steps:
                    return choice_num
                else:
                    self.console.print(f"[red]Выберите число от 1 до {num_steps}[/red]")
            except ValueError:
                self.console.print("[red]Введите корректное число[/red]")
            except KeyboardInterrupt:
                return None
    
    def get_problem_input(self) -> Optional[str]:
        """Get problem input from user."""
        try:
            problem = self.console.input("\n[bold]Введите математическую задачу:[/bold] ").strip()
            if not problem:
                self.console.print("[yellow]Задача не может быть пустой[/yellow]")
                return None
            return problem
        except KeyboardInterrupt:
            return None
    
    def get_numeric_parameter(self, param_def: ParameterDefinition) -> str:
        """Get numeric parameter value from user."""
        while True:
            try:
                value = self.console.input(f"{param_def.prompt} (число): ")
                if param_def.param_type == ParameterType.NUMBER:
                    # Проверяем, что это число, но возвращаем как строку
                    float(value) if '.' in value else int(value)
                return value
            except ValueError:
                self.console.print("[red]Введите корректное число[/red]")
            except KeyboardInterrupt:
                return ""
    
    def get_expression_parameter(self, param_def: ParameterDefinition) -> str:
        """Get expression parameter value from user."""
        try:
            value = self.console.input(f"{param_def.prompt} (выражение): ")
            return value
        except KeyboardInterrupt:
            return ""
    
    def get_choice_parameter(self, param_def: ParameterDefinition) -> str:
        """Get choice parameter value from user."""
        if not param_def.options:
            return self.get_text_parameter(param_def)
        
        self.console.print(f"\n{param_def.prompt}")
        for i, option in enumerate(param_def.options, 1):
            self.console.print(f"{i}. {option}")
        
        while True:
            try:
                choice = self.console.input(f"Выберите вариант (1-{len(param_def.options)}): ")
                choice_num = int(choice) - 1
                if 0 <= choice_num < len(param_def.options):
                    return param_def.options[choice_num]
                else:
                    self.console.print(f"[red]Выберите число от 1 до {len(param_def.options)}[/red]")
            except ValueError:
                self.console.print("[red]Введите корректное число[/red]")
            except KeyboardInterrupt:
                return ""
    
    def get_text_parameter(self, param_def: ParameterDefinition) -> str:
        """Get text parameter value from user."""
        try:
            value = cast(str, self.console.input(f"{param_def.prompt}: "))
            return value
        except KeyboardInterrupt:
            return "" 
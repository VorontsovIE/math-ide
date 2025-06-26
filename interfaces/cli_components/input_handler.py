import click
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.types import ParameterDefinition, ParameterType

console = Console()


class InputHandler:
    """
    Компонент для обработки пользовательского ввода и запроса параметров.
    Отвечает за интерактивный ввод данных от пользователя.
    """
    
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
            return self._handle_choice_parameter(param_def)
        else:
            return self._handle_text_parameter(param_def)
    
    def _handle_choice_parameter(self, param_def: ParameterDefinition) -> str:
        """
        Обрабатывает параметр типа выбор из вариантов.
        
        Args:
            param_def: Определение параметра с вариантами выбора
            
        Returns:
            Выбранное значение
        """
        if not param_def.options:
            raise ValueError("Options list is empty for choice parameter")
            
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
    
    def _handle_text_parameter(self, param_def: ParameterDefinition) -> str:
        """
        Обрабатывает текстовый параметр.
        
        Args:
            param_def: Определение параметра
            
        Returns:
            Введенное значение
        """
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
                return str(param_def.default_value)
            raise
    
    def get_user_choice(self, prompt: str, choices: Optional[list[str]] = None) -> str:
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
                choice = click.prompt(prompt, type=str).strip().lower()
                
                if choices is None:
                    return choice
                
                # Проверяем, есть ли выбор среди допустимых
                for valid_choice in choices:
                    if choice == valid_choice.lower():
                        return choice
                
                console.print(f"[red]Допустимые варианты: {', '.join(choices)}[/red]")
                
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
                choice = click.prompt(prompt, type=int)
                
                if min_value <= choice <= max_value:
                    return choice
                else:
                    console.print(f"[red]Введите число от {min_value} до {max_value}[/red]")
                    
            except (ValueError, click.Abort):
                console.print("[red]Введите корректное число[/red]")
    
    def confirm_action(self, message: str) -> bool:
        """
        Запрашивает подтверждение действия у пользователя.
        
        Args:
            message: Сообщение для подтверждения
            
        Returns:
            True если пользователь подтвердил, False иначе
        """
        return click.confirm(message) 
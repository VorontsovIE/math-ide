"""Solution processing logic for CLI interface."""

from typing import Dict, Any, List, Optional, Callable
from core.types import (
    SolutionStep, Transformation, TransformationParameter,
    ParameterType, SolutionType, GenerationResult
)
from core.engines.transformation_generator import TransformationGenerator
from core.engines.transformation_applier import TransformationApplier
from core.engines.solution_checker import SolutionChecker
from core.history import SolutionHistory
from .input_handler import InputHandler
from .display_manager import DisplayManager


class SolutionProcessor:
    """Handles solution processing workflow."""
    
    def __init__(self, 
                 transformation_generator: TransformationGenerator,
                 transformation_applier: TransformationApplier,
                 solution_checker: SolutionChecker,
                 history: SolutionHistory,
                 input_handler: InputHandler, 
                 display_manager: DisplayManager) -> None:
        self.transformation_generator = transformation_generator
        self.transformation_applier = transformation_applier
        self.solution_checker = solution_checker
        self.history = history
        self.input_handler = input_handler
        self.display_manager = display_manager
    
    def process_solution_step(self, problem: str) -> bool:
        """Process a single solution step with parameterized transformations support.
        
        Returns True if solution should continue, False if complete or cancelled.
        """
        try:
            # Create current step
            current_step = SolutionStep(
                expression=problem,
                solution_type=SolutionType.SINGLE
            )
            
            # Check if problem is already solved
            is_solved = self.solution_checker.check_solution_completeness(current_step, problem)
            if is_solved.is_solved:
                self.display_manager.show_completion_message()
                return False
            
            # Generate transformations  
            transformations_result = self.transformation_generator.generate_transformations(current_step)
            if not transformations_result or not transformations_result.transformations:
                self.display_manager.show_error("Не удалось сгенерировать трансформации")
                return False
            
            # Display transformations and get user choice
            self.display_manager.show_transformations(transformations_result.transformations)
            choice = self.input_handler.get_transformation_choice(len(transformations_result.transformations))
            
            if choice is None:  # User cancelled
                return False
            
            selected_transformation = transformations_result.transformations[choice]
            
            # Handle parameterized transformations
            if selected_transformation.requires_user_input:
                parameters = self._collect_transformation_parameters(selected_transformation)
                if parameters is None:  # User cancelled parameter input
                    return False
                selected_transformation.parameters = parameters
            
            # Apply transformation
            result = self.transformation_applier.apply_transformation(current_step, selected_transformation)
            if not result or not result.is_valid:
                self.display_manager.show_error("Не удалось применить трансформацию")
                return False
            
            # Add step to history using the simplified API
            self.history.add_step(
                expression=problem,
                available_transformations=[{
                    'description': t.description,
                    'requires_user_input': t.requires_user_input
                } for t in transformations_result.transformations],
                chosen_transformation={
                    'description': selected_transformation.description,
                    'expression': result.result
                },
                result_expression=result.result
            )
            
            self.display_manager.show_info(f"Применено преобразование: {selected_transformation.description}")
            
            return True
            
        except Exception as e:
            self.display_manager.show_error(f"Ошибка при обработке шага: {e}")
            return False
    
    def _collect_transformation_parameters(self, transformation: Transformation) -> Optional[List[TransformationParameter]]:
        """Collect parameters for parameterized transformation."""
        if not transformation.parameter_definitions:
            return []
        
        parameters = []
        
        self.display_manager.show_info(f"Трансформация '{transformation.description}' требует параметры:")
        
        for param_def in transformation.parameter_definitions:
            try:
                if param_def.param_type == ParameterType.NUMBER:
                    value = self.input_handler.get_numeric_parameter(param_def)
                elif param_def.param_type == ParameterType.EXPRESSION:
                    value = self.input_handler.get_expression_parameter(param_def)
                elif param_def.param_type == ParameterType.CHOICE:
                    value = self.input_handler.get_choice_parameter(param_def)
                elif param_def.param_type == ParameterType.TEXT:
                    value = self.input_handler.get_text_parameter(param_def)
                else:
                    self.display_manager.show_error(f"Неизвестный тип параметра: {param_def.param_type}")
                    return None
                
                if value == "":  # User cancelled or empty value
                    return None
                
                parameters.append(TransformationParameter(
                    name=param_def.name,
                    value=value
                ))
                
            except KeyboardInterrupt:
                self.display_manager.show_info("Ввод параметров отменён")
                return None
            except Exception as e:
                self.display_manager.show_error(f"Ошибка при вводе параметра {param_def.name}: {e}")
                return None
        
        return parameters
    
    def show_solution_summary(self) -> None:
        """Show complete solution summary."""
        if not self.history or self.history.is_empty():
            self.display_manager.show_info("История решения пуста")
            return
        
        self.display_manager.display_history(self.history)
    
    def handle_rollback(self) -> bool:
        """Handle solution rollback."""
        if not self.history or not self.history.can_rollback():
            self.display_manager.show_info("Нет шагов для отката")
            return False
        
        # Show current steps for selection
        self.display_manager.display_interactive_history(self.history)
        step_choice = self.input_handler.get_rollback_choice(len(self.history.steps))
        
        if step_choice is None:
            return False
        
        try:
            self.history.rollback_to_step(step_choice + 1)  # Convert to 1-based
            self.display_manager.show_info(f"Откат выполнен к шагу {step_choice + 1}")
            return True
        except Exception as e:
            self.display_manager.show_error(f"Ошибка при откате: {e}")
            return False

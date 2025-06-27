"""
Тесты для функциональности возврата к произвольному шагу истории.
"""

from core.history import SolutionHistory, HistoryStep
from core.types import SolutionStep


def test_basic_rollback():
    """Тест базового возврата к шагу."""
    history = SolutionHistory("x + 1 = 3")

    # Добавляем несколько шагов
    history.add_step(
        expression="x + 1 = 3",
        available_transformations=[],
        chosen_transformation={
            "description": "Вычесть 1",
            "type": "subtract",
            "expression": "x = 2",
        },
        result_expression="x = 2",
    )

    history.add_step(
        expression="x = 2",
        available_transformations=[],
        chosen_transformation={
            "description": "Решение найдено",
            "type": "solution",
            "expression": "x = 2",
        },
        result_expression="x = 2",
    )

    history.add_step(
        expression="x = 2",
        available_transformations=[],
        chosen_transformation={
            "description": "Проверка",
            "type": "verify",
            "expression": "2 + 1 = 3",
        },
        result_expression="2 + 1 = 3",
    )

    # Проверяем исходное состояние
    assert history.get_steps_count() == 3
    assert history.current_step_number == 3

    # Выполняем возврат к шагу 1
    assert history.rollback_to_step(1) == True

    # Проверяем состояние после возврата
    assert history.get_steps_count() == 2  # Остались только шаги 0 и 1
    assert history.current_step_number == 2  # Готов к добавлению шага 2
    assert history.get_current_expression() == "x = 2"


def test_rollback_to_first_step():
    """Тест возврата к самому первому шагу."""
    history = SolutionHistory("2x = 4")

    # Добавляем шаги
    history.add_step(
        expression="2x = 4",
        available_transformations=[],
        chosen_transformation={
            "description": "Разделить на 2",
            "type": "divide",
            "expression": "x = 2",
        },
        result_expression="x = 2",
    )

    history.add_step(
        expression="x = 2",
        available_transformations=[],
        chosen_transformation={
            "description": "Решение найдено",
            "type": "solution",
            "expression": "x = 2",
        },
        result_expression="x = 2",
    )

    # Возврат к шагу 0
    assert history.rollback_to_step(0) == True
    assert history.get_steps_count() == 1
    assert history.current_step_number == 1
    assert history.get_current_expression() == "x = 2"  # Результат шага 0


def test_rollback_invalid_step():
    """Тест возврата к несуществующему шагу."""
    history = SolutionHistory("x = 1")

    history.add_step(
        expression="x = 1",
        available_transformations=[],
        chosen_transformation=None,
        result_expression=None,
    )

    # Попытка возврата к несуществующим шагам
    assert history.rollback_to_step(-1) == False  # Отрицательный номер
    assert history.rollback_to_step(5) == False  # Слишком большой номер
    assert history.rollback_to_step(10) == False  # Намного больший номер

    # Состояние не изменилось
    assert history.get_steps_count() == 1
    assert history.current_step_number == 1


def test_can_rollback():
    """Тест проверки возможности возврата."""
    history = SolutionHistory("x = 0")

    # Пустая история - возврат невозможен
    assert history.can_rollback() == False

    # Добавляем один шаг - возврат все еще невозможен
    history.add_step(
        expression="x = 0",
        available_transformations=[],
        chosen_transformation=None,
        result_expression=None,
    )
    assert history.can_rollback() == False

    # Добавляем второй шаг - теперь возврат возможен
    history.add_step(
        expression="x = 0",
        available_transformations=[],
        chosen_transformation={
            "description": "Решение",
            "type": "solution",
            "expression": "x = 0",
        },
        result_expression="x = 0",
    )
    assert history.can_rollback() == True


def test_rollback_by_id():
    """Тест возврата к шагу по ID."""
    history = SolutionHistory("3x = 9")

    # Добавляем шаги и сохраняем их ID
    step1_id = history.add_step(
        expression="3x = 9",
        available_transformations=[],
        chosen_transformation={
            "description": "Разделить на 3",
            "type": "divide",
            "expression": "x = 3",
        },
        result_expression="x = 3",
    )

    step2_id = history.add_step(
        expression="x = 3",
        available_transformations=[],
        chosen_transformation={
            "description": "Готово",
            "type": "solution",
            "expression": "x = 3",
        },
        result_expression="x = 3",
    )

    step3_id = history.add_step(
        expression="x = 3",
        available_transformations=[],
        chosen_transformation={
            "description": "Проверка",
            "type": "verify",
            "expression": "3*3 = 9",
        },
        result_expression="3*3 = 9",
    )

    # Возврат к первому шагу по ID (номер 0)
    assert history.rollback_to_step_by_id(step1_id) == True
    assert history.get_steps_count() == 1  # Остается только шаг 0
    assert history.get_current_expression() == "x = 3"

    # Возврат к несуществующему ID
    assert history.rollback_to_step_by_id("nonexistent-id") == False


def test_get_current_expression():
    """Тест получения текущего выражения."""
    history = SolutionHistory("x + 5 = 7")

    # Для пустой истории должна возвращаться исходная задача
    assert history.get_current_expression() == "x + 5 = 7"

    # Добавляем шаг без результата
    history.add_step(
        expression="x + 5 = 7",
        available_transformations=[],
        chosen_transformation=None,
        result_expression=None,
    )
    assert history.get_current_expression() == "x + 5 = 7"

    # Добавляем шаг с результатом
    history.add_step(
        expression="x + 5 = 7",
        available_transformations=[],
        chosen_transformation={
            "description": "Вычесть 5",
            "type": "subtract",
            "expression": "x = 2",
        },
        result_expression="x = 2",
    )
    assert history.get_current_expression() == "x = 2"


def test_rollback_and_continue():
    """Тест возврата с последующим продолжением решения."""
    history = SolutionHistory("2x + 4 = 8")

    # Добавляем шаги
    history.add_step(
        expression="2x + 4 = 8",
        available_transformations=[],
        chosen_transformation={
            "description": "Вычесть 4",
            "type": "subtract",
            "expression": "2x = 4",
        },
        result_expression="2x = 4",
    )

    history.add_step(
        expression="2x = 4",
        available_transformations=[],
        chosen_transformation={
            "description": "Разделить на 2",
            "type": "divide",
            "expression": "x = 2",
        },
        result_expression="x = 2",
    )

    # Возврат к первому шагу
    assert history.rollback_to_step(0) == True

    # Добавляем новый шаг (альтернативный путь решения)
    new_step_id = history.add_step(
        expression="2x + 4 = 8",
        available_transformations=[],
        chosen_transformation={
            "description": "Разделить все на 2",
            "type": "divide",
            "expression": "x + 2 = 4",
        },
        result_expression="x + 2 = 4",
    )

    # Проверяем, что добавился новый шаг с правильным номером
    assert history.get_steps_count() == 2
    assert history.current_step_number == 2
    assert history.get_current_expression() == "x + 2 = 4"

    # Находим новый шаг и проверяем его номер
    new_step = history.get_step_by_id(new_step_id)
    assert new_step is not None
    assert new_step.step_number == 1  # Второй шаг имеет номер 1


if __name__ == "__main__":
    test_basic_rollback()
    test_rollback_to_first_step()
    test_rollback_invalid_step()
    test_can_rollback()
    test_rollback_by_id()
    test_get_current_expression()
    test_rollback_and_continue()
    print("Все тесты возврата к шагам истории прошли успешно!")

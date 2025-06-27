"""
Тесты для функциональности отката к предыдущим шагам в истории решения.
"""

from core.history import SolutionHistory


def test_basic_rollback():
    """Тест базового отката к предыдущему шагу."""
    history = SolutionHistory("Решить уравнение: 2x + 4 = 10")
    
    # Добавляем несколько шагов
    history.add_step("2x + 4 = 10", available_transformations=[])
    history.add_step("2x = 6", available_transformations=[])
    history.add_step("x = 3", available_transformations=[])
    
    # Проверяем текущее состояние
    assert history.get_steps_count() == 3
    assert history.get_current_step().expression == "x = 3"
    
    # Откатываемся к предыдущему шагу
    success = history.rollback_to_step(1)
    
    assert success is True
    assert history.get_steps_count() == 2
    assert history.get_current_step().expression == "2x = 6"


def test_rollback_to_first_step():
    """Тест отката к первому шагу."""
    history = SolutionHistory("Решить уравнение x + 2 = 5")
    
    # Добавляем несколько шагов
    history.add_step("x + 2 = 5", available_transformations=[])
    history.add_step("x = 5 - 2", available_transformations=[])
    history.add_step("x = 3", available_transformations=[])
    
    # Возврат к шагу 0
    assert history.rollback_to_step(0) is True
    assert history.get_steps_count() == 1
    assert history.current_step_number == 1
    assert history.get_current_expression() == "x + 2 = 5"
    
    # Проверяем, что можем продолжить
    new_step = history.add_step("x = 5 - 2", available_transformations=[])
    assert history.get_steps_count() == 2
    assert new_step.step_number == 2


def test_rollback_invalid_step():
    """Тест отката к несуществующему шагу."""
    history = SolutionHistory("Решить уравнение x + 2 = 5")
    
    # Добавляем несколько шагов
    history.add_step("x + 2 = 5", available_transformations=[])
    history.add_step("x = 5 - 2", available_transformations=[])
    history.add_step("x = 3", available_transformations=[])
    
    # Попытка возврата к несуществующим шагам
    assert history.rollback_to_step(-1) is False  # Отрицательный номер
    assert history.rollback_to_step(5) is False  # Слишком большой номер
    assert history.rollback_to_step(10) is False  # Намного больший номер
    
    # Состояние не изменилось
    assert history.get_steps_count() == 3
    assert history.current_step_number == 3


def test_can_rollback():
    """Тест проверки возможности отката."""
    history = SolutionHistory("Решить уравнение x + 2 = 5")
    
    # Пустая история - возврат невозможен
    assert history.can_rollback() is False
    
    # Добавляем один шаг - возврат все еще невозможен
    step1 = history.add_step(
        "x + 2 = 5",
        chosen_transformation=None,
        result_expression=None,
    )
    assert history.can_rollback() is False
    
    # Добавляем второй шаг - теперь возврат возможен
    step2 = history.add_step(
        "x = 0",
        chosen_transformation=None,
        result_expression="x = 0",
    )
    assert history.can_rollback() is True


def test_rollback_by_id():
    """Тест отката к шагу по ID."""
    history = SolutionHistory("Решить уравнение x + 2 = 5")
    
    # Добавляем несколько шагов
    step1_id = history.add_step("x + 2 = 5")
    step2_id = history.add_step("x = 5 - 2")
    step3_id = history.add_step("x = 3")
    
    # Возврат к первому шагу по ID (номер 0)
    assert history.rollback_to_step_by_id(step1_id) is True
    assert history.get_steps_count() == 1  # Остается только шаг 0
    assert history.get_current_expression() == "x = 3"
    
    # Попытка возврата к несуществующему ID
    assert history.rollback_to_step_by_id("nonexistent-id") is False
    
    # Проверяем, что можем продолжить
    new_step = history.add_step("x = 3 (проверка)")
    assert history.get_steps_count() == 2
    assert new_step.step_number == 2


def test_get_current_expression():
    """Тест получения текущего выражения."""
    history = SolutionHistory("Решить уравнение x + 2 = 5")
    
    # В пустой истории нет выражения
    assert history.get_current_expression() == ""
    
    # Добавляем шаг
    step1 = history.add_step("x + 2 = 5")
    assert history.get_current_expression() == "x + 2 = 5"
    
    # Добавляем еще шаг
    step2 = history.add_step("x = 5 - 2")
    assert history.get_current_expression() == "x = 5 - 2"


def test_rollback_and_continue():
    """Тест продолжения решения после отката."""
    history = SolutionHistory("Решить уравнение x + 2 = 5")
    
    # Добавляем несколько шагов
    step1 = history.add_step("x + 2 = 5")
    step2 = history.add_step("x = 5 - 2")
    step3 = history.add_step("x = 3")
    
    # Откатываемся к шагу 1
    history.rollback_to_step(1)
    
    # Продолжаем решение по новому пути
    new_step = history.add_step("x = 3 (новый путь)")
    assert history.get_steps_count() == 3
    assert new_step.step_number == 3
    
    # Проверяем, что старые шаги после отката удалены
    assert history.get_step_summary(history.steps[0]) == "x + 2 = 5"
    assert history.get_step_summary(history.steps[1]) == "x = 5 - 2"
    assert history.get_step_summary(history.steps[2]) == "x = 3 (новый путь)"


def test_rollback_to_previous_step():
    """Тест отката к предыдущему шагу."""
    history = SolutionHistory("Решить уравнение: 2x + 4 = 10")
    
    # Добавляем несколько шагов
    history.add_step("2x + 4 = 10", available_transformations=[])
    history.add_step("2x = 6", available_transformations=[])
    history.add_step("x = 3", available_transformations=[])
    
    # Проверяем текущее состояние
    assert history.get_steps_count() == 3
    assert history.get_current_step().expression == "x = 3"
    
    # Откатываемся к предыдущему шагу
    success = history.rollback_to_step(1)
    
    assert success is True
    assert history.get_steps_count() == 2
    assert history.get_current_step().expression == "2x = 6"


if __name__ == "__main__":
    # Запускаем все тесты
    test_basic_rollback()
    test_rollback_to_first_step()
    test_rollback_invalid_step()
    test_can_rollback()
    test_rollback_by_id()
    test_get_current_expression()
    test_rollback_and_continue()
    test_rollback_to_previous_step()
    print("Все тесты возврата к шагам истории прошли успешно!")

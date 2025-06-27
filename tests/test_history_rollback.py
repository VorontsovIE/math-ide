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
    new_step_id = history.add_step("x = 5 - 2", available_transformations=[])
    assert history.get_steps_count() == 2
    assert isinstance(new_step_id, str)  # add_step возвращает ID


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
    _ = history.add_step(
        "x + 2 = 5",
        available_transformations=[],
        chosen_transformation=None,
        result_expression=None,
    )
    assert history.can_rollback() is False

    # Добавляем второй шаг - теперь возврат возможен
    _ = history.add_step(
        "x = 0",
        available_transformations=[],
        chosen_transformation=None,
        result_expression="x = 0",
    )
    assert history.can_rollback() is True


def test_rollback_by_id():
    """Тест отката к шагу по ID."""
    history = SolutionHistory("Решить уравнение x + 2 = 5")

    # Добавляем несколько шагов
    step1_id = history.add_step("x + 2 = 5", available_transformations=[])
    _ = history.add_step("x = 5 - 2", available_transformations=[])
    _ = history.add_step("x = 3", available_transformations=[])

    # Возврат к первому шагу по ID (номер 0)
    assert history.rollback_to_step_by_id(step1_id) is True
    assert history.get_steps_count() == 1  # Остается только шаг 0
    assert history.get_current_expression() == "x + 2 = 5"

    # Попытка возврата к несуществующему ID
    assert history.rollback_to_step_by_id("nonexistent-id") is False

    # Проверяем, что можем продолжить
    new_step_id = history.add_step("x = 3 (проверка)", available_transformations=[])
    assert history.get_steps_count() == 2
    assert isinstance(new_step_id, str)  # add_step возвращает ID


def test_get_current_expression():
    """Тест получения текущего выражения."""
    history = SolutionHistory("Решить уравнение x + 2 = 5")

    # В пустой истории нет выражения
    assert history.get_current_expression() == ""

    # Добавляем шаг
    _ = history.add_step("x + 2 = 5", available_transformations=[])
    assert history.get_current_expression() == "x + 2 = 5"

    # Добавляем еще шаг
    _ = history.add_step("x = 5 - 2", available_transformations=[])
    assert history.get_current_expression() == "x = 5 - 2"


def test_rollback_and_continue():
    """Тест продолжения решения после отката."""
    history = SolutionHistory("Решить уравнение x + 2 = 5")

    # Добавляем несколько шагов
    _ = history.add_step("x + 2 = 5", available_transformations=[])
    _ = history.add_step("x = 5 - 2", available_transformations=[])
    _ = history.add_step("x = 3", available_transformations=[])

    # Откатываемся к шагу 1
    history.rollback_to_step(1)

    # Продолжаем решение по новому пути
    new_step_id = history.add_step("x = 3 (новый путь)", available_transformations=[])
    assert history.get_steps_count() == 3
    assert isinstance(new_step_id, str)  # add_step возвращает ID

    # Проверяем, что старые шаги после отката удалены
    assert history.get_step_summary(history.steps[0])["expression"] == "x + 2 = 5"
    assert history.get_step_summary(history.steps[1])["expression"] == "x = 5 - 2"
    assert history.get_step_summary(history.steps[2])["expression"] == "x = 3 (новый путь)"


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


def test_basic_history_operations() -> None:
    """Тест базовых операций с историей."""
    history = SolutionHistory()

    # Добавляем первый шаг
    step1_id = history.add_step(
        expression="x + 2 = 5",
        available_transformations=[{"description": "Вычесть 2"}],
        chosen_transformation={"description": "Вычесть 2", "expression": "x = 5 - 2"},
        result_expression="x = 3",
    )

    # Проверяем, что шаг добавлен
    assert step1_id is not None
    assert isinstance(step1_id, str)  # add_step возвращает ID
    assert len(history.steps) == 1

    # Добавляем второй шаг
    step2_id = history.add_step(
        expression="x = 3",
        available_transformations=[{"description": "Упростить"}],
        chosen_transformation={"description": "Упростить", "expression": "x = 3"},
        result_expression="x = 3",
    )

    assert step2_id is not None
    assert isinstance(step2_id, str)  # add_step возвращает ID
    assert len(history.steps) == 2


def test_rollback_operations() -> None:
    """Тест операций отката."""
    history = SolutionHistory()

    # Добавляем несколько шагов
    history.add_step(
        expression="x + 2 = 5",
        available_transformations=[{"description": "Вычесть 2"}],
        chosen_transformation={"description": "Вычесть 2", "expression": "x = 5 - 2"},
        result_expression="x = 3",
    )

    history.add_step(
        expression="x = 3",
        available_transformations=[{"description": "Проверить"}],
        chosen_transformation={"description": "Проверить", "expression": "3 + 2 = 5"},
        result_expression="✓",
    )

    # Проверяем, что можно откатиться
    assert history.can_rollback()

    # Откатываемся к первому шагу
    history.rollback_to_step(1)
    assert len(history.steps) == 1
    assert history.steps[0].expression == "x + 2 = 5"


def test_rollback_edge_cases() -> None:
    """Тест граничных случаев отката."""
    history = SolutionHistory()

    # Пытаемся откатиться в пустой истории
    assert not history.can_rollback()

    # Добавляем один шаг
    history.add_step(
        expression="x = 1",
        available_transformations=[{"description": "Упростить"}],
        chosen_transformation={"description": "Упростить", "expression": "x = 1"},
        result_expression="x = 1",
    )

    # Пытаемся откатиться к несуществующему шагу
    try:
        history.rollback_to_step(5)
        assert False, "Должна была возникнуть ошибка"
    except ValueError:
        pass  # Ожидаемое поведение


def test_history_persistence() -> None:
    """Тест сохранения состояния истории."""
    history = SolutionHistory()

    # Добавляем шаги
    history.add_step(
        expression="x + 2 = 5",
        available_transformations=[{"description": "Вычесть 2"}],
        chosen_transformation={"description": "Вычесть 2", "expression": "x = 5 - 2"},
        result_expression="x = 3",
    )

    history.add_step(
        expression="x = 3",
        available_transformations=[{"description": "Проверить"}],
        chosen_transformation={"description": "Проверить", "expression": "3 + 2 = 5"},
        result_expression="✓",
    )

    # Проверяем, что история сохранилась
    assert len(history.steps) == 2
    assert history.steps[0].expression == "x + 2 = 5"
    assert history.steps[1].expression == "x = 3"


def test_complex_rollback_scenario() -> None:
    """Тест сложного сценария отката."""
    history = SolutionHistory()

    # Добавляем несколько шагов с разными преобразованиями
    steps_data = [
        ("x + 2 = 5", "Вычесть 2", "x = 5 - 2", "x = 3"),
        ("x = 3", "Проверить", "3 + 2 = 5", "✓"),
        ("x = 3 (новый путь)", "Упростить", "x = 3", "x = 3"),
    ]

    for expr, desc, chosen_expr, result in steps_data:
        history.add_step(
            expression=expr,
            available_transformations=[{"description": desc}],
            chosen_transformation={"description": desc, "expression": chosen_expr},
            result_expression=result,
        )

    # Проверяем, что все шаги добавлены
    assert len(history.steps) == 3

    # Откатываемся к первому шагу
    history.rollback_to_step(1)
    assert len(history.steps) == 1
    assert history.steps[0].expression == "x + 2 = 5"


def test_history_validation() -> None:
    """Тест валидации истории."""
    history = SolutionHistory()

    # Добавляем валидный шаг
    step_id = history.add_step(
        expression="x = 1",
        available_transformations=[{"description": "Упростить"}],
        chosen_transformation={"description": "Упростить", "expression": "x = 1"},
        result_expression="x = 1",
    )

    # Проверяем валидность
    assert step_id is not None
    assert isinstance(step_id, str)  # add_step возвращает ID
    assert len(history.steps) == 1
    assert history.steps[0].expression == "x = 1"


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
    test_basic_history_operations()
    test_rollback_operations()
    test_rollback_edge_cases()
    test_history_persistence()
    test_complex_rollback_scenario()
    test_history_validation()
    print("Все тесты возврата к шагам истории прошли успешно!")

# MathIDE

Интерактивная математическая IDE с поддержкой пошагового решения задач.

## Установка

1. Установите poetry:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

2. Клонируйте репозиторий:
   ```bash
   git clone <repository_url>
   cd math-ide
   ```

3. Установите зависимости:
   ```bash
   poetry install
   ```

4. Создайте файл `.env` на основе `docs/env.example`:
   ```bash
   cp docs/env.example .env
   ```

5. Отредактируйте `.env`, указав:
   - `TELEGRAM_BOT_TOKEN` - токен вашего Telegram-бота (получить у @BotFather)
   - `OPENAI_API_KEY` - ваш ключ API OpenAI
   - `GPT_MODEL` - модель GPT для использования (опционально)

## Запуск

### Telegram-бот
```bash
poetry run python -m interfaces
```

### CLI-интерфейс
```bash
poetry run python -m interfaces.cli
```

## Разработка

Проект использует:
- poetry для управления зависимостями
- black для форматирования кода
- flake8 для линтинга
- mypy для проверки типов
- pytest для тестирования

### Команды для разработки
```bash
# Форматирование кода
poetry run black .

# Линтинг
poetry run flake8

# Проверка типов
poetry run mypy .

# Тесты
poetry run pytest
```

## Структура проекта

См. [docs/project_structure.mdc](docs/project_structure.mdc) 
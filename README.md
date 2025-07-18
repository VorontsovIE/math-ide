# MathIDE

Интерактивная математическая IDE с поддержкой пошагового решения задач.

## ✅ Статус проекта: Рефакторинг завершён!

Проект успешно трансформирован из монолитной архитектуры в современную модульную систему:

- **🎯 22 модуля** вместо 2 монолитных файлов
- **📉 95% сокращение** размера главного файла Telegram бота (1357 → 62 строки)
- **📉 30% сокращение** размера основного движка (1003 → 700 строк)
- **⚡ Соблюдение SOLID** принципов и архитектурных best practices

## 🚀 Установка

1. Установите uv:
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

2. Клонируйте репозиторий:
   ```bash
   git clone <repository_url>
   cd math-ide
   ```

3. Установите зависимости:
   ```bash
   uv sync --dev
   ```

4. Создайте файл `.env` на основе `docs/env.example`:
   ```bash
   cp docs/env.example .env
   ```

5. Отредактируйте `.env`, указав:
   - `TELEGRAM_BOT_TOKEN` - токен вашего Telegram-бота (получить у @BotFather)
   - `OPENAI_API_KEY` - ваш ключ API OpenAI
   - `GPT_MODEL` - модель GPT для использования (опционально)

## 🎮 Запуск

### Telegram-бот
```bash
uv run python -m interfaces
```

### CLI-интерфейс
```bash
uv run python -m interfaces.cli
```

## 🏗️ Архитектура

### Модульная структура
```
MathIDE/
├── core/              # Ядро системы (8 модулей)
│   ├── engine.py      # Главный движок (700 строк)
│   ├── gpt_client.py  # GPT клиент
│   ├── types.py       # Типы данных
│   └── ...
├── interfaces/        # Интерфейсы (11 модулей)
│   ├── cli.py         # CLI интерфейс
│   ├── telegram/      # Telegram бот (7 модулей)
│   └── ...
├── utils/             # Утилиты (3 модуля)
└── prompts/           # GPT промпты
```

### Ключевые достижения рефакторинга
- ✅ **Читаемость**: каждый модуль имеет четкое назначение
- ✅ **Тестируемость**: модули можно тестировать изолированно
- ✅ **Масштабируемость**: легко добавлять новые интерфейсы
- ✅ **Поддерживаемость**: изменения локализованы в конкретных модулях

## 🔧 Разработка

Проект использует:
- **uv** для управления зависимостями
- **black** для форматирования кода
- **flake8** для линтинга
- **mypy** для проверки типов
- **pytest** для тестирования

### Команды для разработки
```bash
# Тест архитектуры (проверка модульной структуры)
uv run python tests/test_architecture.py

# Форматирование кода
uv run black .

# Линтинг
uv run flake8

# Проверка типов
uv run mypy .

# Тесты
uv run pytest
```

## 📚 Документация

- **[Архитектура](docs/architecture.mdc)** - подробное описание модульной архитектуры
- **[Структура проекта](docs/project_structure.mdc)** - детальная карта всех модулей
- **[План рефакторинга](docs/refactoring_plan.mdc)** - история и этапы рефакторинга
- **[PRD](docs/PRD.mdc)** - требования к продукту
- **[Детали реализации](docs/implementation_details.mdc)** - технические детали

## 🧪 Тестирование архитектуры

Для проверки целостности модульной архитектуры используйте:

```bash
# Запуск теста архитектуры
python tests/test_architecture.py

# Или как исполняемый файл
./tests/test_architecture.py
```

Скрипт проверяет:
- ✅ Корректность импортов всех ключевых модулей
- ✅ Доступность основных классов и функций
- ✅ Целостность модульной структуры
- ⚠️ Опциональные зависимости (click, telegram)

**Коды возврата:**
- `0` - все основные тесты прошли успешно
- `1` - обнаружены проблемы в архитектуре

## ✨ Возможности

### Основные функции
- 🧮 **Пошаговое решение** математических задач
- 🤖 **AI-генерация** преобразований
- 📱 **Telegram-бот** с интуитивным интерфейсом
- 💻 **CLI-интерфейс** для терминала
- 📊 **Рендеринг LaTeX** в изображения
- 📝 **История решений** с возможностью экспорта

### Продвинутые возможности
- 🔍 **Анализ прогресса** с рекомендациями возврата
- ✏️ **Пользовательские преобразования**
- 🔧 **Проверка и исправление ошибок**
- 🎯 **Режим предпоказа результатов**
- 🚫 **Rate limiting** для защиты от spam'а

## 🎯 Технологический стек

| Слой | Технология | Назначение |
|------|------------|------------|
| **Core** | Python 3.10+ | Основной язык |
| **AI** | OpenAI GPT | Генерация преобразований |
| **CLI** | Click | Командная строка |
| **Bot** | python-telegram-bot | Telegram интерфейс |
| **Math** | matplotlib | Рендеринг LaTeX |
| **Config** | python-dotenv | Управление настройками |
| **Deps** | uv | Управление зависимостями |

## 🚦 Статус компонентов

| Компонент | Статус | Описание |
|-----------|--------|----------|
| **Core Engine** | ✅ Готов | Модульная архитектура реализована |
| **Telegram Bot** | ✅ Готов | Полная модульная структура |
| **CLI Interface** | ✅ Готов | Функциональный интерфейс |
| **Web Interface** | ⏳ Планируется | FastAPI + Jinja2 |
| **Tests** | 🔧 В разработке | Юнит и интеграционные тесты |
| **Documentation** | ✅ Готова | Полная техническая документация |

---

**Проект готов к использованию и дальнейшему развитию!** 🎉 
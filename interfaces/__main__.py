import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Добавляем корневую директорию в PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

def load_env_files() -> bool:
    """Загружает переменные окружения из .env файлов."""
    # Пытаемся загрузить локальные .env файлы в порядке приоритета
    env_files = [
        ".env.local",  # Локальные переопределения, не в git
        ".env",        # Основной .env файл, не в git
        ".env.example" # Пример настроек, в git
    ]
    
    for env_file in env_files:
        env_path = root_dir / env_file
        if env_path.exists():
            load_dotenv(env_path)
            if env_file != ".env.example":
                print(f"Загружены настройки из {env_file}")
            return True
    
    print("Внимание: .env файл не найден, используются переменные окружения системы")
    return False

def main() -> None:
    """Точка входа для запуска Math IDE."""
    # Загружаем переменные окружения
    load_env_files()
    
    # Проверяем наличие OPENAI_API_KEY
    if not os.getenv("OPENAI_API_KEY"):
        print("Предупреждение: не задан OPENAI_API_KEY")
        print("Укажите OPENAI_API_KEY в файле .env для работы с GPT")
    
    # Импортируем и запускаем CLI
    from interfaces.cli import cli
    cli()

if __name__ == "__main__":
    main() 
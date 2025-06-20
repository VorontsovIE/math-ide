import os
import sys
from pathlib import Path

# Добавляем корневую директорию в PYTHONPATH
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

def main():
    """Точка входа для запуска бота."""
    # Получаем токен из переменной окружения
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Ошибка: не задан TELEGRAM_BOT_TOKEN")
        sys.exit(1)
    
    # Проверяем наличие OPENAI_API_KEY
    if not os.getenv("OPENAI_API_KEY"):
        print("Предупреждение: не задан OPENAI_API_KEY")
    
    # Импортируем и запускаем бота
    from interfaces.telegram_bot import run_bot
    run_bot(token)

if __name__ == "__main__":
    main() 
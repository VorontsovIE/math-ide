#!/usr/bin/env python3
"""
Тест для проверки работы разделенных промптов (system/user).
"""

import os
import sys
from pathlib import Path

# Добавляем корневую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from core.prompts import PromptManager
from core.gpt_client import GPTClient

def test_split_prompts():
    """Тестирует загрузку и форматирование разделенных промптов."""
    
    print("🧪 Тестирование разделенных промптов...")
    
    # Инициализируем менеджер промптов
    pm = PromptManager()
    
    # Тестируем загрузку разделенных промптов
    print("\n📁 Загрузка разделенных промптов:")
    
    try:
        # Тест 1: Генерация преобразований
        print("\n1️⃣ Тест генерации преобразований:")
        system_prompt, user_prompt = pm.load_split_prompt("generation")
        print(f"✅ System промпт загружен ({len(system_prompt)} символов)")
        print(f"✅ User промпт загружен ({len(user_prompt)} символов)")
        
        # Тест форматирования
        formatted_system, formatted_user = pm.format_split_prompt(
            system_prompt,
            user_prompt,
            current_state="2x + 4 = 10"
        )
        print(f"✅ System промпт отформатирован ({len(formatted_system)} символов)")
        print(f"✅ User промпт отформатирован ({len(formatted_user)} символов)")
        
        # Тест 2: Анализ ветвления
        print("\n2️⃣ Тест анализа ветвления:")
        system_prompt, user_prompt = pm.load_split_prompt("branching")
        print(f"✅ System промпт загружен ({len(system_prompt)} символов)")
        print(f"✅ User промпт загружен ({len(user_prompt)} символов)")
        
        # Тест 3: Проверка решения
        print("\n3️⃣ Тест проверки решения:")
        system_prompt, user_prompt = pm.load_split_prompt("check")
        print(f"✅ System промпт загружен ({len(system_prompt)} символов)")
        print(f"✅ User промпт загружен ({len(user_prompt)} символов)")
        
        # Тест 4: Верификация
        print("\n4️⃣ Тест верификации:")
        system_prompt, user_prompt = pm.load_split_prompt("verification")
        print(f"✅ System промпт загружен ({len(system_prompt)} символов)")
        print(f"✅ User промпт загружен ({len(user_prompt)} символов)")
        
        # Тест 5: Анализ прогресса
        print("\n5️⃣ Тест анализа прогресса:")
        system_prompt, user_prompt = pm.load_split_prompt("progress_analysis")
        print(f"✅ System промпт загружен ({len(system_prompt)} символов)")
        print(f"✅ User промпт загружен ({len(user_prompt)} символов)")
        
        print("\n🎉 Все тесты разделенных промптов прошли успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        return False
    
    return True

def test_gpt_integration():
    """Тестирует интеграцию с GPT (если доступен API ключ)."""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n⚠️  OPENAI_API_KEY не установлен, пропускаем тест GPT интеграции")
        return True
    
    print("\n🤖 Тестирование интеграции с GPT...")
    
    try:
        # Инициализируем клиенты
        pm = PromptManager()
        gpt_client = GPTClient(api_key=api_key)
        
        # Загружаем разделенные промпты
        system_prompt, user_prompt = pm.load_split_prompt("generation")
        
        # Форматируем промпты
        formatted_system, formatted_user = pm.format_split_prompt(
            system_prompt,
            user_prompt,
            current_state="x + 2 = 5"
        )
        
        print("📤 Отправка запроса к GPT...")
        
        # Отправляем запрос
        response = gpt_client.chat_completion(
            messages=[
                {"role": "system", "content": formatted_system},
                {"role": "user", "content": formatted_user},
            ],
            temperature=0.3,
        )
        
        print(f"✅ Получен ответ от GPT ({len(response.content)} символов)")
        print(f"📊 Использовано токенов: {response.usage.total_tokens}")
        
        # Проверяем, что ответ содержит JSON
        if "[" in response.content and "]" in response.content:
            print("✅ Ответ содержит JSON-массив")
        else:
            print("⚠️  Ответ не содержит JSON-массив")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании GPT интеграции: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Запуск тестов разделенных промптов...")
    
    success = True
    
    # Тест загрузки промптов
    success &= test_split_prompts()
    
    # Тест GPT интеграции
    success &= test_gpt_integration()
    
    if success:
        print("\n🎉 Все тесты прошли успешно!")
        sys.exit(0)
    else:
        print("\n❌ Некоторые тесты не прошли")
        sys.exit(1) 
from core.prompts import PromptManager
from core.types import get_transformation_types_markdown

pm = PromptManager()
prompt = pm.load_prompt('generation.md')
print('Промпт загружен')

try:
    formatted = pm.format_prompt(
        prompt, 
        current_state='x^2 - 3x + 2 = 0', 
        transformation_types=get_transformation_types_markdown(), 
        transformation_types_list=pm.load_prompt('transformation_types.md')
    )
    print('Форматирование успешно!')
except Exception as e:
    print(f'Ошибка форматирования: {e}') 
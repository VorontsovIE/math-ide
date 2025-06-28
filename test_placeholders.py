from core.prompts import PromptManager
import re

pm = PromptManager()
prompt = pm.load_prompt('generation.md')

matches = re.findall(r'\{([^}]+)\}', prompt)
print('Найденные плейсхолдеры:')
for i, m in enumerate(set(matches)):
    print(f'{i}: {repr(m)}') 
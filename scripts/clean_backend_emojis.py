"""
Clean emojis from backend python files.
"""
import re

def clean_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # Clean emoji followed by space if applicable
    content = re.sub(r'([\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55])\s?', '', content)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Cleaned {filepath}")

if __name__ == '__main__':
    targets = [
        'backend/app/modules/routing/department_config.py',
        'backend/app/modules/routing/service.py',
        'backend/app/api/v1/physician.py'
    ]
    for t in targets:
        clean_file(t)

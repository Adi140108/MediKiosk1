import re

for filename in ['frontend/index.html', 'frontend/physician.html']:
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    buttons = re.findall(r'<button[^>]*>.*?</button>', content, re.DOTALL)
    print(f'=== {filename}: {len(buttons)} buttons ===')
    for i, b in enumerate(buttons):
        clean = ' '.join(b.split())
        print(f"{i+1}: {ascii(clean[:120])}")

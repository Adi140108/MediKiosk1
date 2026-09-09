"""
Deep clean all remaining emojis across all frontend files.
"""
import re
import glob

emoji_pattern = re.compile(r'[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]')

def clean_file(filepath):
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    original = content
    # Clean emoji followed by space if applicable
    content = re.sub(r'([\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55])\s?', '', content)

    if content != original:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Cleaned emojis from {filepath}")
    else:
        print(f"No emojis in {filepath}")

if __name__ == '__main__':
    targets = [
        'frontend/js/i18n.js',
        'frontend/js/patient_intake.js',
        'frontend/js/physician_dashboard.js',
        'frontend/physician.html',
        'frontend/index.html',
        'frontend/diagnostics.html',
        'frontend/js/speech.js'
    ]
    for t in targets:
        clean_file(t)

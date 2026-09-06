import os
import shutil
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(ROOT_DIR, "frontend")
PUBLIC_DIR = os.path.join(ROOT_DIR, "public")
BACKEND_TEMPLATES_DIR = os.path.join(ROOT_DIR, "backend", "app", "templates")
EMBEDDED_ASSETS_FILE = os.path.join(BACKEND_TEMPLATES_DIR, "embedded_assets.py")

def sync():
    # 1. Sync frontend -> public
    if not os.path.exists(PUBLIC_DIR):
        os.makedirs(PUBLIC_DIR, exist_ok=True)
    
    for item in os.listdir(FRONTEND_DIR):
        s = os.path.join(FRONTEND_DIR, item)
        d = os.path.join(PUBLIC_DIR, item)
        if os.path.isdir(s):
            if os.path.exists(d):
                shutil.rmtree(d)
            shutil.copytree(s, d)
        else:
            shutil.copy2(s, d)
    print(f"Synced {FRONTEND_DIR} to {PUBLIC_DIR}")

    # Also copy logo.png to root if present
    logo_src = os.path.join(FRONTEND_DIR, "logo.png")
    if os.path.exists(logo_src):
        shutil.copy2(logo_src, os.path.join(ROOT_DIR, "logo.png"))
        shutil.copy2(logo_src, os.path.join(PUBLIC_DIR, "logo.png"))

    # 2. Read contents for embedded_assets.py
    def read_file(path):
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    index_html = read_file(os.path.join(FRONTEND_DIR, "index.html"))
    physician_html = read_file(os.path.join(FRONTEND_DIR, "physician.html"))
    diagnostics_html = read_file(os.path.join(FRONTEND_DIR, "diagnostics.html"))
    styles_css = read_file(os.path.join(FRONTEND_DIR, "css", "styles.css"))
    logo_svg = read_file(os.path.join(FRONTEND_DIR, "logo.svg"))

    js_assets = {}
    js_dir = os.path.join(FRONTEND_DIR, "js")
    if os.path.exists(js_dir):
        for js_file in os.listdir(js_dir):
            if js_file.endswith(".js"):
                js_assets[js_file] = read_file(os.path.join(js_dir, js_file))

    # Generate embedded_assets.py
    os.makedirs(BACKEND_TEMPLATES_DIR, exist_ok=True)
    with open(EMBEDDED_ASSETS_FILE, "w", encoding="utf-8") as f:
        f.write("# Generated automatically by scripts/sync_assets.py\n")
        f.write("import os\n\n")
        f.write(f"INDEX_HTML = {repr(index_html)}\n\n")
        f.write(f"PHYSICIAN_HTML = {repr(physician_html)}\n\n")
        f.write(f"DIAGNOSTICS_HTML = {repr(diagnostics_html)}\n\n")
        f.write(f"STYLES_CSS = {repr(styles_css)}\n\n")
        f.write(f"LOGO_SVG = {repr(logo_svg)}\n\n")
        f.write(f"JS_ASSETS = {repr(js_assets)}\n")

    print(f"Generated {EMBEDDED_ASSETS_FILE}")

if __name__ == "__main__":
    sync()

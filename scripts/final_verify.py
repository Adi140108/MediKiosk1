import urllib.request
import re

req = urllib.request.urlopen("http://127.0.0.1:8000/")
html = req.read().decode("utf-8")

checks = [
    ("navbar-audio-toggle present", 'id="navbar-audio-toggle"' in html),
    ("toggleMute wired to button", "SpeechManager.toggleMute()" in html),
    ("nav-audio-pill class", 'class="nav-audio-pill"' in html),
    ("no btn-hero-audio dupe", "btn-hero-audio" not in html),
    ("no per-step speaker buttons", "toggleSpeakForStep" not in html),
    ("keyboard-fab present", 'id="keyboard-fab"' in html),
    ("VirtualKeyboard.toggle on FAB", "VirtualKeyboard.toggle()" in html),
    ("virtual_keyboard.js script", "virtual_keyboard.js" in html),
    ("pain-slider present", 'id="pain-slider"' in html),
    ("pain-range-slider class", 'class="pain-range-slider"' in html),
    ("no old pain-num-btn grid", "pain-num-btn" not in html),
    ("hero-primary btn", "btn-hero-primary" in html),
    ("no stray emojis >=U+1F000", not bool(re.search(r"[\U0001F000-\U0001FAFF]", html))),
]

all_pass = True
for name, result in checks:
    status = "PASS" if result else "FAIL"
    if not result:
        all_pass = False
    print(f"[{status}] {name}")

print()
if all_pass:
    print("ALL CHECKS PASSED - Landing page is clean and functional")
else:
    print("SOME CHECKS FAILED - issues remain")

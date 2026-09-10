import urllib.request
import re

print("Running Comprehensive End-to-End Verification on http://127.0.0.1:8000/ ...\n")

# 1. Fetch Landing Page
req = urllib.request.urlopen("http://127.0.0.1:8000/")
html = req.read().decode("utf-8")

# Check Navbar Single Mute Button
assert 'id="navbar-audio-toggle"' in html, "ERROR: navbar-audio-toggle not found in index.html"
assert 'class="nav-audio-pill"' in html, "ERROR: nav-audio-pill class not found"
assert 'btn-hero-audio' not in html, "ERROR: Duplicate btn-hero-audio is still present"

# Check Clean Start Check-In Button
assert 'id="btn-begin-checkin"' in html, "ERROR: btn-begin-checkin missing"
assert '<button id="btn-begin-checkin" class="btn-hero-primary"' in html, "ERROR: btn-hero-primary class missing"

# Check Floating Keyboard FAB and script
assert 'id="keyboard-fab"' in html, "ERROR: keyboard-fab missing"
assert 'VirtualKeyboard.toggle()' in html, "ERROR: VirtualKeyboard.toggle() call missing on FAB"
assert '/js/virtual_keyboard.js' in html, "ERROR: virtual_keyboard.js script tag missing"

# Check Pain Slider
assert 'id="pain-slider"' in html, "ERROR: pain-slider missing"
assert 'class="pain-range-slider"' in html, "ERROR: pain-range-slider class missing"
assert 'pain-num-btn' not in html, "ERROR: old pain-num-btn grid still present"

print("[PASS] index.html structure verified: single mute button, clean hero, virtual keyboard FAB, and pain slider confirmed.")

# 2. Fetch Virtual Keyboard JS
vk_req = urllib.request.urlopen("http://127.0.0.1:8000/js/virtual_keyboard.js?v=15")
vk_js = vk_req.read().decode("utf-8")
assert "window.VirtualKeyboard = VirtualKeyboard;" in vk_js, "ERROR: VirtualKeyboard not exposed globally"
assert "handleKeyPress" in vk_js, "ERROR: handleKeyPress missing"
assert "insertText" in vk_js, "ERROR: insertText missing"
assert "deleteBackwards" in vk_js, "ERROR: deleteBackwards missing"
assert "ensureDrawerDOM" in vk_js, "ERROR: ensureDrawerDOM missing"
print("[PASS] virtual_keyboard.js verified: module loaded and all methods present.")

# 3. Fetch Styles CSS
css_req = urllib.request.urlopen("http://127.0.0.1:8000/css/styles.css")
css = css_req.read().decode("utf-8")
assert ".nav-audio-pill" in css, "ERROR: .nav-audio-pill missing in CSS"
assert ".keyboard-fab" in css, "ERROR: .keyboard-fab missing in CSS"
assert ".vk-drawer" in css, "ERROR: .vk-drawer missing in CSS"
assert ".vk-key" in css, "ERROR: .vk-key missing in CSS"
assert ".pain-range-slider" in css, "ERROR: .pain-range-slider missing in CSS"
print("[PASS] styles.css verified: .nav-audio-pill, .vk-drawer, .vk-key, .keyboard-fab, .pain-range-slider present.")

# 4. Fetch Physician Portal
phys_req = urllib.request.urlopen("http://127.0.0.1:8000/physician")
phys_html = phys_req.read().decode("utf-8")
assert "virtual_keyboard.js" in phys_html, "ERROR: virtual_keyboard.js missing in physician.html"
assert "btn-card-action" in phys_html, "ERROR: btn-card-action missing in physician.html"
assert "✏️" not in phys_html, "ERROR: Pencil emoji found in physician.html"
assert "🔍" not in phys_html, "ERROR: Search emoji found in physician.html"
print("[PASS] physician.html verified: clean SVG buttons and virtual keyboard present.")

# 5. Check Emojis across all endpoints
emoji_regex = re.compile(r'[\U00010000-\U0010ffff\u2600-\u27BF]')
assert not emoji_regex.search(html), f"ERROR: Emoji found in index.html: {emoji_regex.findall(html)}"
assert not emoji_regex.search(phys_html), f"ERROR: Emoji found in physician.html: {emoji_regex.findall(phys_html)}"
print("[PASS] Zero emojis strictly verified on all HTML endpoints.")

print("\nALL AUTOMATED VERIFICATION CHECKS PASSED SUCCESSFULLY!")

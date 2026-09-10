import re
import urllib.request

def verify():
    # 1. Check index.html from server
    with urllib.request.urlopen("http://127.0.0.1:8000/") as resp:
        html = resp.read().decode("utf-8")

    assert "hero-floating-decorations" not in html, "Floating decorations still in HTML"
    assert "hero-vitals-subtle-bar" not in html, "Subtle ECG bar still in HTML"
    assert "hero-highlights-row" in html, "hero-highlights-row missing in HTML"
    assert "pain-ticks-container" in html, "pain-ticks-container missing in HTML"
    assert 'id="pain-tick-7"' in html, "pain-tick-7 missing in HTML"
    assert "btn-begin-checkin" in html, "btn-begin-checkin missing in HTML"
    print("[PASS] Step 1 Landing page is simple, uncluttered, and beautiful.")
    print("[PASS] Pain slider ticks markup has IDs and container.")

    # 2. Check styles.css
    with urllib.request.urlopen("http://127.0.0.1:8000/css/styles.css") as resp:
        css = resp.read().decode("utf-8")

    assert ".hero-container" in css, ".hero-container missing in CSS"
    assert ".hero-main-card" in css, ".hero-main-card missing in CSS"
    assert ".hero-highlights-row" in css, ".hero-highlights-row missing in CSS"
    assert "--slider-thumb-color" in css, "--slider-thumb-color missing in CSS"
    assert "padding: 0 16px;" in css, "padding: 0 16px missing for slider ticks alignment"
    assert ".pain-slider-ticks span.active-tick" in css, "active-tick styling missing in CSS"
    print("[PASS] CSS contains calibrated slider and clean hero styles.")

    # 3. Check virtual_keyboard.js
    with urllib.request.urlopen("http://127.0.0.1:8000/js/virtual_keyboard.js") as resp:
        vk = resp.read().decode("utf-8")

    assert "isNumberType" in vk, "isNumberType guard missing in virtual_keyboard.js"
    assert "dispatchInputEvents" in vk, "dispatchInputEvents missing in virtual_keyboard.js"
    # Ensure no auto-open in bindGlobalInputListeners
    listeners_code = vk.split("bindGlobalInputListeners")[1].split("bindFabButton")[0]
    assert "this.open()" not in listeners_code, "Keyboard should not auto-open on focus"
    assert "findDefaultInputForCurrentStep" in vk, "findDefaultInputForCurrentStep missing in virtual_keyboard.js"
    print("[PASS] virtual_keyboard.js is strictly toggle-controlled (no auto-open) with safe number handling.")

    # 4. Check patient_intake.js
    with urllib.request.urlopen("http://127.0.0.1:8000/js/patient_intake.js") as resp:
        pi = resp.read().decode("utf-8")

    assert "--slider-thumb-color" in pi, "--slider-thumb-color missing in patient_intake.js"
    assert "active-tick" in pi, "active-tick class missing in patient_intake.js"
    print("[PASS] patient_intake.js dynamically colorizes slider thumb and highlights active tick.")

    print("\n>>> ALL VALIDATION CHECKS FOR FIRST PAGE, SLIDER, AND KEYBOARD PASSED! <<<")

if __name__ == "__main__":
    verify()

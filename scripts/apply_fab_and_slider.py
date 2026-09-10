import os
import re

css_path = r"c:\Users\adity\MediKiosk1\frontend\css\styles.css"
html_path = r"c:\Users\adity\MediKiosk1\frontend\index.html"

# 1. Update CSS
with open(css_path, "r", encoding="utf-8") as f:
    css_content = f.read()

slider_css = """
.pain-range-slider {
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 14px;
  border-radius: 9999px;
  background: linear-gradient(90deg, #10B981 0%, #FBBF24 35%, #F97316 65%, #EF4444 100%);
  outline: none;
  cursor: pointer;
  margin: 1.5rem 0 1rem 0;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.15);
}

/* Chrome, Safari, Edge, Opera */
.pain-range-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #FFFFFF;
  border: 4px solid var(--primary-color, #10b981);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2), inset 0 2px 4px rgba(255,255,255,0.5);
  cursor: grab;
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), border-color 0.2s ease, box-shadow 0.2s ease;
}

.pain-range-slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.25), inset 0 2px 4px rgba(255,255,255,0.5);
}

.pain-range-slider::-webkit-slider-thumb:active {
  cursor: grabbing;
  transform: scale(1.05);
}

/* Firefox */
.pain-range-slider::-moz-range-thumb {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: #FFFFFF;
  border: 4px solid var(--primary-color, #10b981);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2), inset 0 2px 4px rgba(255,255,255,0.5);
  cursor: grab;
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), border-color 0.2s ease;
}

.pain-range-slider::-moz-range-thumb:hover {
  transform: scale(1.15);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.25), inset 0 2px 4px rgba(255,255,255,0.5);
}

.pain-range-slider::-moz-range-thumb:active {
  cursor: grabbing;
  transform: scale(1.05);
}
"""

# Replace the existing slider CSS from `.pain-range-slider {` to `.pain-slider-ticks {` (exclusive)
pattern = re.compile(r'\.pain-range-slider \{.*?(?=\.pain-slider-ticks \{)', re.DOTALL)
if pattern.search(css_content):
    css_content = pattern.sub(slider_css.strip() + "\n\n", css_content)

keyboard_fab_css = """

/* Virtual Keyboard FAB */
.keyboard-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  color: #475569;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 1000;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.keyboard-fab:hover {
  background: rgba(255, 255, 255, 0.95);
  transform: translateY(-4px) scale(1.08);
  box-shadow: 0 8px 24px rgba(13, 148, 136, 0.2);
  color: #0D9488;
  border-color: #0D9488;
}

.keyboard-fab:active {
  transform: translateY(0) scale(0.95);
}
"""

if "Virtual Keyboard FAB" not in css_content:
    css_content += keyboard_fab_css

with open(css_path, "w", encoding="utf-8") as f:
    f.write(css_content)

# 2. Update HTML
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

fab_html = """
  <!-- Virtual Keyboard FAB -->
  <button id="keyboard-fab" class="keyboard-fab" title="Open On-Screen Keyboard" onclick="if(window.PatientIntake) { console.log('Keyboard button clicked'); }">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
      <rect x="2" y="4" width="20" height="16" rx="2" ry="2"></rect>
      <line x1="6" y1="8" x2="6" y2="8"></line>
      <line x1="10" y1="8" x2="10" y2="8"></line>
      <line x1="14" y1="8" x2="14" y2="8"></line>
      <line x1="18" y1="8" x2="18" y2="8"></line>
      <line x1="6" y1="12" x2="6" y2="12"></line>
      <line x1="10" y1="12" x2="10" y2="12"></line>
      <line x1="14" y1="12" x2="14" y2="12"></line>
      <line x1="18" y1="12" x2="18" y2="12"></line>
      <line x1="7" y1="16" x2="17" y2="16"></line>
    </svg>
  </button>

  <!-- JavaScript Modules -->
"""

if "id=\"keyboard-fab\"" not in html_content:
    html_content = html_content.replace("  <!-- JavaScript Modules -->", fab_html)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

print("Applied CSS fixes and added FAB to HTML successfully.")

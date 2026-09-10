with open('frontend/css/styles.css', 'r', encoding='utf-8') as f:
    css = f.read()

slider_css = """
/* ── Pain Severity Sliding Bar ────────────────────────────── */
.pain-slider-card {
  margin-bottom: 1.75rem;
  background: var(--bg-surface, #FFFFFF);
  border-radius: var(--radius-sm, 12px);
  padding: 1.5rem;
  border: 1px solid var(--border-color, #E2E8F0);
  box-shadow: var(--shadow-sm, 0 1px 3px rgba(0,0,0,0.05));
}

.pain-badge-display {
  display: inline-flex;
  align-items: center;
  font-family: 'Outfit', sans-serif;
  font-size: 0.88rem;
  font-weight: 700;
  padding: 0.35rem 0.95rem;
  border-radius: var(--radius-pill, 9999px);
  transition: all 0.2s ease;
  background: #ffedd5;
  color: #9a3412;
  border: 1px solid #f97316;
}

.pain-slider-wrapper {
  position: relative;
  padding: 0.75rem 0.25rem 0.5rem 0.25rem;
}

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
  border: 4px solid #0D9488;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2), inset 0 2px 4px rgba(255,255,255,0.5);
  cursor: grab;
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), border-color 0.2s ease, box-shadow 0.2s ease;
}

.pain-range-slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
  box-shadow: 0 6px 16px rgba(13, 148, 136, 0.35), inset 0 2px 4px rgba(255,255,255,0.5);
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
  border: 4px solid #0D9488;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2), inset 0 2px 4px rgba(255,255,255,0.5);
  cursor: grab;
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1), border-color 0.2s ease;
}

.pain-range-slider::-moz-range-thumb:hover {
  transform: scale(1.15);
  box-shadow: 0 6px 16px rgba(13, 148, 136, 0.35);
}

.pain-slider-ticks {
  display: flex;
  justify-content: space-between;
  padding: 0 4px;
  margin-top: 0.5rem;
  user-select: none;
}

.pain-slider-ticks span {
  font-family: 'Outfit', sans-serif;
  font-size: 0.85rem;
  font-weight: 700;
  color: #64748B;
  display: flex;
  flex-direction: column;
  align-items: center;
  cursor: pointer;
  transition: color 0.15s ease;
}

.pain-slider-ticks span small {
  font-size: 0.65rem;
  font-weight: 600;
  color: #94A3B8;
  margin-top: 2px;
}

.pain-slider-ticks span:hover {
  color: #0D9488;
}
"""

if '.pain-range-slider' not in css:
    css += "\n" + slider_css
    with open('frontend/css/styles.css', 'w', encoding='utf-8') as f:
        f.write(css)
    print("Added pain-range-slider to frontend/css/styles.css")

"""
Complete update script to:
1. Standardize all button styling across frontend/index.html and frontend/physician.html (zero emojis, sleek SVGs).
2. Wire up the universal Single Mute Button in the navbar with robust audio state handling.
3. Implement and wire the On-Screen Virtual Keyboard and floating FAB.
4. Add all required CSS for navbar mute pill, virtual keyboard drawer, clean buttons, and slider.
"""
import re
import os

def update_styles_css():
    path = "frontend/css/styles.css"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Navbar Audio Mute Pill styles
    nav_audio_css = """
/* ── Universal Navbar Audio Guidance Pill ───────────────────── */
.nav-audio-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 0.35rem 0.95rem;
  background: rgba(13, 148, 136, 0.08);
  border: 1.5px solid rgba(13, 148, 136, 0.25);
  color: #0F766E;
  border-radius: var(--radius-pill, 9999px);
  font-family: 'Outfit', sans-serif;
  font-size: 0.8rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  user-select: none;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.nav-audio-pill:hover {
  background: rgba(13, 148, 136, 0.16);
  border-color: #0D9488;
  color: #0D9488;
  transform: translateY(-1px);
}

.nav-audio-pill:active {
  transform: translateY(0);
}

.nav-audio-pill.is-playing {
  background: #ECFDF5;
  border-color: #10B981;
  color: #047857;
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.15);
}

.nav-audio-pill.is-muted {
  background: #F1F5F9 !important;
  border-color: #CBD5E1 !important;
  color: #64748B !important;
  box-shadow: none !important;
}

.nav-audio-pill svg {
  flex-shrink: 0;
}

/* ── Hero Buttons ────────────────────────────────────────────── */
.hero-cta-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.btn-hero-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 52px;
  padding: 0 2.2rem;
  background: linear-gradient(135deg, #0D9488 0%, #059669 100%);
  color: #FFFFFF;
  border: none;
  border-radius: var(--radius-pill, 9999px);
  font-family: 'Outfit', sans-serif;
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  cursor: pointer;
  transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 4px 14px rgba(13, 148, 136, 0.3);
}

.btn-hero-primary:hover {
  background: linear-gradient(135deg, #0F766E 0%, #047857 100%);
  transform: translateY(-2px);
  box-shadow: 0 8px 22px rgba(13, 148, 136, 0.4);
}

.btn-hero-primary:active {
  transform: translateY(0);
  box-shadow: 0 2px 6px rgba(13, 148, 136, 0.25);
}

/* ── Virtual Keyboard Drawer & Floating FAB ─────────────────── */
.keyboard-fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 52px;
  height: 52px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(226, 232, 240, 0.9);
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.12);
  color: #475569;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 10000;
  transition: all 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.keyboard-fab:hover {
  background: #FFFFFF;
  transform: translateY(-3px) scale(1.08);
  box-shadow: 0 8px 24px rgba(13, 148, 136, 0.25);
  color: #0D9488;
  border-color: #0D9488;
}

.keyboard-fab:active {
  transform: translateY(0) scale(0.95);
}

.keyboard-fab.is-active {
  background: #0D9488 !important;
  color: #FFFFFF !important;
  border-color: #0D9488 !important;
  box-shadow: 0 8px 24px rgba(13, 148, 136, 0.45) !important;
}

.vk-drawer {
  position: fixed;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%) translateY(105%);
  width: 100%;
  max-width: 860px;
  background: rgba(15, 23, 42, 0.94);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-bottom: none;
  border-radius: 20px 20px 0 0;
  box-shadow: 0 -12px 40px rgba(0, 0, 0, 0.45);
  z-index: 10050;
  padding: 0.85rem 1rem 1.25rem 1rem;
  box-sizing: border-box;
  transition: transform 0.32s cubic-bezier(0.16, 1, 0.3, 1);
  user-select: none;
}

.vk-drawer.vk-open {
  transform: translateX(-50%) translateY(0);
}

.vk-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.vk-target-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #94A3B8;
  font-family: 'Outfit', sans-serif;
  font-size: 0.82rem;
  font-weight: 600;
}

.vk-beacon {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #10B981;
  box-shadow: 0 0 8px #10B981;
}

.vk-target-icon {
  color: #2DD4BF;
}

.vk-target-name {
  color: #F8FAFC;
  letter-spacing: 0.01em;
}

.vk-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

.vk-action-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 0.3rem 0.75rem;
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: #CBD5E1;
  font-family: 'Outfit', sans-serif;
  font-size: 0.78rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
}

.vk-action-btn:hover {
  background: rgba(255, 255, 255, 0.16);
  color: #FFFFFF;
}

.vk-btn-hide:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: rgba(239, 68, 68, 0.4);
  color: #FCA5A5;
}

.vk-keyboard-body {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.vk-row {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.vk-key {
  flex: 1;
  min-height: 48px;
  min-width: 32px;
  max-width: 68px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 8px;
  color: #F8FAFC;
  font-family: 'Outfit', sans-serif;
  font-size: 1.15rem;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.15s ease, transform 0.08s ease;
  touch-action: manipulation;
}

.vk-key:hover {
  background: rgba(255, 255, 255, 0.18);
  border-color: rgba(255, 255, 255, 0.25);
}

.vk-key:active {
  background: rgba(13, 148, 136, 0.35);
  border-color: #2DD4BF;
  transform: scale(0.95);
}

.vk-key-special {
  flex: 1.35;
  background: rgba(255, 255, 255, 0.05);
  font-size: 0.88rem;
}

.vk-key-shift.vk-key-active {
  background: #0D9488 !important;
  border-color: #2DD4BF !important;
  color: #FFFFFF !important;
  box-shadow: 0 0 12px rgba(13, 148, 136, 0.5);
}

.vk-key-space {
  flex: 4.5 !important;
  max-width: 380px !important;
  font-size: 0.85rem !important;
  color: #94A3B8 !important;
}

.vk-key-done {
  flex: 1.8 !important;
  background: linear-gradient(135deg, #0D9488, #059669) !important;
  border: 1px solid #2DD4BF !important;
  color: #FFFFFF !important;
  font-weight: 700 !important;
  gap: 5px;
}

.vk-key-done:hover {
  background: linear-gradient(135deg, #0F766E, #047857) !important;
}
"""

    if ".nav-audio-pill" not in content:
        content += "\n" + nav_audio_css

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated styles.css with nav-audio-pill and virtual keyboard styles")


def update_speech_js():
    path = "frontend/js/speech.js"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update updateButtonStates to use clean SVG and update #navbar-audio-toggle
    old_update_btn = """  updateButtonStates(state) {
    const buttons = document.querySelectorAll('#btn-speak-question, .btn-icon-round');
    buttons.forEach(btn => {
      if (state === 'playing') {
        btn.innerHTML = '🔊';
        btn.classList.add('is-playing');
        btn.classList.remove('is-muted');
        btn.title = "Audio Playing — Tap to Mute";
      } else if (state === 'muted' || this.isMuted) {
        btn.innerHTML = '🔇';
        btn.classList.remove('is-playing');
        btn.classList.add('is-muted');
        btn.title = "Audio Muted — Tap to Unmute & Listen";
      } else {
        btn.innerHTML = '🔊';
        btn.classList.remove('is-playing');
        btn.classList.remove('is-muted');
        btn.title = "Listen with Audio / Voice";
      }
    });
  },"""

    new_update_btn = """  updateButtonStates(state) {
    const playSvg = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>';
    const muteSvg = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><line x1="23" y1="9" x2="17" y2="15"></line><line x1="17" y1="9" x2="23" y2="15"></line></svg>';

    const buttons = document.querySelectorAll('#btn-speak-question, .btn-icon-round');
    buttons.forEach(btn => {
      if (state === 'playing') {
        btn.innerHTML = playSvg;
        btn.classList.add('is-playing');
        btn.classList.remove('is-muted');
        btn.title = "Audio Playing";
      } else if (state === 'muted' || this.isMuted) {
        btn.innerHTML = muteSvg;
        btn.classList.remove('is-playing');
        btn.classList.add('is-muted');
        btn.title = "Audio Muted";
      } else {
        btn.innerHTML = playSvg;
        btn.classList.remove('is-playing');
        btn.classList.remove('is-muted');
        btn.title = "Listen with Audio / Voice";
      }
    });

    this.updateNavbarAudioUI(state);
  },

  updateNavbarAudioUI(state = null) {
    const toggleBtn = document.getElementById('navbar-audio-toggle');
    if (!toggleBtn) return;

    const playSvg = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>';
    const muteSvg = '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><line x1="23" y1="9" x2="17" y2="15"></line><line x1="17" y1="9" x2="23" y2="15"></line></svg>';

    if (this.isMuted) {
      toggleBtn.className = 'nav-audio-pill is-muted';
      toggleBtn.innerHTML = `${muteSvg}<span>Muted</span>`;
      toggleBtn.title = "Audio Muted — Click to Enable Voice Guidance";
    } else if (state === 'playing' || this.isSpeaking) {
      toggleBtn.className = 'nav-audio-pill is-playing';
      toggleBtn.innerHTML = `${playSvg}<span>Speaking...</span>`;
      toggleBtn.title = "Voice Guidance Playing — Click to Mute";
    } else {
      toggleBtn.className = 'nav-audio-pill';
      toggleBtn.innerHTML = `${playSvg}<span>Voice On</span>`;
      toggleBtn.title = "Voice Guidance Active — Click to Mute";
    }
  },

  toggleMute() {
    this.isMuted = !this.isMuted;
    if (this.isMuted) {
      this.stopAllAudio();
      this.updateNavbarAudioUI('muted');
    } else {
      this.updateNavbarAudioUI('idle');
      // Speak current step guidance cleanly without double-talk
      const currentStep = (window.PatientIntake && window.PatientIntake.currentStep) ? window.PatientIntake.currentStep : 1;
      const targetLang = (window.PatientIntake && window.PatientIntake.language) ? window.PatientIntake.language : (this.currentLanguage || 'en');
      this.speakStepGuidance(currentStep, targetLang);
    }
    return !this.isMuted;
  },"""

    if old_update_btn in content:
        content = content.replace(old_update_btn, new_update_btn)
    else:
        print("Warning: old_update_btn exact match not found in speech.js, searching alternative")
        content = re.sub(
            r'updateButtonStates\(state\)\s*\{.*?\}\,',
            new_update_btn + ",",
            content,
            flags=re.DOTALL
        )

    # 2. In toggleSpeak, call toggleMute()
    old_toggle_speak = """  toggleSpeak(text = null, lang = null) {
    if (this.isMuted) {
      // User tapped while muted -> Unmute and speak
      this.isMuted = false;
      const targetLang = lang || this.currentLanguage || 'en';
      const toSpeak = text || this.lastSpokenText || this.getStepGuidanceText(1, targetLang);
      this.speakText(toSpeak, targetLang);
      return true;
    } else {
      // User tapped while unmuted / playing -> Mute completely
      this.isMuted = true;
      this.isSpeaking = false;
      this.stopAllAudio();
      this.updateButtonStates('muted');
      return false;
    }
  },"""

    new_toggle_speak = """  toggleSpeak(text = null, lang = null) {
    return this.toggleMute();
  },"""

    if old_toggle_speak in content:
        content = content.replace(old_toggle_speak, new_toggle_speak)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated speech.js with clean SVG icons, updateNavbarAudioUI, and toggleMute")


def update_index_html():
    path = "frontend/index.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Navbar Audio Mute Button
    if 'id="navbar-audio-toggle"' not in content:
        nav_pattern = r'(<div class="lang-pill-indicator"[^>]*>.*?</div>\s*</div>\s*</nav>)'
        replacement = """      <!-- Single Universal Audio Guidance / Mute Toggle -->
      <button id="navbar-audio-toggle" class="nav-audio-pill" onclick="SpeechManager.toggleMute()" title="Toggle Voice Guidance" type="button" aria-label="Toggle Voice Guidance">
        <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon>
          <path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path>
        </svg>
        <span>Voice On</span>
      </button>
    </div>
  </nav>"""
        content = re.sub(r'</div>\s*</nav>', replacement, content, count=1)

    # 2. Hero Start Check-In Button: remove ⚡ emoji, keep clean SVG arrow
    content = re.sub(
        r'<button id="btn-begin-checkin" class="btn-hero-primary" onclick="goToStep\(2\)">\s*<span style="font-size:1.3rem;">⚡</span>\s*<span data-i18n="begin_checkin">Start Patient Check-In</span>\s*<svg[^>]*>.*?</svg>\s*</button>',
        """<button id="btn-begin-checkin" class="btn-hero-primary" onclick="goToStep(2)">
              <span data-i18n="begin_checkin">Start Patient Check-In</span>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <line x1="5" y1="12" x2="19" y2="12"></line>
                <polyline points="12 5 19 12 12 19"></polyline>
              </svg>
            </button>""",
        content,
        flags=re.DOTALL
    )

    # 3. Remove duplicate hero audio button from hero card
    content = re.sub(
        r'<button class="btn-hero-audio"[^>]*>.*?</button>',
        '',
        content,
        flags=re.DOTALL
    )

    # 4. Remove duplicate btn-icon-round buttons from step headers 2, 3, 4, 5, 6
    content = re.sub(
        r'<button class="btn-icon-round" onclick="SpeechManager\.toggleSpeakForStep\(\d\)"[^>]*>.*?</button>',
        '',
        content,
        flags=re.DOTALL
    )

    # 5. Clean Step 1 features and trust icons
    content = content.replace('<span>🏥</span>\n              <span>OPD Smart Self Check-In', '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21h18"></path><path d="M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16"></path><line x1="12" y1="7" x2="12" y2="13"></line><line x1="9" y1="10" x2="15" y2="10"></line></svg>\n              <span>OPD Smart Self Check-In')
    content = content.replace('<span id="mobile-step-icon">📍</span>', '<span id="mobile-step-icon"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="10" r="3"></circle><path d="M12 2a8 8 0 0 0-8 8c0 5.25 8 12 8 12s8-6.75 8-12a8 8 0 0 0-8-8z"></path></svg></span>')
    content = content.replace('<span>📁</span> <span>Browse Files</span>', '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg> <span>Browse Files</span>')
    content = content.replace('<span>📷</span> <span>Live Camera</span>', '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg> <span>Live Camera</span>')
    content = content.replace('<span>🔄</span> <span>Retake Photo</span>', '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"></polyline><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"></path></svg> <span>Retake Photo</span>')
    content = content.replace('<span>✓</span> <span>Use Document</span>', '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg> <span>Use Document</span>')
    content = content.replace('⚠️ Camera access was not granted or is unavailable on this device.', '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:text-bottom; margin-right:4px;"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg> Camera access was not granted or is unavailable on this device.')
    content = content.replace('📁 Use System File / Photo Picker', '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:text-bottom; margin-right:4px;"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg> Use System File / Photo Picker')
    content = content.replace('✓ Photo Captured', '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:text-bottom; margin-right:4px;"><polyline points="20 6 9 17 4 12"></polyline></svg> Photo Captured')

    # 6. Step 5 Pain severity slider replacement (if not already replaced)
    if 'id="pain-slider"' not in content:
        old_pain_html_pattern = re.compile(
            r'<!-- 5\. Pain Severity Scale -->.*?<input type="hidden" id="pain-range" value="7">\s*</div>',
            re.DOTALL
        )
        new_pain_html = """<!-- 5. Pain Severity Scale (Sliding Bar) -->
        <div class="pain-slider-card">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:1rem; flex-wrap:wrap; gap:0.5rem;">
            <div>
              <label class="form-label" for="pain-slider" style="margin:0; font-weight:700; color:var(--brand-primary); font-size:1.02rem;" data-i18n="pain_level">
                Symptom Severity / Pain Scale
              </label>
              <p style="font-size:0.8rem; color:var(--text-muted); margin:0.25rem 0 0 0;">
                Drag the sliding bar to indicate your pain level (1 = Very Mild, 10 = Critical / Emergency):
              </p>
            </div>
            <span id="pain-val-display" class="pain-badge-display">
              Level 7 — Severe Pain
            </span>
          </div>

          <div class="pain-slider-wrapper">
            <input type="range" id="pain-slider" class="pain-range-slider" min="1" max="10" step="1" value="7"
              oninput="PatientIntake.onPainSliderInput(this.value)"
              onchange="PatientIntake.selectPainLevel(this.value)"
              aria-label="Pain Severity Slider">
            <input type="hidden" id="pain-range" value="7">

            <div class="pain-slider-ticks">
              <span onclick="PatientIntake.setSliderVal(1)">1<small>Mild</small></span>
              <span onclick="PatientIntake.setSliderVal(2)">2</span>
              <span onclick="PatientIntake.setSliderVal(3)">3</span>
              <span onclick="PatientIntake.setSliderVal(4)">4</span>
              <span onclick="PatientIntake.setSliderVal(5)">5<small>Moderate</small></span>
              <span onclick="PatientIntake.setSliderVal(6)">6</span>
              <span onclick="PatientIntake.setSliderVal(7)">7</span>
              <span onclick="PatientIntake.setSliderVal(8)">8<small>Severe</small></span>
              <span onclick="PatientIntake.setSliderVal(9)">9</span>
              <span onclick="PatientIntake.setSliderVal(10)">10<small>Critical</small></span>
            </div>
          </div>
        </div>"""
        content = old_pain_html_pattern.sub(new_pain_html, content)

    # 7. Wire FAB to VirtualKeyboard.toggle()
    content = re.sub(
        r'<button id="keyboard-fab"[^>]*>.*?</button>',
        """<button id="keyboard-fab" class="keyboard-fab" title="Open On-Screen Keyboard" onclick="if(window.VirtualKeyboard){VirtualKeyboard.toggle();}">
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
      stroke-linecap="round" stroke-linejoin="round">
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
  </button>""",
        content,
        flags=re.DOTALL
    )

    # 8. Include virtual_keyboard.js script
    if 'virtual_keyboard.js' not in content:
        content = content.replace(
            '<script src="/js/patient_intake.js?v=14"></script>',
            '<script src="/js/virtual_keyboard.js?v=15"></script>\n  <script src="/js/patient_intake.js?v=15"></script>'
        )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated index.html with single mute button, virtual keyboard FAB wiring, clean buttons, and slider")


def update_physician_html():
    path = "frontend/physician.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Replace ✏️ Edit Summary
    edit_summary_svg = '<svg class="btn-icon-svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:5px;"><path d="M12 20h9"></path><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"></path></svg><span>Edit Summary</span>'
    content = content.replace('✏️ Edit Summary', edit_summary_svg)

    # Replace 🔍 Explore Ayurvedic RAG
    rag_svg = '<svg class="btn-icon-svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right:5px;"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg><span>Explore Ayurvedic RAG Knowledge Base</span>'
    content = content.replace('🔍 Explore Ayurvedic RAG Knowledge Base', rag_svg)

    # Replace any 🩺
    content = content.replace('<span>🩺</span>', '')

    # Include virtual keyboard script in physician.html too
    if 'virtual_keyboard.js' not in content:
        content = content.replace(
            '<script src="/js/physician_dashboard.js"></script>',
            '<script src="/js/virtual_keyboard.js?v=15"></script>\n  <script src="/js/physician_dashboard.js"></script>'
        )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated physician.html with clean SVG buttons and virtual keyboard")


def update_physician_dashboard_js():
    path = "frontend/js/physician_dashboard.js"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace(
        '<span>📝 Show/Hide Full Raw OCR Text ▼</span>',
        '<span>Show/Hide Full Raw OCR Text</span>'
    )
    content = content.replace(
        '🔍 Preview Document Scan',
        'Preview Document Scan'
    )

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Updated physician_dashboard.js")


if __name__ == "__main__":
    update_styles_css()
    update_speech_js()
    update_index_html()
    update_physician_html()
    update_physician_dashboard_js()

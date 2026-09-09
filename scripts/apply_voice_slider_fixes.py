"""
Apply fixes for:
1. Double voice on landing page & speech watchdog race condition
2. Make only one mute button (navbar only, remove hero and step header audio buttons)
3. Make the symptom severity option a smooth sliding bar
"""
import re

def update_speech_js():
    path = "frontend/js/speech.js"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. In speakText, ensure robust cancellation of any existing speech/audio
    # and fix the watchdog race condition where browser synth + server audio played together
    old_watchdog_block = '''        if (this._speechWatchdog) clearInterval(this._speechWatchdog);
        let watchdogTicks = 0;
        this._speechWatchdog = setInterval(() => {
          watchdogTicks++;
          if (this.synth && this.synth.speaking) {
            try { this.synth.resume(); } catch(e) {}
          } else if (watchdogTicks <= 1 && !audioStarted) {
            clearInterval(this._speechWatchdog);
            this._speechWatchdog = null;
            console.warn("Browser voice produced no audio for", targetLang, "- falling back to server TTS");
            this._playServerAudioStream(text, targetLang, onEndCallback);
          } else {
            clearInterval(this._speechWatchdog);
            this._speechWatchdog = null;
          }
        }, 800);'''

    new_watchdog_block = '''        if (this._speechWatchdog) {
          clearInterval(this._speechWatchdog);
          this._speechWatchdog = null;
        }
        let watchdogTicks = 0;
        this._speechWatchdog = setInterval(() => {
          watchdogTicks++;
          // Keep browser speech active if paused
          if (this.synth && (this.synth.speaking || this.synth.pending)) {
            try { this.synth.resume(); } catch(e) {}
            if (audioStarted || watchdogTicks >= 4) {
              clearInterval(this._speechWatchdog);
              this._speechWatchdog = null;
            }
          } else if (watchdogTicks >= 3 && !audioStarted) {
            // Truly stalled after 2.4s without starting speech
            clearInterval(this._speechWatchdog);
            this._speechWatchdog = null;
            if (this.synth) {
              try { this.synth.cancel(); } catch(e) {}
            }
            console.warn("Browser voice stalled for", targetLang, "- falling back to server TTS");
            this._playServerAudioStream(text, targetLang, onEndCallback);
          } else if (audioStarted) {
            clearInterval(this._speechWatchdog);
            this._speechWatchdog = null;
          }
        }, 800);'''

    if old_watchdog_block in content:
        content = content.replace(old_watchdog_block, new_watchdog_block)
        print("Updated speech watchdog in speech.js")
    else:
        print("Warning: old_watchdog_block not found in speech.js!")

    # 2. In _playServerAudioStream, ensure this.synth.cancel() is ALWAYS called
    old_play_server = '''  _playServerAudioStream(text, targetLang, onEndCallback) {
    try {
      this.updateButtonStates('playing');
      this.isSpeaking = true;

      const streamUrl = `/api/v1/speech/stream?text=${encodeURIComponent(text.trim())}&language=${encodeURIComponent(targetLang)}`;
      const audio = new Audio(streamUrl);
      this.currentAudio = audio;'''

    new_play_server = '''  _playServerAudioStream(text, targetLang, onEndCallback) {
    try {
      // Strictly cancel browser speech synthesis before server audio starts
      if (this.synth) {
        try { this.synth.cancel(); } catch(e) {}
      }
      if (this.currentAudio) {
        try {
          this.currentAudio.pause();
          this.currentAudio.currentTime = 0;
        } catch(e) {}
        this.currentAudio = null;
      }

      this.updateButtonStates('playing');
      this.isSpeaking = true;

      const streamUrl = `/api/v1/speech/stream?text=${encodeURIComponent(text.trim())}&language=${encodeURIComponent(targetLang)}`;
      const audio = new Audio(streamUrl);
      this.currentAudio = audio;'''

    if old_play_server in content:
        content = content.replace(old_play_server, new_play_server)
        print("Updated _playServerAudioStream in speech.js")
    else:
        print("Warning: old_play_server not found in speech.js!")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved {path}")


def update_patient_intake_js():
    path = "frontend/js/patient_intake.js"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Clean welcome speech trigger to prevent double firing
    old_welcome = '''    // 2. IMMEDIATE WELCOMING AUTO-SPEECH
    const triggerWelcomeSpeech = () => {
      try {
        if (this.currentStep === 1 && !this.hasSpokenInitialWelcome && typeof SpeechManager !== "undefined" && !SpeechManager.isMuted) {
          this.hasSpokenInitialWelcome = true;
          if (SpeechManager.resumeAudioAndSpeak) {
            SpeechManager.resumeAudioAndSpeak(1, this.language);
          }
        }
      } catch (e) {}
    };

    // Immediate attempt on load (50ms)
    setTimeout(triggerWelcomeSpeech, 50);
    setTimeout(triggerWelcomeSpeech, 250);

    // Unlock audio instantly on any first micro-interaction
    const unlockAndSpeak = () => {
      try {
        if (typeof SpeechManager !== "undefined") {
          if (SpeechManager.synth) SpeechManager.synth.resume();
          const ctx = SpeechManager.getAudioContext();
          if (ctx && ctx.state === 'suspended') ctx.resume();
        }
      } catch(e) {}
      triggerWelcomeSpeech();
    };

    ['click', 'touchstart', 'touchend', 'pointerdown', 'pointermove', 'mousemove', 'keydown', 'scroll', 'focus'].forEach(evt => {
      try {
        window.addEventListener(evt, unlockAndSpeak, { once: true, passive: true });
      } catch (e) {}
    });'''

    new_welcome = '''    // 2. SINGLE WELCOMING AUTO-SPEECH (Guarded against duplicate execution)
    let welcomeTriggered = false;
    const triggerWelcomeSpeech = () => {
      if (welcomeTriggered || this.hasSpokenInitialWelcome) return;
      if (this.currentStep !== 1) return;
      if (typeof SpeechManager !== "undefined" && SpeechManager.isMuted) return;

      welcomeTriggered = true;
      this.hasSpokenInitialWelcome = true;

      try {
        if (typeof SpeechManager !== "undefined") {
          if (SpeechManager.synth) SpeechManager.synth.resume();
          const ctx = SpeechManager.getAudioContext();
          if (ctx && ctx.state === 'suspended') ctx.resume();
          if (SpeechManager.resumeAudioAndSpeak) {
            SpeechManager.resumeAudioAndSpeak(1, this.language);
          }
        }
      } catch (e) {
        console.warn("Welcome speech notice:", e);
      }
    };

    // Single delayed trigger after DOM is settled
    setTimeout(triggerWelcomeSpeech, 250);

    // Fallback: If autoplay policy blocked initial speech, trigger once on first user click/touch
    const onFirstUserGesture = () => {
      window.removeEventListener('click', onFirstUserGesture, true);
      window.removeEventListener('touchstart', onFirstUserGesture, true);
      window.removeEventListener('keydown', onFirstUserGesture, true);
      triggerWelcomeSpeech();
    };
    window.addEventListener('click', onFirstUserGesture, true);
    window.addEventListener('touchstart', onFirstUserGesture, true);
    window.addEventListener('keydown', onFirstUserGesture, true);'''

    if old_welcome in content:
        content = content.replace(old_welcome, new_welcome)
        print("Updated welcome speech in patient_intake.js")
    else:
        print("Warning: old_welcome not found in patient_intake.js!")

    # 2. Add Slider handlers & update selectPainLevel
    old_pain_select = '''  selectPainLevel(level) {
    this.painLevel = parseInt(level, 10);
    const hiddenInput = document.getElementById("pain-range");
    if (hiddenInput) hiddenInput.value = this.painLevel;

    // Update active button state in grid
    document.querySelectorAll(".pain-num-btn").forEach((btn) => {
      const val = parseInt(btn.getAttribute("data-val"), 10);
      if (val === this.painLevel) {
        btn.classList.add("selected");
      } else {
        btn.classList.remove("selected");
      }
    });

    const displayBadge = document.getElementById("pain-val-display");
    if (displayBadge) {
      if (this.painLevel <= 3) {
        displayBadge.style.cssText = "background:#ecfdf5; color:#065f46; border:1px solid #10b981; font-size:0.875rem; padding:0.3rem 0.75rem; font-weight:700;";
        displayBadge.innerText = `Level ${this.painLevel} — Mild Discomfort`;
      } else if (this.painLevel <= 6) {
        displayBadge.style.cssText = "background:#fef3c7; color:#92400e; border:1px solid #f59e0b; font-size:0.875rem; padding:0.3rem 0.75rem; font-weight:700;";
        displayBadge.innerText = `Level ${this.painLevel} — Moderate Pain`;
      } else if (this.painLevel <= 8) {
        displayBadge.style.cssText = "background:#ffedd5; color:#9a3412; border:1px solid #f97316; font-size:0.875rem; padding:0.3rem 0.75rem; font-weight:700;";
        displayBadge.innerText = `Level ${this.painLevel} — Severe Pain`;
      } else {
        displayBadge.style.cssText = "background:#fee2e2; color:#991b1b; border:1px solid #ef4444; font-size:0.875rem; padding:0.3rem 0.75rem; font-weight:700;";
        displayBadge.innerText = `Level ${this.painLevel} — Critical Pain`;
      }
    }

    const nativePainConfirm = {
      en: `Pain level ${this.painLevel} selected`,
      hi: `दर्द का स्तर ${this.painLevel} चुना गया`,
      kn: `ನೋವಿನ ಪ್ರಮಾಣ ${this.painLevel} ಆಯ್ಕೆಮಾಡಲಾಗಿದೆ`,
      ta: `வலி அளவு ${this.painLevel} தேர்ந்தெடுக்கப்பட்டது`,
      te: `నొప్పి స్థాయి ${this.painLevel} ఎంపిక చేయబడింది`,
      ml: `വേദനയുടെ അളവ് ${this.painLevel} തിരഞ്ഞെടുത്തു`,
      mr: `वेदनेचा स्तर ${this.painLevel} निवडला आहे`,
      bn: `ব্যথার মাত্রা ${this.painLevel} নির্বাচিত হয়েছে`,
      gu: `દુખાવાનું પ્રમાણ ${this.painLevel} પસંદ કરવામાં આવ્યું`,
      pa: `ਦਰਦ ਦਾ ਪੱਧਰ ${this.painLevel} ਚੁਣਿਆ ਗਿਆ`
    };
    const painMsg = nativePainConfirm[this.language] || nativePainConfirm["en"];
    SpeechManager.speakText(painMsg, this.language);
  },'''

    new_pain_select = '''  onPainSliderInput(level) {
    this.updatePainDisplay(level);
  },

  setSliderVal(level) {
    const slider = document.getElementById("pain-slider");
    if (slider) slider.value = level;
    this.selectPainLevel(level);
  },

  updatePainDisplay(level) {
    this.painLevel = parseInt(level, 10);
    const hiddenInput = document.getElementById("pain-range");
    if (hiddenInput) hiddenInput.value = this.painLevel;

    const slider = document.getElementById("pain-slider");
    if (slider && parseInt(slider.value, 10) !== this.painLevel) {
      slider.value = this.painLevel;
    }

    const displayBadge = document.getElementById("pain-val-display");
    if (displayBadge) {
      if (this.painLevel <= 3) {
        displayBadge.style.cssText = "background:#ecfdf5; color:#065f46; border:1px solid #10b981; font-size:0.88rem; padding:0.35rem 0.95rem; font-weight:700;";
        displayBadge.innerText = `Level ${this.painLevel} — Mild Discomfort`;
      } else if (this.painLevel <= 6) {
        displayBadge.style.cssText = "background:#fef3c7; color:#92400e; border:1px solid #f59e0b; font-size:0.88rem; padding:0.35rem 0.95rem; font-weight:700;";
        displayBadge.innerText = `Level ${this.painLevel} — Moderate Pain`;
      } else if (this.painLevel <= 8) {
        displayBadge.style.cssText = "background:#ffedd5; color:#9a3412; border:1px solid #f97316; font-size:0.88rem; padding:0.35rem 0.95rem; font-weight:700;";
        displayBadge.innerText = `Level ${this.painLevel} — Severe Pain`;
      } else {
        displayBadge.style.cssText = "background:#fee2e2; color:#991b1b; border:1px solid #ef4444; font-size:0.88rem; padding:0.35rem 0.95rem; font-weight:700;";
        displayBadge.innerText = `Level ${this.painLevel} — Critical Pain`;
      }
    }
  },

  selectPainLevel(level) {
    this.updatePainDisplay(level);

    if (this._painSpeakTimeout) clearTimeout(this._painSpeakTimeout);
    this._painSpeakTimeout = setTimeout(() => {
      const nativePainConfirm = {
        en: `Pain level ${this.painLevel} selected`,
        hi: `दर्द का स्तर ${this.painLevel} चुना गया`,
        kn: `ನೋವಿನ ಪ್ರಮಾಣ ${this.painLevel} ಆಯ್ಕೆಮಾಡಲಾಗಿದೆ`,
        ta: `வலி அளவு ${this.painLevel} தேர்ந்தெடுக்கப்பட்டது`,
        te: `నొప్పి స్థాయి ${this.painLevel} ఎంపిక చేయబడింది`,
        ml: `വേദനയുടെ അളവ് ${this.painLevel} തിരഞ്ഞെടുത്തു`,
        mr: `वेदनेचा स्तर ${this.painLevel} निवडला आहे`,
        bn: `ব্যথার মাত্রা ${this.painLevel} নির্বাচিত হয়েছে`,
        gu: `દુખાવાનું પ્રમાણ ${this.painLevel} પસંદ કરવામાં આવ્યું`,
        pa: `ਦਰਦ ਦਾ ਪੱਧਰ ${this.painLevel} ਚੁਣਿਆ ਗਿਆ`
      };
      const painMsg = nativePainConfirm[this.language] || nativePainConfirm["en"];
      if (typeof SpeechManager !== "undefined" && !SpeechManager.isMuted) {
        SpeechManager.speakText(painMsg, this.language);
      }
    }, 400);
  },'''

    if old_pain_select in content:
        content = content.replace(old_pain_select, new_pain_select)
        print("Updated selectPainLevel and slider handlers in patient_intake.js")
    else:
        print("Warning: old_pain_select not found in patient_intake.js!")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved {path}")


def update_index_html():
    path = "frontend/index.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Remove redundant Audio Guidance button from hero card (leaving ONLY the navbar mute button)
    content = re.sub(
        r'<button class="btn-hero-audio"[^>]*>.*?</button>',
        '',
        content,
        flags=re.DOTALL
    )

    # 2. Remove redundant .btn-icon-round buttons from Step 2, 3, 4, 5, 6 headers
    # (Step 7 #btn-speak-question is kept for question replay)
    content = re.sub(
        r'<button class="btn-icon-round" onclick="SpeechManager\.toggleSpeakForStep\(\d\)"[^>]*>.*?</button>',
        '',
        content,
        flags=re.DOTALL
    )

    # 3. Replace Pain 10-button grid with Sliding Bar in Step 5
    old_pain_html_pattern = re.compile(
        r'<!-- 5\. Pain Severity Scale -->.*?<input type="hidden" id="pain-range" value="7">\s*</div>',
        re.DOTALL
    )

    new_pain_html = '''<!-- 5. Pain Severity Scale (Sliding Bar) -->
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
        </div>'''

    content = old_pain_html_pattern.sub(new_pain_html, content)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved {path}")


def update_styles_css():
    path = "frontend/css/styles.css"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Append range slider styles
    slider_css = """
/* ── Pain Severity Sliding Bar ────────────────────────────── */
.pain-slider-card {
  margin-bottom: 1.75rem;
  background: var(--bg-surface);
  border-radius: var(--radius-sm);
  padding: 1.5rem;
  border: 1px solid var(--border-color);
  box-shadow: var(--shadow-sm);
}

.pain-badge-display {
  display: inline-flex;
  align-items: center;
  font-family: 'Outfit', sans-serif;
  font-size: 0.88rem;
  font-weight: 700;
  padding: 0.35rem 0.95rem;
  border-radius: var(--radius-pill);
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
  height: 10px;
  border-radius: 9999px;
  background: linear-gradient(90deg, #10B981 0%, #F59E0B 45%, #F97316 70%, #EF4444 100%);
  outline: none;
  cursor: pointer;
  margin: 1rem 0 0.75rem 0;
  box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.12);
}

/* Chrome, Safari, Edge, Opera */
.pain-range-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #FFFFFF;
  border: 3.5px solid #0D9488;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.25);
  cursor: pointer;
  transition: transform 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
}

.pain-range-slider::-webkit-slider-thumb:hover {
  transform: scale(1.15);
  box-shadow: 0 6px 16px rgba(13, 148, 136, 0.35);
}

.pain-range-slider::-webkit-slider-thumb:active {
  transform: scale(1.05);
}

/* Firefox */
.pain-range-slider::-moz-range-thumb {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #FFFFFF;
  border: 3.5px solid #0D9488;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.25);
  cursor: pointer;
  transition: transform 0.15s ease, border-color 0.15s ease;
}

.pain-range-slider::-moz-range-thumb:hover {
  transform: scale(1.15);
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
    if ".pain-range-slider" not in content:
        content += slider_css
        print("Appended slider CSS to styles.css")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Saved {path}")

if __name__ == "__main__":
    update_speech_js()
    update_patient_intake_js()
    update_index_html()
    update_styles_css()

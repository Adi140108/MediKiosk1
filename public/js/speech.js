// MediKiosk Production-Grade 6-State Speech-to-Speech Engine with Indian Female Voice & Visual Mute State
const SpeechState = {
  IDLE: 'IDLE',
  LISTENING: 'LISTENING',
  PROCESSING: 'PROCESSING',
  TRANSCRIBING: 'TRANSCRIBING',
  SUCCESS: 'SUCCESS',
  ERROR: 'ERROR'
};

const SpeechManager = {
  state: SpeechState.IDLE,
  isListening: false,
  isSpeaking: false,
  isMuted: false,
  recognition: null,
  synth: window.speechSynthesis || null,
  currentLanguage: 'en',
  audioCtx: null,
  voicesLoaded: false,
  lastSpokenText: "",

  langLocaleMap: {
    en: 'en-IN',
    hi: 'hi-IN',
    ta: 'ta-IN',
    te: 'te-IN',
    kn: 'kn-IN',
    ml: 'ml-IN',
    mr: 'mr-IN',
    bn: 'bn-IN',
    gu: 'gu-IN',
    pa: 'pa-IN'
  },

  init() {
    this.setupRecognition();
    if (this.synth) {
      try { this.synth.resume(); } catch(e) {}
      if (this.synth.onvoiceschanged !== undefined) {
        this.synth.onvoiceschanged = () => {
          this.voicesLoaded = true;
        };
      }
    }
  },

  resumeAudioAndSpeak(stepNum, lang) {
    if (this.isMuted) return;
    try {
      if (this.synth) {
        this.synth.cancel();
        this.synth.resume();
      }
      const ctx = this.getAudioContext();
      if (ctx && ctx.state === 'suspended') {
        ctx.resume();
      }
    } catch(e) {}
    this.speakStepGuidance(stepNum, lang);
  },

  getAudioContext() {
    if (!this.audioCtx) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      if (AudioContextClass) {
        this.audioCtx = new AudioContextClass();
      }
    }
    return this.audioCtx;
  },

  playBeep(type = 'start') {
    try {
      const ctx = this.getAudioContext();
      if (!ctx) return;
      if (ctx.state === 'suspended') ctx.resume();

      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);

      if (type === 'start') {
        osc.frequency.setValueAtTime(440, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.12);
        gain.gain.setValueAtTime(0.15, ctx.currentTime);
        gain.gain.linearRampToValueAtTime(0.01, ctx.currentTime + 0.15);
        osc.start();
        osc.stop(ctx.currentTime + 0.15);
      } else if (type === 'stop') {
        osc.frequency.setValueAtTime(880, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.12);
        gain.gain.setValueAtTime(0.15, ctx.currentTime);
        gain.gain.linearRampToValueAtTime(0.01, ctx.currentTime + 0.15);
        osc.start();
        osc.stop(ctx.currentTime + 0.15);
      } else if (type === 'error') {
        osc.frequency.setValueAtTime(300, ctx.currentTime);
        gain.gain.setValueAtTime(0.2, ctx.currentTime);
        gain.gain.linearRampToValueAtTime(0.01, ctx.currentTime + 0.25);
        osc.start();
        osc.stop(ctx.currentTime + 0.25);
      }
    } catch (e) {
      console.debug("Audio cue omitted:", e);
    }
  },

  countdownInterval: null,
  silenceTimer: null,
  activeTargetInputId: null,
  activeTargetBtnId: null,
  autoSilenceMs: 4000,
  remainingSeconds: 4,
  hasReceivedSpeechInSession: false,
  isRecognitionActive: false,
  lastTranscript: "",

  clearSilenceTimer() {
    this.clearAllTimers();
  },

  clearAllTimers() {
    if (this.silenceTimer) {
      clearTimeout(this.silenceTimer);
      this.silenceTimer = null;
    }
    if (this.countdownInterval) {
      clearInterval(this.countdownInterval);
      this.countdownInterval = null;
    }
  },

  updateMicBadge(seconds, isPostSpeech = false) {
    const micBtn = document.getElementById('btn-mic-toggle');
    const waveEl = document.getElementById('audio-wave-bars');
    const statusEl = document.getElementById('mic-status-label');

    if (this.isListening) {
      if (micBtn) micBtn.classList.add('recording');
      if (waveEl) waveEl.style.display = 'flex';
    }

    if (statusEl) {
      if (isPostSpeech || (this.hasReceivedSpeechInSession && this.lastTranscript)) {
        const preview = this.lastTranscript ? `"${this.lastTranscript.slice(-25)}"` : 'Voice captured';
        statusEl.innerHTML = `🎙️ ${preview} <span class="mic-countdown-pill" style="font-size:0.75rem; background:rgba(220,38,38,0.18); color:#991b1b; padding:2px 8px; border-radius:12px; font-weight:700; border:1px solid rgba(220,38,38,0.35); margin-left:6px;">closing in ${seconds}s</span>`;
      } else {
        statusEl.innerHTML = `🎙️ Listening... <span class="mic-countdown-pill" style="font-size:0.75rem; background:rgba(220,38,38,0.18); color:#991b1b; padding:2px 8px; border-radius:12px; font-weight:700; border:1px solid rgba(220,38,38,0.35); margin-left:6px;">${seconds}s</span>`;
      }
    }
  },

  // Called whenever user speaks a word / interim transcript arrives (4-second trailing silence)
  resetTrailingSilenceTimer(seconds = 4) {
    this.clearAllTimers();
    this.remainingSeconds = seconds;
    this.updateMicBadge(this.remainingSeconds, true);

    this.countdownInterval = setInterval(() => {
      this.remainingSeconds -= 1;
      if (this.remainingSeconds > 0) {
        this.updateMicBadge(this.remainingSeconds, true);
      } else {
        // Patient finished speaking and paused for 4 consecutive seconds -> auto-close mic!
        console.log("Trailing 4s silence elapsed after speaking. Auto-stopping microphone.");
        this.clearAllTimers();
        this.finishListeningAndClose();
      }
    }, 1000);
  },

  // Called when mic is first opened (initial 4-second silence detection before any speech)
  startInitialSilenceTimer(seconds = 4) {
    this.clearAllTimers();
    this.remainingSeconds = seconds;
    this.hasReceivedSpeechInSession = false;
    this.updateMicBadge(this.remainingSeconds, false);

    this.countdownInterval = setInterval(() => {
      this.remainingSeconds -= 1;
      if (this.remainingSeconds > 0) {
        this.updateMicBadge(this.remainingSeconds, false);
      } else {
        // Initial 4 seconds elapsed with no speech detected -> turn off mic
        console.log("No speech detected within initial 4s window. Auto-stopping microphone.");
        this.clearAllTimers();
        this.stopListening(true);
      }
    }, 1000);
  },

  _finishGuard: false,

  finishListeningAndClose() {
    // Guard against double-invocation (timer → stop() → onend → finishListeningAndClose again)
    if (this._finishGuard) return;
    this._finishGuard = true;

    this.clearAllTimers();
    this.isListening = false;
    this.isRecognitionActive = false;

    // CRITICAL: Commit lastTranscript to the correct target input BEFORE stopping recognition.
    // Chrome may discard the last interim result when .stop() is called programmatically,
    // so onresult may never fire for the final transcript. This ensures we don't lose text.
    if (this.lastTranscript && this.lastTranscript.trim().length > 0) {
      const targetId = this.activeTargetInputId || 'patient-answer-input';
      const targetInput = document.getElementById(targetId);
      if (targetInput) {
        targetInput.value = this.lastTranscript.trim();
        targetInput.dispatchEvent(new Event('input', { bubbles: true }));
        console.log(`[SpeechManager] Committed transcript to #${targetId}: "${this.lastTranscript.trim().slice(0, 50)}..."`);
      }
    }

    if (this.recognition) {
      try { this.recognition.stop(); } catch(e) {}
    }
    this.playBeep('stop');

    const micBtn = document.getElementById('btn-mic-toggle');
    const waveEl = document.getElementById('audio-wave-bars');
    const statusEl = document.getElementById('mic-status-label');

    if (micBtn) micBtn.classList.remove('recording');
    if (waveEl) waveEl.style.display = 'none';
    if (this.activeTargetBtnId) {
      const customBtn = document.getElementById(this.activeTargetBtnId);
      if (customBtn) customBtn.classList.remove('recording');
    }

    // Check the CORRECT target input for text, not just patient-answer-input
    const targetId = this.activeTargetInputId || 'patient-answer-input';
    const targetInput = document.getElementById(targetId);
    const hasText = targetInput && targetInput.value.trim().length > 0;

    if (statusEl) {
      if (hasText) {
        statusEl.innerHTML = `✓ Voice captured. Review or submit below.`;
      } else {
        statusEl.innerText = (typeof I18n !== 'undefined' && I18n.t) ? I18n.t('mic_speak_btn') : "🎤 Speak Answer";
      }
    }
    this.state = hasText ? SpeechState.SUCCESS : SpeechState.IDLE;

    // Reset guard after a short delay to allow future sessions
    setTimeout(() => { this._finishGuard = false; }, 200);
  },

  setState(newState, detail = '') {
    this.state = newState;
    const micBtn = document.getElementById('btn-mic-toggle');
    const waveEl = document.getElementById('audio-wave-bars');
    const statusEl = document.getElementById('mic-status-label');

    if (statusEl) {
      switch (newState) {
        case SpeechState.LISTENING:
          this.updateMicBadge(this.remainingSeconds || 4, this.hasReceivedSpeechInSession);
          break;
        case SpeechState.PROCESSING:
        case SpeechState.TRANSCRIBING:
          statusEl.innerText = detail || "⏳ Processing audio & transcribing...";
          if (waveEl) waveEl.style.display = 'none';
          break;
        case SpeechState.SUCCESS:
          statusEl.innerText = detail || "✓ Voice captured. Review or submit below.";
          if (micBtn) micBtn.classList.remove('recording');
          if (waveEl) waveEl.style.display = 'none';
          break;
        case SpeechState.ERROR:
          statusEl.innerText = detail || "⚠️ Speech not recognized. Please retry or type.";
          if (micBtn) micBtn.classList.remove('recording');
          if (waveEl) waveEl.style.display = 'none';
          break;
        case SpeechState.IDLE:
        default:
          statusEl.innerText = detail || ((typeof I18n !== 'undefined' && I18n.t) ? I18n.t('mic_speak_btn') : "🎤 Speak Answer");
          if (micBtn) micBtn.classList.remove('recording');
          if (waveEl) waveEl.style.display = 'none';
          break;
      }
    }
  },

  setupRecognition() {
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRec) {
      this.recognition = new SpeechRec();
      this.recognition.continuous = true;
      this.recognition.interimResults = true;

      this.recognition.onstart = () => {
        this.isListening = true;
        this.isRecognitionActive = true;
        this.playBeep('start');
        this.setState(SpeechState.LISTENING);
      };

      this.recognition.onresult = (event) => {
        let transcript = '';
        for (let i = 0; i < event.results.length; ++i) {
          transcript += event.results[i][0].transcript;
        }

        const trimmed = transcript.trim();
        if (trimmed.length > 0) {
          this.hasReceivedSpeechInSession = true;
          this.lastTranscript = trimmed;

          const targetId = this.activeTargetInputId || 'patient-answer-input';
          const targetInput = document.getElementById(targetId);
          if (targetInput) {
            targetInput.value = trimmed;
            targetInput.dispatchEvent(new Event('input', { bubbles: true }));
          }

          // Restart 4-second trailing silence countdown whenever patient speaks / pauses
          this.resetTrailingSilenceTimer(4);
        }
      };

      this.recognition.onspeechend = () => {
        if (this.isListening && this.hasReceivedSpeechInSession) {
          this.resetTrailingSilenceTimer(4);
        }
      };

      this.recognition.onerror = (event) => {
        if (event.error === 'no-speech') {
          // If 4s countdown is still running and no speech captured yet, keep listening session alive
          if (this.isListening && !this.hasReceivedSpeechInSession && this.remainingSeconds > 0) {
            try {
              if (!this.isRecognitionActive) this.recognition.start();
            } catch(e) {}
            return;
          }
        }

        if (event.error !== 'aborted') {
          console.warn('Speech recognition notice:', event.error);
          if (event.error !== 'no-speech') {
            this.playBeep('error');
            this.setState(SpeechState.ERROR, `Speech note (${event.error})`);
          } else {
            this.setState(SpeechState.IDLE, "Microphone paused (tap to speak)");
          }
        }
        this.clearAllTimers();
        this.isListening = false;
        this.isRecognitionActive = false;
      };

      this.recognition.onend = () => {
        this.isRecognitionActive = false;
        // If the browser prematurely ended while we already captured speech, finalize and close cleanly
        if (this.hasReceivedSpeechInSession) {
          this.finishListeningAndClose();
          return;
        }

        // If the browser prematurely ended while the initial 4s countdown is still active without speech, restart it
        if (this.isListening && !this.hasReceivedSpeechInSession && this.remainingSeconds > 0) {
          try {
            this.recognition.start();
            return;
          } catch(e) {}
        }

        this.clearAllTimers();
        this.isListening = false;
        this.playBeep('stop');
        const fallbackTargetId = this.activeTargetInputId || 'patient-answer-input';
        const answerInput = document.getElementById(fallbackTargetId);
        if (answerInput && answerInput.value.trim().length > 0) {
          this.setState(SpeechState.SUCCESS);
        } else {
          this.setState(SpeechState.IDLE, "Microphone paused (tap to speak)");
        }
      };
    }
  },

  setLanguage(lang) {
    this.currentLanguage = lang;
    if (this.recognition) {
      this.recognition.lang = this.langLocaleMap[lang] || 'en-IN';
    }
  },

  startListeningWithSilenceTimeout(silenceMs = 4000) {
    if (!this.recognition) return;
    this.clearAllTimers();

    // If speech synthesis is currently speaking, wait or don't overlap
    if (this.isSpeaking && (this.synth || this.currentAudio)) {
      return;
    }

    this.hasReceivedSpeechInSession = false;
    this.lastTranscript = "";
    this.isListening = true;

    try {
      this.recognition.lang = this.langLocaleMap[this.currentLanguage] || 'en-IN';
      if (!this.isRecognitionActive) {
        this.recognition.start();
      }
    } catch (err) {
      console.debug("Speech recognition start note:", err);
    }

    const seconds = Math.round((silenceMs || 4000) / 1000);
    this.startInitialSilenceTimer(seconds);
  },

  stopListening(isSilenceTimeout = false) {
    this.clearAllTimers();
    this.isListening = false;
    this.isRecognitionActive = false;
    if (this.recognition) {
      try {
        this.recognition.stop();
      } catch (e) {}
    }
    const micBtn = document.getElementById('btn-mic-toggle');
    const waveEl = document.getElementById('audio-wave-bars');
    if (micBtn) micBtn.classList.remove('recording');
    if (waveEl) waveEl.style.display = 'none';
    if (this.activeTargetBtnId) {
      const customBtn = document.getElementById(this.activeTargetBtnId);
      if (customBtn) customBtn.classList.remove('recording');
    }

    if (isSilenceTimeout) {
      this.setState(SpeechState.IDLE, "Microphone paused (tap to speak)");
    } else {
      const answerInput = document.getElementById('patient-answer-input');
      if (answerInput && answerInput.value.trim().length > 0) {
        this.setState(SpeechState.SUCCESS, "✓ Voice captured. Review or submit below.");
      } else {
        this.setState(SpeechState.IDLE);
      }
    }
  },

    toggleListeningForInput(targetInputId, targetBtnId, lang = null) {
    if (!this.recognition) {
      alert('Speech recognition is not supported in this browser. Please type directly.');
      return;
    }
    if (this.isListening && this.activeTargetInputId === targetInputId) {
      this.stopListening(false);
      this.activeTargetInputId = null;
      this.activeTargetBtnId = null;
      if (targetBtnId) {
        const btn = document.getElementById(targetBtnId);
        if (btn) btn.classList.remove('recording');
      }
      return;
    }
    this.stopAllAudio();
    this.activeTargetInputId = targetInputId;
    this.activeTargetBtnId = targetBtnId;
    if (targetBtnId) {
      const btn = document.getElementById(targetBtnId);
      if (btn) btn.classList.add('recording');
    }
    if (lang) this.setLanguage(lang);
    this.startListeningWithSilenceTimeout(4000);
  },

  toggleListening() {
    if (!this.recognition) {
      alert('Speech recognition is not supported in this browser. Please type your answer.');
      return;
    }

    if (this.isListening) {
      this.stopListening(false);
    } else {
      // Set target to the patient answer input (Step 7 interview)
      this.activeTargetInputId = 'patient-answer-input';
      this.activeTargetBtnId = 'btn-mic-toggle';
      this.startListeningWithSilenceTimeout(4000);
    }
  },

  getIndianFemaleVoice(targetLang) {
    if (!this.synth) return null;
    const voices = this.synth.getVoices();
    if (!voices || voices.length === 0) return null;

    const langCode = (targetLang || 'en').toLowerCase().trim();
    const locale = this.langLocaleMap[langCode] || `${langCode}-IN`;

    // High quality named voices per language
    const preferredVoicesByLang = {
      hi: ['swara', 'madhur', 'google हिन्दी', 'hindi', 'hi-in'],
      kn: ['sapna', 'gagan', 'google ಕನ್ನಡ', 'kannada', 'kn-in'],
      ta: ['pallavi', 'valluvar', 'google தமிழ்', 'tamil', 'ta-in'],
      te: ['shruti', 'mohan', 'google తెలుగు', 'telugu', 'te-in'],
      ml: ['sobhana', 'midhun', 'google മലയാളം', 'malayalam', 'ml-in'],
      mr: ['aarohi', 'manohar', 'google मराठी', 'marathi', 'mr-in'],
      bn: ['tanishaa', 'bashkar', 'google বাংলা', 'bengali', 'bangla', 'bn-in'],
      gu: ['dhwani', 'niranjan', 'google ગુજરાતી', 'gujarati', 'gu-in'],
      pa: ['ojas', 'google ਪੰਜਾਬੀ', 'punjabi', 'pa-in'],
      en: ['neerja', 'heera', 'priya', 'aditi', 'google english (india)', 'en-in']
    };

    const preferredKeywords = preferredVoicesByLang[langCode] || preferredVoicesByLang['en'];

    // 1. Check for exact language match (locale or prefix)
    const langVoices = voices.filter(v => {
      const vLang = (v.lang || '').replace('_', '-').toLowerCase();
      return vLang === locale.toLowerCase() || vLang.startsWith(langCode);
    });

    if (langVoices.length > 0) {
      // 1a. Check for preferred natural/neural female voice for this exact language
      for (const kw of preferredKeywords) {
        const found = langVoices.find(v => v.name.toLowerCase().includes(kw));
        if (found) return found;
      }
      // 1b. Check for any natural / online / Google voice in this language
      const naturalVoice = langVoices.find(v => {
        const name = v.name.toLowerCase();
        return name.includes('natural') || name.includes('google') || name.includes('online') || name.includes('neural');
      });
      if (naturalVoice) return naturalVoice;

      // 1c. Any non-male voice in this language
      const femaleVoice = langVoices.find(v => {
        const name = v.name.toLowerCase();
        return !name.includes('male') && !name.includes('david') && !name.includes('mark') && !name.includes('george');
      });
      if (femaleVoice) return femaleVoice;

      return langVoices[0];
    }

    // 2. If target is English, find best Indian English female voice
    if (langCode === 'en') {
      const enInVoice = voices.find(v => {
        const vLang = (v.lang || '').toLowerCase();
        const vName = v.name.toLowerCase();
        return (vLang.includes('en-in') || vName.includes('india')) && (vName.includes('neerja') || vName.includes('heera') || vName.includes('natural') || !vName.includes('male'));
      });
      if (enInVoice) return enInVoice;
    }

    // 3. IMPORTANT: For non-English languages, if no exact voice object is loaded in browser,
    // return null so browser falls back to its native synthesizer for utterance.lang!
    // Never force an English voice onto Hindi, Kannada, Tamil, etc.
    return null;
  },

  guidanceMapByLang: {
    en: {
      1: "Namaste! Welcome to MediKiosk intelligent hospital check-in. Please touch the Begin Check-In button on your screen to start.",
      2: "Please choose your preferred language by tapping any box on the screen: English, Hindi, Kannada, Tamil, Telugu, and more.",
      3: "Please listen carefully to our safety guidelines. MediKiosk prepares your symptom summary for your attending doctor. Your doctor will personally examine you and write all prescriptions. Please tap the agreement box and touch Continue.",
      4: "Please enter or speak your name, age, gender, and phone number. If a family member or attendant is helping you, you can check the attendant box.",
      5: "What health problem or pain brings you to the clinic today? Touch any number from 1 to 10 to indicate your pain level, or speak your symptoms.",
      6: "If you have previous doctor prescriptions or lab test reports, you can upload them here, or tap Skip to proceed.",
      7: "Please listen to the clinical question and speak your answer using the microphone button.",
      8: "Your clinical check-in is complete! Your consultation ticket is ready. Please proceed to the waiting area of your assigned department."
    },
    hi: {
      1: "नमस्ते! मेडीकियोस्क क्लिनिकल चेक-इन में आपका स्वागत है। शुरू करने के लिए स्क्रीन पर चेक-इन शुरू करें बटन को स्पर्श करें।",
      2: "कृपया स्क्रीन पर अपनी पसंदीदा भाषा का डिब्बा चुनकर स्पर्श करें: हिन्दी, अंग्रेजी, कन्नड़, तमिल, तेलुगु इत्यादि।",
      3: "कृपया ध्यान से सुनें। मेडीकियोस्क आपके लक्षणों की जानकारी सीधे आपके डॉक्टर को भेजता है। आपके डॉक्टर आपकी व्यक्तिगत जांच करेंगे और दवा लिखेंगे। कृपया सहमति के डिब्बे को टिक करें और आगे बढ़ें।",
      4: "कृपया अपना नाम, उम्र, लिंग और मोबाइल नंबर दर्ज करें या बोलें। यदि कोई परिजन या सहायक आपके साथ है, तो सहायक का विकल्प चुनें।",
      5: "आज आपको क्या स्वास्थ्य समस्या या तकलीफ़ है? अपने दर्द का स्तर 1 से 10 तक छूकर चुनें, या माइक दबाकर लक्षण बताएं।",
      6: "यदि आपके पास डॉक्टर की पुरानी पर्ची या जांच रिपोर्ट है, तो यहां अपलोड करें, या आगे बढ़ने के लिए छोड़ें बटन दबाएं।",
      7: "कृपया प्रश्न सुनें और माइक का बटन दबाकर अपना उत्तर बोलें।",
      8: "आपकी जांच पूरी हो गई है! आपका परामर्श टोकन तैयार है। कृपया अपने संबंधित विभाग के प्रतीक्षालय में जाएं।"
    },
    kn: {
      1: "ನಮಸ್ಕಾರ! ಮೆಡಿಕಿಯೋಸ್ಕ್ ಕ್ಲಿನಿಕಲ್ ಚೆಕ್-ಇನ್‌ಗೆ ಸುಸ್ವಾಗತ. ಪ್ರಾರಂಭಿಸಲು ಸ್ಕ್ರೀನ್ ಮೇಲೆ ಚೆಕ್-ಇನ್ ಪ್ರಾರಂಭಿಸಿ ಬಟನ್ ಒತ್ತಿರಿ.",
      2: "ದಯವಿಟ್ಟು ಸ್ಕ್ರೀನ್ ಮೇಲೆ ನಿಮ್ಮ ಮೆಚ್ಚಿನ ಭಾಷೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ: ಕನ್ನಡ, ಹಿಂದಿ, ಇಂಗ್ಲಿಷ್, ತಮಿಳು, ತೆಲುಗು.",
      3: "ದಯವಿಟ್ಟು ಗಮನವಿಟ್ಟು ಕೇಳಿ. ಮೆಡಿಕಿಯೋಸ್ಕ್ ನಿಮ್ಮ ರೋಗಲಕ್ಷಣಗಳ ವಿವರವನ್ನು ನಿಮ್ಮ ವೈದ್ಯರಿಗೆ ಕಳುಹಿಸುತ್ತದೆ. ನಿಮ್ಮ ವೈದ್ಯರು ಪರೀಕ್ಷಿಸಿ ಔಷಧ ನೀಡುತ್ತಾರೆ. ಒಪ್ಪಿಗೆ ಬಾಕ್ಸ್ ಒತ್ತಿ ಮುಂದುವರಿಯಿರಿ.",
      4: "ದಯವಿಟ್ಟು ನಿಮ್ಮ ಹೆಸರು, ವಯಸ್ಸು, ಲಿಂಗ ಮತ್ತು ಮೊಬೈಲ್ ಸಂಖ್ಯೆಯನ್ನು ನಮೂದಿಸಿ ಅಥವಾ ಧ್ವನಿ ಮೂಲಕ ತಿಳಿಸಿ.",
      5: "ಇಂದು ನಿಮಗೆ ಯಾವ ಆರೋಗ್ಯ ಸಮಸ್ಯೆ ಇದೆ? ನೋವಿನ ಪ್ರಮಾಣವನ್ನು 1 ರಿಂದ 10 ರವರೆಗೆ ಮುಟ್ಟಿ ಆಯ್ಕೆಮಾಡಿ ಅಥವಾ ಮಾತನಾಡಿ ತಿಳಿಸಿ.",
      6: "ಹಳೆಯ ವೈದ್ಯಕೀಯ ಚೀಟಿ ಅಥವಾ ರಿಪೋರ್ಟ್ ಇದ್ದರೆ ಇಲ್ಲಿ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ, ಇಲ್ಲದಿದ್ದರೆ ಸ್ಕಿಪ್ ಒತ್ತಿರಿ.",
      7: "ದಯವಿಟ್ಟು ಪ್ರಶ್ನೆಯನ್ನು ಕೇಳಿ ಮೈಕ್ರೊಫೋನ್ ಬಟನ್ ಒತ್ತಿ ಉತ್ತರಿಸಿ.",
      8: "ನಿಮ್ಮ ಚೆಕ್-ಇನ್ ಪೂರ್ಣಗೊಂಡಿದೆ! ನಿಮ್ಮ ಟೋಕನ್ ಸಿದ್ಧವಾಗಿದೆ. ದಯವಿಟ್ಟು ನಿಗದಿಪಡಿಸಿದ ವಿಭಾಗದ ಕಾಯುವ ಕೋಣೆಗೆ ಹೋಗಿ."
    },
    ta: {
      1: "வணக்கம்! மெடிகியோஸ்க் மருத்துவ செக்-இன்னிற்கு வரவேற்கிறோம். தொடங்க திரையில் உள்ள செக்-இன் தொடங்கு பொத்தானைத் தொடவும்.",
      2: "தயவுசெய்து திரையில் உங்கள் விருப்பமான மொழியைத் தேர்ந்தெடுக்கவும்: தமிழ், ஆங்கிலம், இந்தி, கன்னடம், தெலுங்கு.",
      3: "கவனமாகக் கேளுங்கள். மெடிகியோஸ்க் உங்கள் அறிகுறிகளை மருத்துவருக்குத் தெரிவிக்கும். மருத்துவரே பரிசோதித்து மருந்து வழங்குவார். ஒப்புதல் பெட்டியைத் தொட்டு தொடரவும்.",
      4: "தயவுசெய்து உங்கள் பெயர், வயது, பாலினம் மற்றும் தொலைபேசி எண்ணை உள்ளிடவும் அல்லது பேசவும்.",
      5: "இன்று உங்களுக்கு என்ன உடல்நல பிரச்சனை அல்லது வலி உள்ளது? உங்கள் வலியை 1 முதல் 10 வரை தொட்டு தேர்வு செய்யவும் அல்லது பேசவும்.",
      6: "பழைய மருத்துவ சீட்டு அல்லது பரிசோதனை அறிக்கை இருந்தால் பதிவேற்றவும், இல்லையெனில் தவிர் என்பதைத் தொடவும்.",
      7: "கேள்வியைக் கேட்டு மைக் பொத்தானை அழுத்தி பதில் சொல்லுங்கள்.",
      8: "உங்கள் செக்-இன் முடிந்தது! டோக்கன் தயாராக உள்ளது. ஒதுக்கப்பட்ட பிரிவின் காத்திருப்பு அறைக்கு செல்லவும்."
    },
    te: {
      1: "నమస్కారం! మెడికియోస్క్ క్లినికల్ చెక్-ఇన్‌కు స్వాగతం. ప్రారంభించడానికి స్క్రీన్‌పై చెక్-ఇన్ ప్రారంభించండి బటన్‌ను నొక్కండి.",
      2: "దయచేసి స్క్రీన్‌పై మీకు నచ్చిన భాషను ఎంచుకోండి: తెలుగు, ఇంగ్లీష్, హిందీ, కన్నడ, తమిళం.",
      3: "దయచేసి వినండి. మెడికియోస్క్ మీ లక్షణాల వివరాలను డాక్టర్‌కు పంపుతుంది. డాక్టరే మిమ్మల్ని పరీక్షించి మందులు రాస్తారు. అంగీకార పెట్టెను నొక్కి కొనసాగించండి.",
      4: "దయచేసి మీ పేరు, వయస్సు, లింగం మరియు ఫోన్ నంబర్‌ను నమోదు చేయండి లేదా మాట్లాడండి.",
      5: "ఈరోజు మీకు ఎలాంటి ఆరోగ్య సమస్య లేదా నొప్పి ఉంది? నొప్పి స్థాయిని 1 నుండి 10 వరకు తాకి ఎంచుకోండి లేదా మాట్లాడండి.",
      6: "పాత డాక్టర్ చీటీ లేదా రిపోర్టులు ఉంటే అప్‌లోడ్ చేయండి, లేకపోతే స్కిప్ నొక్కండి.",
      7: "దయచేసి ప్రశ్నను విని మైక్ బటన్ నొక్కి సమాధానం చెప్పండి.",
      8: "మీ చెక్-ఇన్ పూర్తయింది! మీ టోకెన్ సిద్ధంగా ఉంది. దయచేసి కేటాయించిన విభాగం వద్దకు వెళ్లండి."
    },
    ml: {
      1: "നമസ്കാരം! മെഡികിയോസ്ക് ക്ലിനിക്കൽ ചെക്ക്-ഇന്നിലേക്ക് സ്വാഗതം. ആരംഭിക്കാൻ സ്ക്രീനിലെ ബട്ടൺ സ്പർശിക്കുക.",
      2: "ദയവായി സ്ക്രീനിൽ നിങ്ങളുടെ ഇഷ്ടപ്പെട്ട ഭാഷ തിരഞ്ഞെടുക്കുക: മലയാളം, ഇംഗ്ലീഷ്, ഹിന്ദി, തമിഴ്.",
      3: "ദയവായി ശ്രദ്ധിക്കുക. നിങ്ങളുടെ ലക്ഷണങ്ങൾ ഡോക്ടർക്ക് കൈമാറുന്നു. ഡോക്ടർ പരിശോധിച്ച് മരുന്ന് നൽകും. സമ്മത ബോക്സ് അമർത്തി തുടരുക.",
      4: "ദയവായി നിങ്ങളുടെ പേര്, പ്രായം, ലിംഗം, ഫോൺ നമ്പർ എന്നിവ നൽകുക.",
      5: "ഇന്ന് നിങ്ങൾക്ക് എന്താണ് ആരോഗ്യ പ്രശ്നം? വേദനയുടെ അളവ് 1 മുതൽ 10 വരെ തിരഞ്ഞെടുക്കുക അല്ലെങ്കിൽ പറയുക.",
      6: "പഴയ കുറിപ്പടികളോ ലാബ് റിപ്പോർട്ടുകളോ ഉണ്ടെങ്കിൽ അപ്‌ലോഡ് ചെയ്യുക, അല്ലെങ്കിൽ ഒഴിവാക്കുക.",
      7: "ചോദ്യം കേട്ട് മൈക്രോഫോൺ ബട്ടൺ അമർത്തി മറുപടി പറയുക.",
      8: "നിങ്ങളുടെ ചെക്ക്-ഇൻ പൂർത്തിയായി! ടോക്കൺ തയ്യാറാണ്. ദയവായി കാത്തിരിപ്പ് കേന്ദ്രത്തിലേക്ക് പോകുക."
    },
    mr: {
      1: "नमस्ते! मेडीकियोस्क क्लिनिकल चेक-इन मध्ये आपले स्वागत आहे. सुरू करण्यासाठी स्क्रीनवरील चेक-इन सुरू करा बटणावर स्पर्श करा.",
      2: "कृपया स्क्रीनवर आपली पसंतीची भाषा निवडा: मराठी, हिंदी, इंग्रजी, कन्नड.",
      3: "कृपया काळजीपूर्वक ऐका. मेडीकियोस्क आपली माहिती थेट डॉक्टरांकडे पाठवते. डॉक्टर प्रत्यक्ष तपासणी करून औषधे देतील. संमती बॉक्सवर टिक करून पुढे जा.",
      4: "कृपया आपले नाव, वय, लिंग आणि फोन नंबर प्रविष्ट करा किंवा बोलून सांगा.",
      5: "आज आपल्याला काय त्रास किंवा दुखणे होत आहे? १ ते १० मधील वेदनेचा स्तर निवडा किंवा बोलून सांगा.",
      6: "जुन्या पावत्या किंवा वैद्यकीय अहवाल असल्यास अपलोड करा, अन्यथा पुढे जा दाबा.",
      7: "कृपया प्रश्न ऐका आणि माइक बटण दाबून उत्तर द्या.",
      8: "आपले चेक-इन पूर्ण झाले आहे! आपले टोकन तयार आहे. कृपया संबंधित विभागाच्या प्रतीक्षालयात जा."
    },
    bn: {
      1: "নমস্কার! মেডিকিয়স্ক ক্লিনিকাল চেক-ইনে আপনাকে স্বাগতম। শুরু করতে স্ক্রিনের চেক-ইন শুরু করুন বোতামটি স্পর্শ করুন।",
      2: "অনুগ্রহ করে স্ক্রিনে আপনার পছন্দের ভাষাটি নির্বাচন করুন: বাংলা, হিন্দি, ইংরেজি।",
      3: "দয়া করে মনোযোগ দিয়ে শুনুন। মেডিকিয়স্ক আপনার উপসর্গের বিবরণ সরাসরি ডাক্তারকে পাঠায়। ডাক্তার পরীক্ষা করে ওষুধ দেবেন। সম্মতি বক্সে টিক দিন এবং এগিয়ে যান।",
      4: "অনুগ্রহ করে আপনার নাম, বয়স, লিঙ্গ এবং ফোন নম্বর লিখুন বা বলুন।",
      5: "আজ আপনার কি শারীরিক সমস্যা বা ব্যথা হচ্ছে? ১ থেকে ১০ পর্যন্ত ব্যথার মাত্রা স্পর্শ করে বেছে নিন বা বলুন।",
      6: "পুরোনো প্রেসক্রিপশন বা রিপোর্ট থাকলে আপলোড করুন, না হলে এগিয়ে যান।",
      7: "অনুগ্রহ করে প্রশ্নটি শুনুন এবং মাইক চেপে উত্তর দিন।",
      8: "আপনার চেক-ইন সম্পন্ন হয়েছে! আপনার টোকেন প্রস্তুত। অনুগ্রহ করে নির্ধারিত বিভাগের অপেক্ষাগারে যান।"
    },
    gu: {
      1: "નમસ્તે! મેડીકિયોસ્ક ક્લિનિકલ ચેક-ઇનમાં આપનું સ્વાગત છે. શરૂ કરવા માટે સ્ક્રીન પરનું બટન દબાવો.",
      2: "કૃપા કરીને સ્ક્રીન પર તમારી પસંદગીની ભાષા પસંદ કરો: ગુજરાતી, હિન્દી, અંગ્રેજી.",
      3: "કૃપા કરીને ધ્યાનથી સાંભળો. મેડીકિયોસ્ક તમારી માહિતી ડૉક્ટર સુધી પહોંચાડે છે. ડૉક્ટર તપાસીને દવા આપશે. સંમતિ બોક્સ પર ટીક કરીને આગળ વધો.",
      4: "કૃપા કરીને તમારું નામ, ઉંમર, જાતિ અને ફોન નંબર દાખલ કરો અથવા બોલો.",
      5: "આજે તમને શું તકલીફ અથવા દુખાવો છે? ૧ થી ૧૦ માંથી દુખાવાનું પ્રમાણ પસંદ કરો અથવા બોલીને જણાવો.",
      6: "જૂની દવાઓની ચિઠ્ઠી અથવા રિપોર્ટ હોય તો અપલોડ કરો, અથવા આગળ વધો.",
      7: "કૃપા કરીને પ્રશ્ન સાંભળો અને માઇક દબાવીને ઉત્તર આપો.",
      8: "તમારું ચેક-ઇન પૂર્ણ થયું છે! તમારું ટોકન તૈયાર છે. કૃપા કરીને સંબંધિત વિભાગના વેઇટિંગ એરિયામાં જાઓ."
    },
    pa: {
      1: "ਸਤਿ ਸ੍ਰੀ ਅਕਾਲ! ਮੈਡੀਕਿਓਸਕ ਕਲੀਨਿਕਲ ਚੈੱਕ-ਇਨ ਵਿੱਚ ਤੁਹਾਡਾ ਸੁਆਗਤ ਹੈ। ਸ਼ੁਰੂ ਕਰਨ ਲਈ ਸਕ੍ਰੀਨ 'ਤੇ ਬਟਨ ਦਬਾਓ।",
      2: "ਕਿਰਪਾ ਕਰਕੇ ਸਕ੍ਰੀਨ 'ਤੇ ਆਪਣੀ ਪਸੰਦੀਦਾ ਭਾਸ਼ਾ ਚੁਣੋ: ਪੰਜਾਬੀ, ਹਿੰਦੀ, ਅੰਗਰੇਜ਼ੀ।",
      3: "ਕਿਰਪਾ ਕਰਕੇ ਧਿਆਨ ਨਾਲ ਸੁਣੋ। ਮੈਡੀਕਿਓਸਕ ਤੁਹਾਡੇ ਲੱਛਣ ਡਾਕਟਰ ਕੋਲ ਭੇਜਦਾ ਹੈ। ਡਾਕਟਰ ਖੁਦ ਜਾਂਚ ਕਰਕੇ ਦਵਾਈ ਦੇਣਗੇ। ਸਹਿਮਤੀ ਵਾਲੇ ਬਕਸੇ 'ਤੇ ਕਲਿੱਕ ਕਰਕੇ ਅੱਗੇ ਵਧੋ।",
      4: "ਕਿਰਪਾ ਕਰਕੇ ਆਪਣਾ ਨਾਮ, ਉਮਰ, ਲਿੰਗ ਅਤੇ ਫ਼ੋਨ ਨੰਬਰ ਦਰਜ ਕਰੋ ਜਾਂ ਬੋਲ ਕੇ ਦੱਸੋ।",
      5: "ਅੱਜ ਤੁਹਾਨੂੰ ਕੀ ਤਕਲੀਫ਼ ਜਾਂ ਦਰਦ ਹੈ? 1 ਤੋਂ 10 ਤੱਕ ਦਰਦ ਦਾ ਪੱਧਰ ਚੁਣੋ ਜਾਂ ਬੋਲ ਕੇ ਦੱਸੋ।",
      6: "ਪੁਰਾਣੀਆਂ ਪਰਚੀਆਂ ਜਾਂ ਰਿਪੋਰਟਾਂ ਅੱਪਲੋਡ ਕਰੋ, ਜਾਂ ਅੱਗੇ ਵਧਣ ਲਈ ਛੱਡੋ ਦਬਾਓ।",
      7: "ਕਿਰਪਾ ਕਰਕੇ ਸਵਾਲ ਸੁਣੋ ਅਤੇ ਮਾਈਕ ਦਬਾ ਕੇ ਜਵਾਬ ਦਿਓ।",
      8: "ਤੁਹਾਡਾ ਚੈੱਕ-ਇਨ ਪੂਰਾ ਹੋ ਗਿਆ ਹੈ! ਤੁਹਾਡਾ ਟੋਕਨ ਤਿਆਰ ਹੈ। ਕਿਰਪਾ ਕਰਕੇ ਆਪਣੇ ਵਿਭਾਗ ਵਿੱਚ ਜਾਓ।"
    }
  },

  getStepGuidanceText(stepNum, lang = 'en') {
    const targetLang = lang || this.currentLanguage || 'en';
    const langDict = this.guidanceMapByLang[targetLang] || this.guidanceMapByLang['hi'] || this.guidanceMapByLang['en'];
    return langDict[stepNum] || this.guidanceMapByLang['en'][stepNum] || "";
  },

  speakStepGuidance(stepNum, lang = 'en') {
    if (this.isMuted) return;
    const targetLang = lang || this.currentLanguage || 'en';
    const text = this.getStepGuidanceText(stepNum, targetLang);
    if (text) {
      this.speakText(text, targetLang);
    }
  },

  toggleSpeakForStep(stepNum) {
    const targetLang = this.currentLanguage || 'en';
    const text = this.getStepGuidanceText(stepNum, targetLang);
    this.toggleSpeak(text, targetLang);
  },

  updateButtonStates(state) {
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
  },

  currentAudio: null,

  toggleSpeak(text = null, lang = null) {
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
  },

  stopAllAudio() {
    this.clearAllTimers();
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
    this.isSpeaking = false;
    this.stopListening();
    this.updateButtonStates(this.isMuted ? 'muted' : 'idle');
  },

  speakText(text, lang = null, onEndCallback = null) {
    if (!text || !text.trim()) {
      if (onEndCallback) setTimeout(onEndCallback, 100);
      return;
    }

    if (this.isMuted) {
      this.updateButtonStates('muted');
      if (onEndCallback) setTimeout(onEndCallback, 200);
      return;
    }

    // Stop any ongoing speech or audio
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

    this.lastSpokenText = text;
    const targetLang = (lang || this.currentLanguage || 'en').toLowerCase().trim();
    const assignedVoice = this.getIndianFemaleVoice(targetLang);

    // Option A: If browser has a dedicated natural voice installed for this language, use it
    if (this.synth && assignedVoice && (targetLang === 'en' || targetLang === 'hi')) {
      try {
        this.synth.resume();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = this.langLocaleMap[targetLang] || 'en-IN';
        utterance.rate = 0.92;
        utterance.pitch = 1.0;
        utterance.voice = assignedVoice;

        utterance.onstart = () => {
          this.isSpeaking = true;
          this.updateButtonStates('playing');
        };

        utterance.onend = () => {
          this.isSpeaking = false;
          if (this._speechWatchdog) {
            clearInterval(this._speechWatchdog);
            this._speechWatchdog = null;
          }
          this.updateButtonStates(this.isMuted ? 'muted' : 'idle');
          if (typeof onEndCallback === 'function') {
            onEndCallback();
          }
        };

        utterance.onerror = (e) => {
          console.warn("Browser SpeechSynthesis notice:", e);
          this.isSpeaking = false;
          if (this._speechWatchdog) {
            clearInterval(this._speechWatchdog);
            this._speechWatchdog = null;
          }
          this.updateButtonStates(this.isMuted ? 'muted' : 'idle');
          if (e.error !== 'interrupted' && e.error !== 'canceled') {
            this._playServerAudioStream(text, targetLang, onEndCallback);
          } else if (typeof onEndCallback === 'function') {
            onEndCallback();
          }
        };

        this.isSpeaking = true;
        this.updateButtonStates('playing');
        this.synth.speak(utterance);

        // Chrome watchdog to prevent audio suspension mid-speech
        if (this._speechWatchdog) clearInterval(this._speechWatchdog);
        this._speechWatchdog = setInterval(() => {
          if (this.synth && this.synth.speaking) {
            try { this.synth.resume(); } catch(e) {}
          } else {
            clearInterval(this._speechWatchdog);
            this._speechWatchdog = null;
          }
        }, 3500);

        return;
      } catch (err) {
        console.warn("Browser speech error, falling back to server TTS stream:", err);
      }
    }

    // Option B: Server Indic Neural TTS (Kannada, Tamil, Telugu, Malayalam, Marathi, Bengali, Gujarati, Punjabi, Hindi, English)
    this._playServerAudioStream(text, targetLang, onEndCallback);
  },

  _playServerAudioStream(text, targetLang, onEndCallback) {
    try {
      this.updateButtonStates('playing');
      this.isSpeaking = true;

      const streamUrl = `/api/v1/speech/stream?text=${encodeURIComponent(text.trim())}&language=${encodeURIComponent(targetLang)}`;
      const audio = new Audio(streamUrl);
      this.currentAudio = audio;

      audio.onended = () => {
        this.isSpeaking = false;
        this.currentAudio = null;
        this.updateButtonStates(this.isMuted ? 'muted' : 'idle');
        if (typeof onEndCallback === 'function') {
          onEndCallback();
        }
      };

      audio.onerror = (e) => {
        console.warn("Audio stream playback notice:", e);
        this.isSpeaking = false;
        this.currentAudio = null;
        this.updateButtonStates(this.isMuted ? 'muted' : 'idle');
        if (typeof onEndCallback === 'function') {
          onEndCallback();
        }
      };

      audio.play().catch(err => {
        console.debug("Autoplay note:", err);
        this.isSpeaking = false;
        this.currentAudio = null;
        this.updateButtonStates(this.isMuted ? 'muted' : 'idle');
        if (typeof onEndCallback === 'function') {
          onEndCallback();
        }
      });
    } catch (err) {
      console.warn("Speech synthesis initialization error:", err);
      this.isSpeaking = false;
      this.updateButtonStates(this.isMuted ? 'muted' : 'idle');
      if (typeof onEndCallback === 'function') {
        onEndCallback();
      }
    }
  }
};

if (typeof window !== 'undefined') {
  window.SpeechManager = SpeechManager;
  window.SpeechState = SpeechState;
}

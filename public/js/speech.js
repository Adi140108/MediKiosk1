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
      if (this.synth.onvoiceschanged !== undefined) {
        this.synth.onvoiceschanged = () => {
          this.voicesLoaded = true;
        };
      }
    }
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

  setState(newState, detail = '') {
    this.state = newState;
    const micBtn = document.getElementById('btn-mic-toggle');
    const waveEl = document.getElementById('audio-wave-bars');
    const statusEl = document.getElementById('mic-status-label');

    if (statusEl) {
      switch (newState) {
        case SpeechState.LISTENING:
          statusEl.innerText = "🎙️ Listening... (speak clearly)";
          if (micBtn) micBtn.classList.add('recording');
          if (waveEl) waveEl.style.display = 'flex';
          break;
        case SpeechState.PROCESSING:
        case SpeechState.TRANSCRIBING:
          statusEl.innerText = "⏳ Processing audio & transcribing...";
          if (waveEl) waveEl.style.display = 'none';
          break;
        case SpeechState.SUCCESS:
          statusEl.innerText = "✓ Voice captured. Review or submit below.";
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
          statusEl.innerText = (typeof I18n !== 'undefined' && I18n.t) ? I18n.t('mic_speak_btn') : "🎤 Speak Answer";
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
      this.recognition.continuous = false;
      this.recognition.interimResults = true;

      this.recognition.onstart = () => {
        this.isListening = true;
        this.playBeep('start');
        this.setState(SpeechState.LISTENING);
      };

      this.recognition.onresult = (event) => {
        let transcript = '';
        for (let i = event.resultIndex; i < event.results.length; ++i) {
          transcript += event.results[i][0].transcript;
        }
        const answerInput = document.getElementById('patient-answer-input');
        if (answerInput && transcript) {
          answerInput.value = transcript;
        }
        this.setState(SpeechState.TRANSCRIBING);
      };

      this.recognition.onerror = (event) => {
        console.warn('Speech recognition error:', event.error);
        this.isListening = false;
        this.playBeep('error');
        this.setState(SpeechState.ERROR, `Speech error (${event.error})`);
      };

      this.recognition.onend = () => {
        this.isListening = false;
        this.playBeep('stop');
        const answerInput = document.getElementById('patient-answer-input');
        if (answerInput && answerInput.value.trim().length > 0) {
          this.setState(SpeechState.SUCCESS);
        } else {
          this.setState(SpeechState.IDLE);
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

  toggleListening() {
    if (!this.recognition) {
      alert('Speech recognition is not supported in this browser. Please type your answer.');
      return;
    }

    if (this.isListening) {
      this.recognition.stop();
    } else {
      try {
        this.recognition.lang = this.langLocaleMap[this.currentLanguage] || 'en-IN';
        this.recognition.start();
      } catch (err) {
        console.error('Speech recognition start failed:', err);
        this.setState(SpeechState.ERROR, "Microphone access failed.");
      }
    }
  },

  getIndianFemaleVoice(targetLang) {
    if (!this.synth) return null;
    const voices = this.synth.getVoices();
    if (!voices || voices.length === 0) return null;

    const locale = this.langLocaleMap[targetLang] || 'en-IN';
    const targetLangCode = targetLang || 'en';
    
    // 1. Search for named Indian female voices (Microsoft Neerja, Heera, Swara, Aditi, Priya, etc.)
    const indianFemaleNames = ['neerja', 'heera', 'swara', 'aditi', 'priya', 'shashi', 'veena', 'anjali', 'kavya', 'kalpana', 'geeta', 'sunita', 'alka', 'deepa', 'divya', 'sneha'];
    const namedMatch = voices.find(v => {
      const nameLow = v.name.toLowerCase();
      return indianFemaleNames.some(fn => nameLow.includes(fn));
    });
    if (namedMatch) return namedMatch;

    // 2. Search for Indian locale voices that are female (e.g. en-IN or hi-IN)
    const localeMatches = voices.filter(v => {
      const langNorm = v.lang.replace('_', '-').toLowerCase();
      return langNorm.startsWith(locale.toLowerCase()) || langNorm.startsWith(targetLangCode.toLowerCase());
    });

    const femaleMatch = localeMatches.find(v => {
      const nameLow = v.name.toLowerCase();
      const isMale = nameLow.includes('male') || nameLow.includes('guy') || nameLow.includes('george') || nameLow.includes('david') || nameLow.includes('ravi') || nameLow.includes('mark') || nameLow.includes('prabhat');
      return (nameLow.includes('female') || nameLow.includes('woman') || nameLow.includes('google') || !isMale);
    });
    if (femaleMatch) return femaleMatch;
    if (localeMatches.length > 0) return localeMatches[0];

    // 3. Fallback to any clear female English voice
    const anyFemale = voices.find(v => {
      const nameLow = v.name.toLowerCase();
      return nameLow.includes('female') || nameLow.includes('zira') || nameLow.includes('samantha') || nameLow.includes('victoria') || nameLow.includes('karen') || nameLow.includes('woman');
    });
    return anyFemale || voices[0];
  },

  speakStepGuidance(stepNum, lang = 'en') {
    if (this.isMuted) return;

    const guidanceMap = {
      1: "Namaste! Welcome to MediKiosk intelligent hospital check-in. Please touch the Begin Check-In button on your screen to start.",
      2: "Please choose your preferred language by tapping any box on the screen: English, Hindi, Kannada, Tamil, Telugu, and more.",
      3: "Please listen carefully to our safety notice. MediKiosk prepares your symptom summary for your attending doctor. Your doctor will personally examine you and write all prescriptions. Please tap the agreement box and touch Continue.",
      4: "Please enter or speak your name, age, gender, and phone number. If a family member or attendant is helping you, you can check the attendant box.",
      5: "What health problem or pain brings you to the clinic today? Touch any number from 1 to 10 to indicate your pain level, or speak your symptoms.",
      6: "If you have previous doctor prescriptions or lab test reports, you can upload them here, or tap Skip to proceed.",
      7: "Please listen to the clinical question and speak your answer using the microphone button.",
      8: "Your clinical check-in is complete! Your consultation ticket is ready. Please proceed to the waiting area of your assigned department."
    };
    const text = guidanceMap[stepNum];
    if (text) {
      this.speakText(text, lang);
    }
  },

  updateButtonStates(state) {
    const buttons = document.querySelectorAll('#btn-speak-question, .btn-icon-round');
    buttons.forEach(btn => {
      if (state === 'playing') {
        btn.innerHTML = '🔊';
        btn.classList.add('is-playing');
        btn.classList.remove('is-muted');
        btn.title = "Audio Playing — Tap to Mute";
      } else if (state === 'muted') {
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

  toggleSpeak(text, lang = null) {
    if (!this.synth) return false;

    // If currently speaking, mute & stop audio
    if (this.synth.speaking || this.isSpeaking) {
      this.stopAllAudio();
      this.isMuted = true;
      this.updateButtonStates('muted');
      return false;
    }

    // Otherwise unmute and speak
    this.isMuted = false;
    const toSpeak = text || this.lastSpokenText || "Welcome to MediKiosk.";
    this.speakText(toSpeak, lang);
    return true;
  },

  stopAllAudio() {
    if (this.synth) {
      this.synth.cancel();
    }
    this.isSpeaking = false;
    this.updateButtonStates('idle');
  },

  speakText(text, lang = null) {
    if (!this.synth) return;
    this.synth.cancel();

    this.lastSpokenText = text;
    this.isMuted = false;

    const targetLang = lang || this.currentLanguage;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = this.langLocaleMap[targetLang] || 'en-IN';
    utterance.rate = 0.88;  // Calm, accessible pace for patients
    utterance.pitch = 1.12; // Natural, warm Indian female pitch

    const assignedVoice = this.getIndianFemaleVoice(targetLang);
    if (assignedVoice) {
      utterance.voice = assignedVoice;
    }

    this.updateButtonStates('playing');

    utterance.onend = () => {
      this.isSpeaking = false;
      this.updateButtonStates('idle');
    };

    utterance.onerror = () => {
      this.isSpeaking = false;
      this.updateButtonStates('idle');
    };

    this.isSpeaking = true;
    this.synth.speak(utterance);
  }
};

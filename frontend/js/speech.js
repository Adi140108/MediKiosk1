// MediKiosk Production-Grade 6-State Speech-to-Speech Engine
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
  recognition: null,
  synth: window.speechSynthesis || null,
  currentLanguage: 'en',
  audioCtx: null,

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

  toggleSpeak(text, lang = null) {
    if (!this.synth) return false;

    // If currently speaking, mute/stop audio
    if (this.synth.speaking || this.isSpeaking) {
      this.synth.cancel();
      this.isSpeaking = false;
      document.querySelectorAll('#btn-speak-question, .btn-icon-round').forEach(btn => {
        btn.classList.remove('pulse-audio');
      });
      return false;
    }

    // Otherwise unmute and speak
    this.speakText(text, lang);
    return true;
  },

  speakText(text, lang = null) {
    if (!this.synth) return;
    this.synth.cancel();

    const targetLang = lang || this.currentLanguage;
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = this.langLocaleMap[targetLang] || 'en-IN';
    utterance.rate = 0.95;
    utterance.pitch = 1.0;

    const voices = this.synth.getVoices();
    const matchedVoice = voices.find(v => v.lang.startsWith(targetLang) || v.lang.startsWith(this.langLocaleMap[targetLang]));
    if (matchedVoice) {
      utterance.voice = matchedVoice;
    }

    const speakerButtons = document.querySelectorAll('#btn-speak-question, .btn-icon-round');
    speakerButtons.forEach(btn => btn.classList.add('pulse-audio'));

    utterance.onend = () => {
      this.isSpeaking = false;
      speakerButtons.forEach(btn => btn.classList.remove('pulse-audio'));
    };

    utterance.onerror = () => {
      this.isSpeaking = false;
      speakerButtons.forEach(btn => btn.classList.remove('pulse-audio'));
    };

    this.isSpeaking = true;
    this.synth.speak(utterance);
  }
};

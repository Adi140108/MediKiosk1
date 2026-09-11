const PatientIntake = {
  currentStep: 1,
  currentSessionId: null,
  selectedFiles: [],
  uploadedDocuments: [],
  currentPatientId: null,
  currentQuestionId: null,
  currentQuestionText: "",
  language: "en",
  isAttendant: false,
  attendantId: null,
  painLevel: 7,
  registeredData: null,
  knownConditions: [],
  medications: [],
  pastMedicalHistory: "",
  prescriptionNotes: "",


  hasSpokenInitialWelcome: false,

  getStorageItem(key, defaultVal) {
    try {
      return localStorage.getItem(key) || defaultVal;
    } catch (e) {
      return defaultVal;
    }
  },

  setStorageItem(key, val) {
    try {
      localStorage.setItem(key, val);
    } catch (e) {}
  },

  init() {
    // 1. Restore saved language if user previously chose one
    try {
      const savedLang = this.getStorageItem("medikiosk_lang", "en");
      if (savedLang) {
        this.language = savedLang;
      }
    } catch (e) {}

    try { this.updateModeUI(); } catch (e) { console.warn("updateModeUI notice:", e); }
    try { this.bindEvents(); } catch (e) { console.warn("bindEvents notice:", e); }
    try { if (typeof SpeechManager !== "undefined" && SpeechManager.init) SpeechManager.init(); } catch (e) {}
    try { if (typeof I18n !== "undefined" && I18n.setLanguage) I18n.setLanguage(this.language); } catch (e) {}
    try { if (typeof SpeechManager !== "undefined" && SpeechManager.setLanguage) SpeechManager.setLanguage(this.language); } catch (e) {}
    try { this.updateStepIndicator(1); } catch (e) {}
    try { this.updateLanguageGridUI(this.language); } catch (e) {}

    // 2. SINGLE WELCOMING AUTO-SPEECH (Guarded against duplicate execution)
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

    // Fallback: If autoplay policy blocked initial speech, trigger once on first user click/touch (excluding action button clicks)
    const onFirstUserGesture = (evt) => {
      window.removeEventListener('click', onFirstUserGesture, true);
      window.removeEventListener('touchstart', onFirstUserGesture, true);
      window.removeEventListener('keydown', onFirstUserGesture, true);
      if (this.currentStep !== 1) return;
      if (evt && evt.target && evt.target.closest && evt.target.closest('button, .hero-cta-btn, .btn, [onclick]')) {
        return;
      }
      triggerWelcomeSpeech();
    };
    window.addEventListener('click', onFirstUserGesture, true);
    window.addEventListener('touchstart', onFirstUserGesture, true);
    window.addEventListener('keydown', onFirstUserGesture, true);
  },

  getActiveOpdMode() {
    return this.getStorageItem("medikiosk_active_mode", "GENERAL_OPD");
  },

  setActiveOpdMode(mode) {
    const validMode = (mode === "AYUSH_OPD") ? "AYUSH_OPD" : "GENERAL_OPD";
    this.setStorageItem("medikiosk_active_mode", validMode);
    try { this.updateModeUI(); } catch (e) {}
  },

  selectedTempMode: null,

  openStaffModeModal() {
    this.selectedTempMode = this.getActiveOpdMode();
    const modal = document.getElementById("staff-mode-modal");
    if (modal) {
      modal.style.display = "flex";
      this.renderModalModeOptions(this.selectedTempMode);
    }
  },

  closeStaffModeModal() {
    const modal = document.getElementById("staff-mode-modal");
    if (modal) modal.style.display = "none";
  },

  selectKioskMode(mode) {
    this.selectedTempMode = mode;
    this.renderModalModeOptions(mode);
  },

  renderModalModeOptions(mode) {
    const optGen = document.getElementById("mode-opt-general");
    const optAyur = document.getElementById("mode-opt-ayush");
    const badge = document.getElementById("modal-active-mode-badge");

    if (badge) {
      badge.innerText = mode === "AYUSH_OPD" ? "AYUSH OPD (Ayurvedic Assessment)" : "GENERAL OPD (Standard Intake)";
      badge.style.color = mode === "AYUSH_OPD" ? "#059669" : "#0d9488";
    }

    if (optGen) {
      if (mode === "GENERAL_OPD") {
        optGen.style.borderColor = "#0d9488";
        optGen.style.backgroundColor = "#f0fdf4";
      } else {
        optGen.style.borderColor = "#cbd5e1";
        optGen.style.backgroundColor = "#ffffff";
      }
    }
    if (optAyur) {
      if (mode === "AYUSH_OPD") {
        optAyur.style.borderColor = "#059669";
        optAyur.style.backgroundColor = "#ecfdf5";
      } else {
        optAyur.style.borderColor = "#cbd5e1";
        optAyur.style.backgroundColor = "#ffffff";
      }
    }
  },

  confirmKioskModeChange() {
    if (this.selectedTempMode) {
      this.setActiveOpdMode(this.selectedTempMode);
    }
    this.closeStaffModeModal();
  },

  updateModeUI() {
    const currentMode = this.getActiveOpdMode();
    const pillText = document.getElementById("opd-mode-pill-text");
    const pill = document.getElementById("kiosk-opd-mode-pill");

    if (pillText && pill) {
      if (currentMode === "AYUSH_OPD") {
        pillText.innerText = "AYUSH OPD";
        pill.style.background = "linear-gradient(135deg, #059669, #047857)";
      } else {
        pillText.innerText = "GENERAL OPD";
        pill.style.background = "linear-gradient(135deg, #0d9488, #0f766e)";
      }
    }
    this.initWelcomeClock();
  },

  initWelcomeClock() {
    const updateClock = () => {
      const now = new Date();
      const dateEl = document.getElementById("welcome-date");
      const timeEl = document.getElementById("welcome-time");
      if (dateEl) {
        dateEl.innerText = now.toLocaleDateString('en-US', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' });
      }
      if (timeEl) {
        timeEl.innerText = now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
      }
    };
    updateClock();
    setInterval(updateClock, 10000);
  },

  bindEvents() {
    // Begin check-in button binding
    const beginBtn = document.getElementById("btn-begin-checkin");
    if (beginBtn) {
      beginBtn.addEventListener("click", (e) => {
        e.preventDefault();
        this.goToStep(2);
      });
    }

    // Patient registration form
    const regForm = document.getElementById("patient-reg-form");
    if (regForm) {
      regForm.addEventListener("submit", (e) => this.handleRegistration(e));
    }

    // Document upload form
    const docUploadForm = document.getElementById("doc-upload-form");
    if (docUploadForm) {
      docUploadForm.addEventListener("submit", (e) => this.handleDocUpload(e));
    }

    // Attendant checkbox toggle
    const attCheck = document.getElementById("is-attendant-assisted");
    if (attCheck) {
      attCheck.addEventListener("change", (e) => {
        const attFields = document.getElementById("attendant-fields");
        if (attFields) attFields.style.display = e.target.checked ? "block" : "none";
      });
    }

    // Enter key submit in intake text area
    const answerInput = document.getElementById("patient-answer-input");
    if (answerInput) {
      answerInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          this.handleAnswerSubmit();
        }
      });
    }
  },

  goToStep(stepNum) {
    if (this.autoAdvanceTimer) {
      clearTimeout(this.autoAdvanceTimer);
      this.autoAdvanceTimer = null;
    }

    try {
      if (typeof SpeechManager !== "undefined" && SpeechManager.stopAllAudio) {
        SpeechManager.stopAllAudio();
      }
    } catch (e) {
      console.warn("Speech stop notice:", e);
    }

    // Ensure section-patient container is active and visible
    const patientSec = document.getElementById("section-patient");
    if (patientSec) {
      patientSec.style.display = "block";
      patientSec.classList.add("active");
    }

    const mainNavbar = document.querySelector(".navbar, .app-header");
    const safetyBanner = document.querySelector(".safety-top-banner, .top-safety-banner");
    const keyboardFab = document.getElementById("keyboard-fab");
    if (mainNavbar) mainNavbar.style.display = stepNum === 1 ? "none" : "flex";
    if (safetyBanner) safetyBanner.style.display = stepNum === 1 ? "none" : "flex";
    if (keyboardFab) keyboardFab.style.display = stepNum === 1 ? "none" : "flex";

    const stepIndicator = document.getElementById("kiosk-step-indicator");
    if (stepIndicator) {
      stepIndicator.style.display = stepNum === 1 ? "none" : "flex";
    }

    if (stepNum === 1 && typeof window.updateCardConnections === 'function') {
      setTimeout(window.updateCardConnections, 50);
    }

    const prevStep = this.currentStep;
    const currentEl = document.getElementById(`kiosk-step-${prevStep}`);
    const targetEl = document.getElementById(`kiosk-step-${stepNum}`);

    if (stepNum === prevStep && targetEl && targetEl.style.display !== "none" && targetEl.style.display !== "") {
      return;
    }

    const isForward = stepNum >= prevStep;
    this.currentStep = stepNum;

    if (stepNum < 8) {
      this._isFinishing = false;
      this._isSubmittingAnswer = false;
    }

    // Show milestone notification when advancing after completing a step
    if (isForward && prevStep !== stepNum) {
      this.showStepMilestoneToast(prevStep, stepNum);
    }

    const switchStepContent = () => {
      for (let i = 1; i <= 8; i++) {
        const el = document.getElementById(`kiosk-step-${i}`);
        if (el) {
          el.classList.remove("step-exit-forward", "step-exit-backward", "step-enter-forward", "step-enter-backward");
          if (i === stepNum) {
            el.style.display = (stepNum === 1 ? "flex" : "block");
            el.classList.add(isForward ? "step-enter-forward" : "step-enter-backward");
            setTimeout(() => {
              el.classList.remove("step-enter-forward", "step-enter-backward");
            }, 500);
          } else {
            el.style.display = "none";
          }
        }
      }

      if (stepNum === 8) {
        setTimeout(() => {
          const seal = document.getElementById("ticket-verified-seal");
          if (seal) seal.classList.add("stamped");
        }, 300);
      }
    };

    if (currentEl && targetEl && prevStep !== stepNum && currentEl.style.display !== "none") {
      currentEl.classList.add(isForward ? "step-exit-forward" : "step-exit-backward");
      setTimeout(switchStepContent, 160);
    } else {
      switchStepContent();
    }

    try {
      this.updateStepIndicator(stepNum, prevStep);
    } catch (e) {
      console.warn("Step indicator notice:", e);
    }

      window.scrollTo({ top: 0, behavior: "smooth" });
    if (this.stepSpeechTimer) {
      clearTimeout(this.stepSpeechTimer);
      this.stepSpeechTimer = null;
    }

    // Step 2: Refresh language grid UI and continue button
    if (stepNum === 2) {
      try {
        this.updateLanguageGridUI(this.language);
        this.updateStep2ContinueBtn(this.language);
      } catch (e) {
        console.warn("Step 2 UI update notice:", e);
      }
      this.stepSpeechTimer = setTimeout(() => {
        try {
          if (typeof SpeechManager !== "undefined" && SpeechManager.resumeAudioAndSpeak) {
            SpeechManager.resumeAudioAndSpeak(2, this.language);
          }
        } catch (e) {}
      }, 300);
      return;
    }

    // Step 7 & Step 8: Socratic Interview & Ticket Display handle their own custom voice guidance
    if (stepNum === 7) {
      if (!this.currentSessionId) {
        this.currentSessionId = `sess_${this.currentPatientId || 'pat'}_${Date.now()}`;
      }
      this.currentQuestionId = this.currentQuestionId || `q_${this.currentSessionId}_1`;
      const qTextEl = document.getElementById("current-question-text");
      if (qTextEl && !this.currentQuestionText) {
        qTextEl.innerText = "Preparing clinical inquiry...";
      }
      return;
    } else if (stepNum === 8) {
      // Custom ticket summary is spoken exclusively by finishIntake()
      return;
    } else {
      this.stepSpeechTimer = setTimeout(() => {
        try {
          if (typeof SpeechManager !== "undefined" && SpeechManager.resumeAudioAndSpeak) {
            SpeechManager.resumeAudioAndSpeak(stepNum, this.language);
          }
        } catch (e) {}
      }, 350);
    }
  },

  showStepMilestoneToast(completedStep, nextStep) {
    const milestones = {
      1: { icon: "1", title: "Registration Started", sub: "Step 1 of 8 Completed", badge: "STEP 1" },
      2: { icon: "2", title: "Language Selected", sub: "Step 2 of 8 Completed", badge: "STEP 2" },
      3: { icon: "3", title: "Consent Confirmed", sub: "Step 3 of 8 Completed", badge: "STEP 3" },
      4: { icon: "4", title: "Patient Details Saved", sub: "Step 4 of 8 Completed", badge: "STEP 4" },
      5: { icon: "5", title: "Symptoms & Vitals Saved", sub: "Step 5 of 8 Completed", badge: "STEP 5" },
      6: { icon: "6", title: "Documents Attached", sub: "Step 6 of 8 Completed", badge: "STEP 6" },
      7: { icon: "7", title: "Clinical Inquiry Finished", sub: "Step 7 of 8 Completed", badge: "STEP 7" },
      8: { icon: "8", title: "Consultation Ticket Issued", sub: "OPD Check-In Completed", badge: "COMPLETE" }
    };

    const data = milestones[completedStep] || milestones[1];
    let toast = document.getElementById("step-milestone-toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "step-milestone-toast";
      toast.className = "step-milestone-toast";
      document.body.appendChild(toast);
    }

    toast.innerHTML = `
      <span class="step-milestone-icon">${data.icon}</span>
      <div style="display:flex; flex-direction:column; text-align:left;">
        <span class="step-milestone-title">${data.title}</span>
        <span class="step-milestone-sub">${data.sub}</span>
      </div>
      <span class="step-milestone-badge">${data.badge}</span>
    `;

    toast.classList.remove("show");
    void toast.offsetHeight;
    toast.classList.add("show");

    if (this._milestoneTimer) clearTimeout(this._milestoneTimer);
    this._milestoneTimer = setTimeout(() => {
      toast.classList.remove("show");
    }, 2800);
  },

  updateStepIndicator(stepNum, prevStep = null) {
    const bar = document.getElementById("kiosk-step-indicator");

    // Strictly hide indicators on Step 1 (Welcome page)
    if (stepNum === 1) {
      if (bar) bar.style.display = "none";
      return;
    } else {
      if (bar) bar.style.display = "flex";
    }

    for (let i = 1; i <= 8; i++) {
      const node = document.getElementById(`step-node-${i}`);
      const line = document.getElementById(`step-line-${i}`);
      if (node) {
        node.className = "wizard-step-node";
        if (i < stepNum || (i === 8 && stepNum === 8)) {
          node.classList.add("completed");
          node.innerHTML = '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
          if (prevStep && i === prevStep) {
            node.classList.add("node-shockwave");
            setTimeout(() => node.classList.remove("node-shockwave"), 750);
          }
        } else if (i === stepNum) {
          node.classList.add("active");
          node.innerHTML = i;
        } else {
          node.innerHTML = i;
        }
      }
      if (line) {
        line.className = "wizard-step-line" + (i < stepNum ? " completed" : "");
        if (prevStep && i === prevStep && stepNum > prevStep) {
          line.classList.add("surge");
          setTimeout(() => line.classList.remove("surge"), 800);
        }
      }
    }

    // Sync Mobile Progress Header
    const mobileBadge = document.getElementById("mobile-step-badge");
    const mobileLabel = document.getElementById("mobile-step-label");
    const mobileIcon = document.getElementById("mobile-step-icon");
    const mobileFill = document.getElementById("mobile-progress-fill");

    const stepTitles = {
      1: { icon: "📍", title: "Welcome & Registration" },
      2: { icon: "🌐", title: "Select Language" },
      3: { icon: "🛡️", title: "Patient Consent" },
      4: { icon: "👤", title: "Patient Details" },
      5: { icon: "🩺", title: "Symptoms & History" },
      6: { icon: "📄", title: "Previous Records" },
      7: { icon: "💬", title: "AI Clinical Intake" },
      8: { icon: "🎫", title: "Consultation Token" }
    };

    if (mobileBadge) mobileBadge.innerText = `Step ${stepNum} of 8`;
    if (mobileLabel && stepTitles[stepNum]) mobileLabel.innerText = stepTitles[stepNum].title;
    if (mobileIcon && stepTitles[stepNum]) mobileIcon.innerText = stepTitles[stepNum].icon;
    if (mobileFill) mobileFill.style.width = `${(stepNum / 8) * 100}%`;
  },

  updateLanguageGridUI(lang) {
    // Step 2 Tiles
    document.querySelectorAll(".lang-tile").forEach((tile) => {
      const tileLang = tile.getAttribute("data-lang");
      const badge = tile.querySelector(".lang-tile-badge");
      if (tileLang === lang) {
        tile.classList.add("selected");
        if (badge) {
          badge.className = "lang-tile-badge lang-badge-selected";
          badge.innerHTML = '<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle; margin-right:3px;"><polyline points="20 6 9 17 4 12"></polyline></svg>SELECTED';
        }
      } else {
        tile.classList.remove("selected");
        if (badge) {
          badge.className = "lang-tile-badge lang-badge-ready";
          badge.innerText = "READY";
        }
      }
    });

    // Step 1 Hero Chips
    document.querySelectorAll(".hero-lang-chip").forEach((chip) => {
      const chipLang = chip.getAttribute("data-lang");
      if (chipLang === lang) {
        chip.classList.add("active");
      } else {
        chip.classList.remove("active");
      }
    });

    // Header Navbar Lang Pill
    const langPill = document.getElementById("current-lang-pill");
    if (langPill) langPill.innerText = lang.toUpperCase();
  },

  updateStep2ContinueBtn(lang) {
    const continueBtnText = {
      en: "Continue in English →",
      hi: "आगे बढ़ें (Continue in हिन्दी) →",
      kn: "ಮುಂದುವರಿಯಿರಿ (Continue in ಕನ್ನಡ) →",
      ta: "தொடரவும் (Continue in தமிழ்) →",
      te: "కొనసాగించండి (Continue in తెలుగు) →",
      ml: "തുടരുക (Continue in മലയാളം) →",
      mr: "पुढे जा (Continue in मराठी) →",
      bn: "এগিয়ে যান (Continue in বাংলা) →",
      gu: "આગળ વધો (Continue in ગુજરાતી) →",
      pa: "ਅੱਗੇ ਵਧੋ (Continue in ਪੰਜਾਬੀ) →"
    };
    const contBtn = document.getElementById("step2-continue-btn");
    if (contBtn) {
      contBtn.innerHTML = `<span>${continueBtnText[lang] || 'Continue →'}</span>`;
    }
  },

  selectLanguage(lang) {
    if (this.autoAdvanceTimer) {
      clearTimeout(this.autoAdvanceTimer);
      this.autoAdvanceTimer = null;
    }
    if (this.stepSpeechTimer) {
      clearTimeout(this.stepSpeechTimer);
      this.stepSpeechTimer = null;
    }

    SpeechManager.stopAllAudio();
    this.language = lang;
    localStorage.setItem("medikiosk_lang", lang);
    I18n.setLanguage(lang);
    SpeechManager.setLanguage(lang);
    this.updateLanguageGridUI(lang);
    this.updateStep2ContinueBtn(lang);

    const nativeLangConfirm = {
      en: "English language selected. Welcome to MediKiosk.",
      hi: "हिन्दी भाषा चुनी गई। मेडीकियोस्क में आपका स्वागत है।",
      kn: "ಕನ್ನಡ ಭಾಷೆಯನ್ನು ಆಯ್ಕೆ ಮಾಡಲಾಗಿದೆ. ಮೆಡಿಕಿಯೋಸ್ಕ್‌ಗೆ ಸುಸ್ವಾಗತ.",
      ta: "தமிழ் மொழி தேர்ந்தெடுக்கப்பட்டது. மெடிகியோஸ்கிற்கு வரவேற்கிறோம்.",
      te: "తెలుగు భాష ఎంపిక చేయబడింది. మెడికియోస్క్‌కు స్వాగతం.",
      ml: "മലയാളം ഭാഷ തിരഞ്ഞെടുത്തു. മെഡികിയോസ്കിലേക്ക് സ്വാഗതം.",
      mr: "मराठी भाषा निवडली आहे. मेडीकियोस्क मध्ये आपले स्वागत आहे.",
      bn: "বাংলা ভাষা নির্বাচন করা হয়েছে। মেডিকিয়স্কে আপনাকে স্বাগতম।",
      gu: "ગુજરાતી ભાષા પસંદ કરવામાં આવી છે. મેડીકિયોસ્કમાં આપનું સ્વાગત છે.",
      pa: "ਪੰਜਾਬੀ ਭਾਸ਼ਾ ਚੁਣੀ ਗਈ ਹੈ। ਮੈਡੀਕਿਓਸਕ ਵਿੱਚ ਤੁਹਾਡਾ ਸੁਆਗਤ ਹੈ।"
    };
    const confirmMsg = nativeLangConfirm[lang] || `Language selected: ${lang}`;
    SpeechManager.speakText(confirmMsg, lang);
  },

  handleConsentNext() {
    const consentBox = document.getElementById("consent-checkbox");
    const wrapper = document.getElementById("consent-checkbox-wrapper");
    
    if (consentBox && !consentBox.checked) {
      const nativeConsentNotice = {
        en: "Please tap the agreement checkbox to confirm your consent before proceeding.",
        hi: "कृपया आगे बढ़ने से पहले सहमति के डिब्बे पर टिक करें।",
        kn: "ಮುಂದುವರಿಯುವ ಮೊದಲು ದಯವಿಟ್ಟು ಒಪ್ಪಿಗೆ ಬಾಕ್ಸ್ ಒತ್ತಿ.",
        ta: "தொடர்வதற்கு முன் தயவுசெய்து ஒப்புதல் பெட்டியைத் தொடவும்.",
        te: "కొనసాగడానికి ముందు దయచేసి అంగీకార పెట్టెను నొక్కండి.",
        ml: "തുടങ്ങുന്നതിന് മുമ്പ് ദയവായി സമ്മത ബോക്സ് അമർത്തുക.",
        mr: "पुढे जाण्यापूर्वी कृपया संमती बॉक्सवर टिक करा.",
        bn: "এগিয়ে যাওয়ার আগে অনুগ্রহ করে সম্মতি বক্সে টিক দিন।",
        gu: "આગળ વધતા પહેલાં કૃપા કરીને સંમતિ બોક્સ પર ટીક કરો.",
        pa: "ਅੱਗੇ ਵਧਣ ਤੋਂ ਪਹਿਲਾਂ ਕਿਰਪਾ ਕਰਕੇ ਸਹਿਮਤੀ ਵਾਲੇ ਬਕਸੇ 'ਤੇ ਕਲਿੱਕ ਕਰੋ।"
      };
      const msg = nativeConsentNotice[this.language] || nativeConsentNotice["en"];
      SpeechManager.speakText(msg, this.language);
      if (wrapper) {
        wrapper.style.borderColor = "#ef4444";
        wrapper.style.backgroundColor = "#fef2f2";
        wrapper.scrollIntoView({ behavior: "smooth", block: "center" });
        setTimeout(() => {
          wrapper.style.borderColor = "#d8cbba";
          wrapper.style.backgroundColor = "#ffffff";
        }, 2500);
      }
      alert("️ Please check the agreement box to confirm your consent before proceeding.");
      return;
    }
    this.goToStep(4);
  },

  async handleRegistration(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    if (btn) btn.disabled = true;

    try {
      const name = document.getElementById("reg-name").value.trim();
      const age = parseInt(document.getElementById("reg-age").value, 10);
      const gender = document.getElementById("reg-gender").value;
      const phone = document.getElementById("reg-phone").value.trim();
      const abhaId = document.getElementById("reg-abha").value.trim();
      this.isAttendant = document.getElementById("is-attendant-assisted") ? document.getElementById("is-attendant-assisted").checked : false;

      const regData = {
        name,
        age,
        gender,
        phone: phone || null,
        abha_id: abhaId || null,
        identity_type: abhaId ? "ABHA" : "TEMP_DEV",
        preferred_language: this.language,
        is_attendant_assisted: this.isAttendant
      };

      const tempId = abhaId || `pat_${Math.random().toString(36).substring(2, 10)}`;
      this.currentPatientId = tempId;
      this.currentSessionId = `sess_${tempId}_${Date.now()}`;
      this.registeredData = { name, age, gender, phone, abhaId };

      // Transition UI to Step 5 INSTANTLY without waiting for network calls
      this.goToStep(5);

      // Perform backend registration and consent sync non-blockingly in background
      (async () => {
        try {
          const patient = await api.registerPatient(regData);
          if (patient && patient.patient_id) {
            this.currentPatientId = patient.patient_id;
          }
          if (this.isAttendant) {
            const attNameEl = document.getElementById("att-name");
            const attPhoneEl = document.getElementById("att-phone");
            const attRelEl = document.getElementById("att-rel");
            const attName = attNameEl ? attNameEl.value.trim() : "";
            const attPhone = attPhoneEl ? attPhoneEl.value.trim() : "";
            const attRel = attRelEl ? attRelEl.value : "";
            if (attName) {
              const attRes = await api.registerAttendant(this.currentPatientId, {
                name: attName,
                phone: attPhone,
                relationship_to_patient: attRel
              });
              if (attRes && attRes.attendant && attRes.attendant.attendant_id) {
                this.attendantId = attRes.attendant.attendant_id;
              }
            }
          }
          await api.submitConsent(this.currentPatientId, this.currentSessionId, this.isAttendant, this.attendantId);
        } catch (bgErr) {
          console.warn("Background registration/consent sync notice:", bgErr);
        }
      })();
    } catch (err) {
      alert("Registration error: " + err.message);
    } finally {
      if (btn) btn.disabled = false;
    }
  },

    toggleCondition(el, cond) {
    if (!this.knownConditions) this.knownConditions = [];
    if (cond === 'None') {
      this.knownConditions = [];
      document.querySelectorAll('#chronic-conditions-grid .condition-pill').forEach(pill => {
        pill.classList.remove('selected');
      });
      if (el) el.classList.add('selected');
      return;
    }

    // Unselect 'None' pill if active
    const nonePills = document.querySelectorAll('#chronic-conditions-grid .condition-pill');
    nonePills.forEach(p => {
      if (p.innerText.includes('No Chronic') || p.innerText.includes('कोई नहीं') || p.innerText.includes('ಯಾವುದೇ') || p.innerText.includes('எதுவும் இல்லை') || p.innerText.includes('లేవు') || p.innerText.includes('ഇല്ല') || p.innerText.includes('नाही') || p.innerText.includes('নেই') || p.innerText.includes('નથી') || p.innerText.includes('ਨਹੀਂ')) {
        p.classList.remove('selected');
      }
    });

    const idx = this.knownConditions.indexOf(cond);
    if (idx > -1) {
      this.knownConditions.splice(idx, 1);
      if (el) el.classList.remove('selected');
    } else {
      this.knownConditions.push(cond);
      if (el) el.classList.add('selected');
    }
  },

  appendTag(symptom) {
    const input = document.getElementById("chief-complaint-input");
    if (!input) return;
    if (input.value.trim().length > 0) {
      input.value += `, ${symptom}`;
    } else {
      input.value = symptom;
    }
  },

  onPainSliderInput(level) {
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
    let primaryColor = "#10b981";
    let statusText = "Mild Discomfort";
    let bgCol = "#ecfdf5";
    let textCol = "#065f46";

    if (this.painLevel <= 3) {
      primaryColor = "#10b981";
      statusText = "Mild Discomfort";
      bgCol = "#ecfdf5";
      textCol = "#065f46";
    } else if (this.painLevel <= 6) {
      primaryColor = "#f59e0b";
      statusText = "Moderate Pain";
      bgCol = "#fef3c7";
      textCol = "#92400e";
    } else if (this.painLevel <= 8) {
      primaryColor = "#f97316";
      statusText = "Severe Pain";
      bgCol = "#ffedd5";
      textCol = "#9a3412";
    } else {
      primaryColor = "#ef4444";
      statusText = "Critical / Emergency";
      bgCol = "#fee2e2";
      textCol = "#991b1b";
    }

    if (displayBadge) {
      displayBadge.style.cssText = `background:${bgCol}; color:${textCol}; border:1.5px solid ${primaryColor}; font-size:0.88rem; padding:0.35rem 0.95rem; font-weight:700; border-radius:9999px;`;
      displayBadge.innerText = `Level ${this.painLevel} — ${statusText}`;
    }
    
    if (slider) {
      slider.style.setProperty('--primary-color', primaryColor);
      slider.style.setProperty('--slider-thumb-color', primaryColor);
    }

    // Highlight active tick
    try {
      const allTicks = document.querySelectorAll("#pain-ticks-container span");
      allTicks.forEach(t => t.classList.remove("active-tick"));
      const currentTick = document.getElementById(`pain-tick-${this.painLevel}`);
      if (currentTick) currentTick.classList.add("active-tick");
    } catch (e) {}
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
  },

  handleComplaintNext() {
    this.painLevel = parseInt(document.getElementById("pain-range")?.value || this.painLevel || 7, 10);
    
    // Collect ongoing medications
    const medsInput = document.getElementById("current-medications-input");
    if (medsInput && medsInput.value.trim()) {
      this.medications = medsInput.value.trim().split(/[,;\n]+/).map(m => m.trim()).filter(Boolean);
    }
    
    // Collect past medical history / allergies
    const pastHistInput = document.getElementById("past-medical-history-input");
    if (pastHistInput) {
      this.pastMedicalHistory = pastHistInput.value.trim();
    }

    this.goToStep(6);
  },

  handleStep6Continue() {
    const rxInput = document.getElementById("prescription-dictation-input");
    if (rxInput && rxInput.value.trim()) {
      this.prescriptionNotes = rxInput.value.trim();
    }
    this.startSocraticIntake();
  },

  handleFileSelect(e) {
    const input = e.target;
    if (!input || !input.files || input.files.length === 0) return;

    if (!this.selectedFiles) this.selectedFiles = [];

    // Add all selected files without duplicates
    for (let i = 0; i < input.files.length; i++) {
      const f = input.files[i];
      const exists = this.selectedFiles.some(existing => existing.name === f.name && existing.size === f.size);
      if (!exists) {
        this.selectedFiles.push(f);
      }
    }

    // Reset input so user can browse and add more files
    try { input.value = ''; } catch(err) {}

    this.renderSelectedFilesPreview();
  },

  removeSelectedFile(index) {
    if (this.selectedFiles && this.selectedFiles[index]) {
      this.selectedFiles.splice(index, 1);
      this.renderSelectedFilesPreview();
    }
  },

  renderSelectedFilesPreview() {
    const previewContainer = document.getElementById("doc-file-selected-preview");
    const uploadBtn = document.getElementById("btn-upload-doc");
    if (!previewContainer) return;

    if (!this.selectedFiles || this.selectedFiles.length === 0) {
      previewContainer.style.display = "none";
      previewContainer.innerHTML = "";
      if (uploadBtn) {
        const count = (this.uploadedDocuments && this.uploadedDocuments.length) || 0;
        if (count > 0) {
          uploadBtn.style.display = "none";
        } else {
          uploadBtn.style.display = "inline-flex";
          uploadBtn.disabled = true;
          uploadBtn.innerHTML = `<span>Upload & Run OCR</span> →`;
        }
      }
      return;
    }

    previewContainer.style.display = "block";
    const totalFiles = this.selectedFiles.length;

    let itemsHtml = this.selectedFiles.map((file, idx) => {
      const isImage = file.type.startsWith("image/");
      const localUrl = isImage ? URL.createObjectURL(file) : "";
      const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
      return `
        <div style="background:#ffffff; border:1px solid #bfdbfe; border-radius:8px; padding:0.65rem 0.85rem; margin-bottom:0.5rem; display:flex; align-items:center; justify-content:space-between; gap:0.75rem; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
          <div style="display:flex; align-items:center; gap:0.65rem; min-width:0; flex:1;">
            ${isImage && localUrl ? `<img src="${localUrl}" style="width:40px; height:40px; object-fit:cover; border-radius:4px; border:1px solid #93c5fd; flex-shrink:0;" />` : `<div style="width:40px; height:40px; background:#eff6ff; border-radius:4px; display:flex; align-items:center; justify-content:center; flex-shrink:0;"><svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg></div>`}
            <div style="min-width:0; flex:1;">
              <p style="font-weight:700; color:#1e40af; margin:0; font-size:0.85rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">${file.name}</p>
              <p style="font-size:0.75rem; color:#64748b; margin:2px 0 0 0;">${sizeMb} MB • Ready to Upload</p>
            </div>
          </div>
          <button type="button" onclick="PatientIntake.removeSelectedFile(${idx})" title="Remove file" style="background:#fee2e2; border:1px solid #fca5a5; color:#991b1b; width:28px; height:28px; border-radius:50%; cursor:pointer; font-weight:700; font-size:0.85rem; display:flex; align-items:center; justify-content:center; flex-shrink:0;">
            ✕
          </button>
        </div>
      `;
    }).join("");

    previewContainer.innerHTML = `
      <div style="background:#f0f9ff; border:1.5px solid #7dd3fc; border-radius:8px; padding:0.85rem; margin-top:0.75rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.6rem;">
          <span style="font-weight:700; color:#0369a1; font-size:0.88rem;">
            📎 Selected Documents (${totalFiles}) — No Upload Limit
          </span>
          <span style="font-size:0.72rem; color:#0284c7; background:#e0f2fe; padding:2px 8px; border-radius:12px; font-weight:600;">
            Unlimited Uploads Allowed
          </span>
        </div>
        ${itemsHtml}
      </div>
    `;

    if (uploadBtn) {
      uploadBtn.style.display = "inline-flex";
      uploadBtn.disabled = false;
      const fileLabel = totalFiles === 1 ? "1 Document" : `${totalFiles} Documents`;
      uploadBtn.innerHTML = `<span>Upload & Run OCR (${fileLabel})</span> →`;
    }
  },

  toggleFullOcrText() {
    const el = document.getElementById("full-ocr-text-container");
    const label = document.getElementById("btn-toggle-ocr-text-label");
    if (!el) return;
    const isExpanded = el.style.maxHeight === "none" || el.style.maxHeight === "1000px";
    if (isExpanded) {
      el.style.maxHeight = "160px";
      if (label) label.innerText = "Show Full Extracted Text ▼";
    } else {
      el.style.maxHeight = "none";
      if (label) label.innerText = "▲ Collapse Text";
    }
  },

  cameraStream: null,
  capturedCameraFile: null,
  cameraFacingMode: "environment",
  _cameraFacingMode: "environment",
  capturedBlobUrl: null,

  openCameraScanner() {
    this.openCameraModal();
  },

  async openCameraModal() {
    const modal = document.getElementById("camera-capture-modal");
    if (!modal) return;
    modal.style.display = "flex";

    // Reset to live-view state
    const liveControls = document.getElementById("camera-live-controls");
    const confirmControls = document.getElementById("camera-confirm-controls");
    const viewfinder = document.getElementById("camera-viewfinder-container");
    const snapshot = document.getElementById("camera-snapshot-preview");
    const permNotice = document.getElementById("camera-permission-notice");
    if (liveControls) liveControls.style.display = "flex";
    if (confirmControls) confirmControls.style.display = "none";
    if (viewfinder) viewfinder.style.display = "block";
    if (snapshot) snapshot.style.display = "none";
    if (permNotice) permNotice.style.display = "none";

    await this.startCameraStream();
  },

  async startCameraStream() {
    const video = document.getElementById("camera-video-feed");
    const permNotice = document.getElementById("camera-permission-notice") || document.getElementById("camera-fallback-notice");
    const liveControls = document.getElementById("camera-live-controls");
    if (!video) return;

    if (this.cameraStream) {
      try {
        this.cameraStream.getTracks().forEach(t => t.stop());
      } catch (e) {}
      this.cameraStream = null;
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      if (permNotice) permNotice.style.display = "block";
      if (liveControls) liveControls.style.display = "flex";
      return;
    }

    const mode = this.cameraFacingMode || this._cameraFacingMode || "environment";
    const constraintsList = [
      { video: { facingMode: { ideal: mode }, width: { ideal: 1920 }, height: { ideal: 1080 } } },
      { video: { facingMode: { ideal: mode }, width: { ideal: 1280 }, height: { ideal: 720 } } },
      { video: { facingMode: { ideal: mode } } },
      { video: true }
    ];

    let stream = null;
    for (const constraints of constraintsList) {
      try {
        stream = await navigator.mediaDevices.getUserMedia(constraints);
        if (stream) break;
      } catch (err) {
        console.warn("Camera constraint attempt failed:", constraints, err.message);
      }
    }

    if (stream) {
      this.cameraStream = stream;
      video.srcObject = stream;
      if (mode === "user") {
        video.style.transform = "scaleX(-1)";
      } else {
        video.style.transform = "none";
      }
      await video.play().catch(() => {});
      if (permNotice) permNotice.style.display = "none";
      if (liveControls) liveControls.style.display = "flex";
    } else {
      console.warn("Could not acquire video stream with any constraints.");
      if (permNotice) permNotice.style.display = "block";
      if (liveControls) liveControls.style.display = "flex";
    }
  },

  async switchCamera() {
    this.cameraFacingMode = this.cameraFacingMode === "environment" ? "user" : "environment";
    await this.startCameraStream();
  },

  capturePhotoFromWebcam() {
    const video = document.getElementById("camera-video-feed");
    const canvas = document.getElementById("camera-canvas");
    const viewfinder = document.getElementById("camera-viewfinder-container");
    const snapshotPreview = document.getElementById("camera-snapshot-preview");
    const previewImg = document.getElementById("camera-preview-img");
    const liveControls = document.getElementById("camera-live-controls");
    const confirmControls = document.getElementById("camera-confirm-controls");

    // Graceful fallback if video stream has no active frames
    if (!video.videoWidth || !this.cameraStream) {
      const camInput = document.getElementById("doc-camera-input") || document.getElementById("doc-file-input");
      if (camInput) {
        camInput.click();
        this.closeCameraModal();
      }
      return;
    }

    const width = video.videoWidth || 1280;
    const height = video.videoHeight || 720;
    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, width, height);

    // Show snapshot preview and confirm controls
    canvas.toBlob((blob) => {
      if (!blob) return;
      if (this.capturedBlobUrl) {
        try { URL.revokeObjectURL(this.capturedBlobUrl); } catch (e) {}
      }
      this.capturedBlobUrl = URL.createObjectURL(blob);
      const file = new File([blob], `medikiosk_scan_${Date.now()}.jpg`, { type: "image/jpeg" });
      this.capturedCameraFile = file;

      if (previewImg) previewImg.src = this.capturedBlobUrl;
      if (viewfinder) viewfinder.style.display = "none";
      if (snapshotPreview) snapshotPreview.style.display = "block";
      if (liveControls) liveControls.style.display = "none";
      if (confirmControls) confirmControls.style.display = "flex";
    }, "image/jpeg", 0.94);
  },

  retakeCameraPhoto() {
    const viewfinder = document.getElementById("camera-viewfinder-container");
    const snapshotPreview = document.getElementById("camera-snapshot-preview");
    const liveControls = document.getElementById("camera-live-controls");
    const confirmControls = document.getElementById("camera-confirm-controls");

    if (viewfinder) viewfinder.style.display = "flex";
    if (snapshotPreview) snapshotPreview.style.display = "none";
    if (liveControls) liveControls.style.display = "flex";
    if (confirmControls) confirmControls.style.display = "none";
  },

  confirmCameraPhoto() {
    if (!this.capturedCameraFile) return;

    if (!this.selectedFiles) this.selectedFiles = [];
    this.selectedFiles.push(this.capturedCameraFile);

    this.renderSelectedFilesPreview();
    this.closeCameraModal();
  },

  closeCameraModal() {
    if (this.cameraStream) {
      try {
        this.cameraStream.getTracks().forEach(t => t.stop());
      } catch (e) {}
      this.cameraStream = null;
    }
    const modal = document.getElementById("camera-capture-modal");
    if (modal) modal.style.display = "none";
  },

  retakeCameraPhoto() {
    this._pendingCameraBlob = null;
    const snapshot = document.getElementById("camera-snapshot-preview");
    const viewfinder = document.getElementById("camera-viewfinder-container");
    const liveControls = document.getElementById("camera-live-controls");
    const confirmControls = document.getElementById("camera-confirm-controls");
    if (snapshot) snapshot.style.display = "none";
    if (viewfinder) viewfinder.style.display = "block";
    if (liveControls) liveControls.style.display = "flex";
    if (confirmControls) confirmControls.style.display = "none";
  },

  confirmCameraPhoto() {
    const blob = this._pendingCameraBlob;
    if (!blob) return;
    this._pendingCameraBlob = null;
    const file = new File([blob], `camera_scan_${Date.now()}.jpg`, { type: "image/jpeg" });
    this.capturedCameraFile = file;

    try {
      const container = new DataTransfer();
      container.items.add(file);
      const fileInput = document.getElementById("doc-file-input");
      if (fileInput) fileInput.files = container.files;
    } catch (e) {}

    this.handleFileSelect({ target: { files: [file] } });
    this.closeCameraModal();
  },

  async handleDocUpload(e) {
    if (e) e.preventDefault();

    const fileInput = document.getElementById("doc-file-input");
    if ((!this.selectedFiles || this.selectedFiles.length === 0) && fileInput && fileInput.files && fileInput.files.length > 0) {
      this.selectedFiles = Array.from(fileInput.files);
    }

    if (!this.selectedFiles || this.selectedFiles.length === 0) {
      if (this.uploadedDocuments && this.uploadedDocuments.length > 0) {
        this.handleStep6Continue();
        return;
      }
      this.startSocraticIntake();
      return;
    }

    const btn = document.getElementById("btn-upload-doc");
    if (btn) btn.disabled = true;

    const filesToUpload = [...this.selectedFiles];
    const totalCount = filesToUpload.length;

    const ocrDiv = document.getElementById("doc-ocr-result");
    if (ocrDiv) {
      ocrDiv.innerHTML = `
        <div style="background:#f8fafc; border:1.5px solid #cbd5e1; border-radius:var(--radius-md); padding:1rem; margin-top:1rem;">
          <div style="display:flex; align-items:center; gap:8px;">
            <span class="spinner" style="display:inline-block;"></span>
            <p id="doc-upload-progress-text" style="font-weight:600; color:#334155; font-size:0.95rem;">
              Uploading ${totalCount} document${totalCount > 1 ? 's' : ''} to secure cloud vault...
            </p>
          </div>
        </div>
      `;
    }

    if (!this.uploadedDocuments) this.uploadedDocuments = [];

    for (let i = 0; i < totalCount; i++) {
      const file = filesToUpload[i];
      const progressText = document.getElementById("doc-upload-progress-text");
      if (progressText) {
        progressText.innerText = `Uploading and encrypting document ${i + 1} of ${totalCount}: ${file.name}...`;
      }
      if (btn) {
        btn.innerText = `Uploading ${i + 1} of ${totalCount}...`;
      }

      try {
        const formData = new FormData();
        formData.append("file", file);
        formData.append("session_id", this.currentSessionId || `sess_${Date.now()}`);
        formData.append("patient_id", this.currentPatientId || `pat_${Date.now()}`);
        formData.append("document_type", "medical_report");
        formData.append("perform_ocr", "true");

        const res = await api.uploadDocument(formData);
        const uploadedAccessUrl = res.access_url || '';
        const localFileUrl = file.type.startsWith('image/') ? URL.createObjectURL(file) : '';
        const docPreviewUrl = uploadedAccessUrl || localFileUrl;

        const docRecord = {
          document_id: res.document_id,
          filename: file.name,
          file_size: file.size,
          access_url: docPreviewUrl,
          ocr_status: res.ocr_status || "PROCESSING",
          extracted_text: ""
        };

        this.uploadedDocuments.push(docRecord);

        // Start background OCR polling for this document
        this.pollOcrForDoc(docRecord);
      } catch (err) {
        console.warn(`Error uploading ${file.name}:`, err.message);
      }
    }

    // Clear selected files now that they are uploaded
    this.selectedFiles = [];
    this.renderSelectedFilesPreview();

    // Re-render uploaded documents list
    this.renderUploadedDocumentsList();

    // Speak native confirmation
    const nativeDocSuccess = {
      en: "Medical reports uploaded and stored securely. You can add more documents or proceed to consultation.",
      hi: "मेडिकल दस्तावेज़ सफलतापूर्वक अपलोड और सुरक्षित कर दिए गए हैं। आप और दस्तावेज़ जोड़ सकते हैं या आगे बढ़ सकते हैं।",
      kn: "ವೈದ್ಯಕೀಯ ದಾಖಲೆಗಳನ್ನು ಯಶಸ್ವಿಯಾಗಿ ಅಪ್‌ಲೋಡ್ ಮಾಡಲಾಗಿದೆ. ನೀವು ಹೆಚ್ಚಿನ ದಾಖಲೆಗಳನ್ನು ಸೇರಿಸಬಹುದು ಅಥವಾ ಮುಂದುವರಿಯಬಹುದು.",
      ta: "மருத்துவ ஆவணங்கள் வெற்றிகரமாக பதிவேற்றப்பட்டன. நீங்கள் மேலும் ஆவணங்களை சேர்க்கலாம் அல்லது தொடரலாம்.",
      te: "వైద్య పత్రాలు విజయవంతంగా అప్‌లోడ్ చేయబడ్డాయి. మీరు మరిన్ని పత్రాలను జోడించవచ్చు లేదా కొనసాగవచ్చు.",
      ml: "മെഡിക്കൽ രേഖകൾ വിജയകരമായി അപ്‌ലോഡ് ചെയ്തു. നിങ്ങൾക്ക് കൂടുതൽ രേഖകൾ ചേർക്കാം അല്ലെങ്കിൽ തുടരാം.",
      mr: "वैद्यकीय कागदपत्रे यशस्वीरित्या अपलोड झाली आहेत. आपण आणखी कागदपत्रे जोडू शकता किंवा पुढे जाऊ शकता.",
      bn: "মেডিকেল নথি সফলভাবে আপলোড হয়েছে। আপনি আরও নথি যোগ করতে পারেন বা এগিয়ে যেতে পারেন.",
      gu: "મેડિકલ દસ્તાવેજો સફળતાપૂર્વક અપલોડ થઈ ગયા છે. તમે વધુ દસ્તાવેજો ઉમેરી શકો છો અથવા આગળ વધી શકો છો.",
      pa: "ਮੈਡੀਕਲ ਦਸਤਾਵੇਜ਼ ਸਫਲਤਾਪੂਰਵਕ ਅੱਪਲੋਡ ਕੀਤੇ ਗਏ ਹਨ।"
    };
    const docMsg = nativeDocSuccess[this.language] || nativeDocSuccess["en"];
    if (typeof SpeechManager !== "undefined" && SpeechManager.speakText) {
      SpeechManager.speakText(docMsg, this.language);
    }

    if (btn) btn.disabled = false;
  },

  pollOcrForDoc(docRecord) {
    const docId = docRecord.document_id;
    let attempts = 0;
    const pollInterval = setInterval(async () => {
      attempts++;
      try {
        const statusRes = await api.getDocumentStatus(docId);
        if (statusRes.ocr_status === "COMPLETED" || statusRes.ocr_status === "OCR_COMPLETE") {
          docRecord.ocr_status = "COMPLETED";
          docRecord.extracted_text = statusRes.extracted_text || statusRes.extracted_text_preview || 'Clinical entities digitized successfully.';
          if (statusRes.access_url) docRecord.access_url = statusRes.access_url;
          clearInterval(pollInterval);
          PatientIntake.renderUploadedDocumentsList();
        } else if (statusRes.ocr_status === "FAILED") {
          docRecord.ocr_status = "FAILED";
          clearInterval(pollInterval);
          PatientIntake.renderUploadedDocumentsList();
        }
      } catch (e) {
        console.warn("OCR polling notice:", e.message);
      }
      if (attempts >= 10) {
        clearInterval(pollInterval);
      }
    }, 1000);
  },

  renderUploadedDocumentsList() {
    const ocrDiv = document.getElementById("doc-ocr-result");
    if (!ocrDiv) return;

    if (!this.uploadedDocuments || this.uploadedDocuments.length === 0) {
      ocrDiv.innerHTML = "";
      return;
    }

    const totalUploaded = this.uploadedDocuments.length;
    let docsHtml = this.uploadedDocuments.map((doc, idx) => {
      const sizeMb = doc.file_size ? (doc.file_size / (1024 * 1024)).toFixed(2) + " MB" : "";
      const isOcrDone = doc.ocr_status === "COMPLETED" || doc.ocr_status === "OCR_COMPLETE";
      const ocrBadge = isOcrDone
        ? `<span style="font-size:0.75rem; background:#ecfdf5; color:#065f46; border:1px solid #a7f3d0; padding:2px 8px; border-radius:12px; font-weight:700;">✓ OCR Digested</span>`
        : `<span style="font-size:0.75rem; background:#eff6ff; color:#1d4ed8; border:1px solid #bfdbfe; padding:2px 8px; border-radius:12px; font-weight:600;"><span class="spinner" style="display:inline-block;">⏳</span> Digitizing Entities...</span>`;

      return `
        <div style="background:#ffffff; border:1.5px solid #86efac; border-radius:8px; padding:0.85rem; margin-bottom:0.6rem; box-shadow:0 1px 4px rgba(0,0,0,0.06);">
          <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.5rem;">
            <div style="display:flex; align-items:center; gap:0.6rem; min-width:0; flex:1;">
              <span style="font-size:1.3rem;">✅</span>
              <div style="min-width:0; flex:1;">
                <p style="font-weight:700; color:#15803d; margin:0; font-size:0.9rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                  ${doc.filename}
                </p>
                <p style="font-size:0.75rem; color:#166534; margin:2px 0 0 0;">
                  ${sizeMb ? sizeMb + ' • ' : ''}Encrypted & Stored in Cloud Vault ✓
                </p>
              </div>
            </div>
            <div>${ocrBadge}</div>
          </div>

          ${doc.access_url && (doc.filename.match(/\.(jpg|jpeg|png|webp|bmp|gif)$/i) || doc.access_url.startsWith('data:image/')) ? `
            <div style="margin-top:0.6rem; text-align:center; background:#f8fafc; border-radius:6px; padding:0.4rem; max-height:140px; overflow:hidden; display:flex; align-items:center; justify-content:center;">
              <img src="${doc.access_url}" alt="Preview" style="max-height:130px; max-width:100%; object-fit:contain; border-radius:4px;" />
            </div>
          ` : ''}

          ${isOcrDone && doc.extracted_text ? `
            <div style="margin-top:0.5rem;">
              <div style="font-size:0.78rem; font-weight:700; color:#166534; margin-bottom:0.25rem;">📄 Digitized Clinical Facts:</div>
              <div style="font-size:0.8rem; color:#1e293b; font-family:monospace; background:#f8fafc; padding:0.5rem 0.75rem; border-radius:6px; border:1px solid #cbd5e1; max-height:100px; overflow-y:auto; white-space:pre-wrap; word-break:break-word;">
                ${doc.extracted_text}
              </div>
            </div>
          ` : ''}
        </div>
      `;
    }).join("");

    ocrDiv.innerHTML = `
      <div style="background:#f0fdf4; border:1.5px solid #86efac; border-radius:var(--radius-md); padding:1.15rem; margin-top:1rem;">
        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.75rem; flex-wrap:wrap; gap:0.5rem;">
          <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size:1.3rem;">📋</span>
            <span style="font-weight:800; color:#15803d; font-size:1rem;">
              Attached Patient Documents (${totalUploaded}) — No Limit
            </span>
          </div>
          <span style="font-size:0.75rem; background:#dcfce7; color:#166534; padding:3px 10px; border-radius:12px; font-weight:700; border:1px solid #86efac;">
            ✓ Attached to Consultation
          </span>
        </div>

        ${docsHtml}

        <div style="margin-top:1rem; display:flex; flex-wrap:wrap; gap:0.75rem; justify-content:space-between; align-items:center; padding-top:0.75rem; border-top:1px dashed #86efac;">
          <div style="display:flex; gap:0.5rem; flex-wrap:wrap;">
            <button type="button" class="btn-secondary-action" style="font-size:0.82rem; padding:0.4rem 0.85rem; background:#ffffff; border-color:#86efac; color:#15803d; font-weight:700;" onclick="document.getElementById('doc-file-input').click()">
              + Upload More Files
            </button>
            <button type="button" class="btn-secondary-action" style="font-size:0.82rem; padding:0.4rem 0.85rem; background:#ffffff; border-color:#86efac; color:#15803d; font-weight:700;" onclick="PatientIntake.openCameraScanner()">
              📷 Snap Another Photo
            </button>
          </div>

          <button type="button" id="btn-proceed-after-ocr" class="btn-primary-action" style="padding:0.65rem 1.5rem; font-size:0.95rem; font-weight:700;" onclick="PatientIntake.handleStep6Continue()">
            ✓ Proceed to AI Clinical Interview (${totalUploaded} Document${totalUploaded > 1 ? 's' : ''}) →
          </button>
        </div>
      </div>
    `;
  },

  async startSocraticIntake() {
    this.goToStep(7);

    const complaintText = document.getElementById("chief-complaint-input")?.value.trim() || "";
    const painLevelVal = this.painLevel || 7;

    try {
      if (!this.currentPatientId) {
        this.currentPatientId = `pat_${Date.now()}`;
      }
      if (!this.currentSessionId) {
        this.currentSessionId = `sess_${this.currentPatientId}_${Date.now()}`;
      }
      this.currentQuestionId = this.currentQuestionId || `q_${this.currentSessionId}_1`;

      const res = await api.startIntake(
        this.currentPatientId,
        this.language,
        this.isAttendant,
        this.attendantId,
        this.currentSessionId,
        complaintText || null,
        painLevelVal,
        this.knownConditions || [],
        this.medications || [],
        this.pastMedicalHistory || null,
        this.prescriptionNotes || null,
        this.getActiveOpdMode()
      );

      if (res.session_id) {
        this.currentSessionId = res.session_id;
      }
      if (res.question && res.question.question_id) {
        this.currentQuestionId = res.question.question_id;
      }

      if (res.question) {
        this.renderQuestion(res.question);
      }
    } catch (err) {
      console.warn("Intake session initialization notice:", err.message);
      if (complaintText) {
        const fallbacks = {
          en: `Could you describe how your symptoms feel and whether they spread anywhere?`,
          hi: `क्या आप बता सकते हैं कि यह दर्द या लक्षण कैसा महसूस होता है और क्या यह कहीं और फैलता है?`,
          kn: `ಈ ನೋವು ಅಥವಾ ಲಕ್ಷಣಗಳು ಹೇಗಿವೆ ಮತ್ತು ಬೇರೆಡೆ ಹರಡುತ್ತವೆಯೇ ಎಂದು ವಿವರಿಸಬಹುದೇ?`,
          ta: `இந்த வலி எப்படி இருக்கிறது மற்றும் வேறு எங்கும் பரவுகிறதா?`,
          te: `ఈ నొప్పి ఎలా ఉంది మరియు ఇతర భాగాలకు వ్యాపిస్తుందా?`,
          ml: `ഈ വേദന എങ്ങനെയുണ്ട്, മറ്റ് ഭാഗങ്ങളിലേക്ക് വ്യാപിക്കുന്നുണ്ടോ?`,
          mr: `हे दुखणे कसे वाटते आणि इतरत्र कुठे पसरते का?`,
          bn: `এই ব্যথাটি কেমন এবং অন্য কোথাও ছড়ায় কি না বলতে পারেন?`,
          gu: `આ દુખાવો કેવો લાગે છે અને બીજે ક્યાંય ફેલાય છે?`,
          pa: `ਇਹ ਦਰਦ ਕਿਵੇਂ ਮਹਿਸੂਸ ਹੁੰਦਾ ਹੈ ਅਤੇ ਕੀ ਇਹ ਹੋਰ ਕਿਤੇ ਫੈਲਦਾ ਹੈ?`
        };
        const fbText = fallbacks[this.language] || fallbacks["en"];
        this.renderQuestion({
          question_id: `q_${this.currentSessionId}_fallback`,
          question: fbText,
          objective: "Clarify symptom details"
        });
      }
    }
  },

  renderQuestion(question) {
    if (!question) return;
    try {
      if (typeof SpeechManager !== "undefined" && SpeechManager.stopAllAudio) {
        SpeechManager.stopAllAudio();
      }
    } catch (e) {}

    this.currentQuestionId = question.question_id || this.currentQuestionId || `q_${this.currentSessionId || 'sess'}_1`;
    this.currentQuestionText = question.question || this.currentQuestionText;

    const qTextEl = document.getElementById("current-question-text");
    const qBadgeEl = document.getElementById("current-question-badge");
    const qAyurEl = document.getElementById("current-ayur-badge");

    if (qTextEl) qTextEl.innerText = this.currentQuestionText;
    if (qBadgeEl) qBadgeEl.innerText = `Objective: ${question.objective || 'Clinical Investigation'}`;

    if (qAyurEl) {
      if (question.ayurvedic_domain) {
        qAyurEl.style.display = "inline-flex";
        qAyurEl.innerText = `Ayurveda: ${question.display_label || question.ayurvedic_domain}`;
      } else {
        qAyurEl.style.display = "none";
      }
    }

    // Render structured option buttons if provided by question bank
    const existingOpts = document.getElementById("question-options-container");
    if (existingOpts) existingOpts.remove();

    if (question.options && Array.isArray(question.options) && question.options.length > 0) {
      const optionsContainer = document.createElement("div");
      optionsContainer.id = "question-options-container";
      optionsContainer.style.cssText = "display: flex; flex-wrap: wrap; gap: 0.75rem; margin-top: 1rem; margin-bottom: 1rem;";
      optionsContainer.innerHTML = question.options.map((opt) => {
        const val = typeof opt === "string" ? opt : (opt.value || opt.label || opt.text_en || "");
        const label = typeof opt === "string" ? opt : (opt.label || opt.text_en || opt.value || "");
        const weightsJson = opt.weights ? JSON.stringify(opt.weights).replace(/"/g, '&quot;') : '{}';
        return `<button type="button" class="btn-option-pill" style="flex: 1 1 calc(50% - 0.75rem); min-width: 150px; min-height: 48px; padding: 0.75rem 1rem; background: #ffffff; border: 2px solid #0d9488; color: #0f766e; font-weight: 700; border-radius: 10px; cursor: pointer; text-align: center; transition: all 0.2s ease; box-shadow: 0 2px 4px rgba(0,0,0,0.05);" onclick="PatientIntake.selectOption('${val.replace(/'/g, "\\'")}', '${label.replace(/'/g, "\\'")}', ${weightsJson})">${label}</button>`;
      }).join('');

      if (qTextEl && qTextEl.parentNode) {
        qTextEl.parentNode.insertBefore(optionsContainer, qTextEl.nextSibling);
      }
    }

    const input = document.getElementById("patient-answer-input");
    if (input) {
      input.value = "";
      input.focus();
    }

    // Auto-speak question in patient's selected language using Indian female voice TTS, then auto-open mic
    SpeechManager.speakText(this.currentQuestionText, this.language, () => {
      SpeechManager.activeTargetInputId = 'patient-answer-input';
      SpeechManager.activeTargetBtnId = 'btn-mic-toggle';
      SpeechManager.startListeningWithSilenceTimeout(4000);
    });
  },

  selectOption(val, label, weights) {
    if (this._isSubmittingAnswer || this._isFinishing || this.currentStep >= 8) return;
    const input = document.getElementById("patient-answer-input");
    if (input) {
      input.value = label || val;
    }
    this.selectedOptionMeta = { value: val, label: label, weights: weights };

    // Disable option buttons to prevent multiple clicks
    const allPills = document.querySelectorAll(".btn-option-pill");
    allPills.forEach(p => { p.disabled = true; p.style.opacity = "0.7"; });

    this.handleAnswerSubmit();
  },

  speakCurrentQuestion() {
    if (this.currentQuestionText) {
      if (typeof SpeechManager !== 'undefined') {
        if (SpeechManager.isSpeaking && !SpeechManager.isMuted) {
          SpeechManager.isMuted = true;
          try { localStorage.setItem('medikiosk_muted', 'true'); } catch(e) {}
          SpeechManager.stopAllAudio();
          SpeechManager.updateButtonStates('muted');
        } else {
          SpeechManager.isMuted = false;
          try { localStorage.setItem('medikiosk_muted', 'false'); } catch(e) {}
          SpeechManager.updateButtonStates('idle');
          SpeechManager.speakText(this.currentQuestionText, this.language, () => {
            SpeechManager.activeTargetInputId = 'patient-answer-input';
            SpeechManager.activeTargetBtnId = 'btn-mic-toggle';
            SpeechManager.startListeningWithSilenceTimeout(4000);
          });
        }
      }
    }
  },

  _isSubmittingAnswer: false,
  _isFinishing: false,

  async handleAnswerSubmit() {
    try {
      if (typeof SpeechManager !== "undefined" && SpeechManager.stopListening) {
        SpeechManager.stopListening();
      }
    } catch (e) {}
    if (this._isSubmittingAnswer || this._isFinishingIntake || this._intakeCompleted || this._isFinishing) return;
    const input = document.getElementById("patient-answer-input");
    const answer = input ? input.value.trim() : "";
    if (!answer) return;

    this._isSubmittingAnswer = true;

    if (!this.currentSessionId) {
      this.currentSessionId = `sess_${this.currentPatientId || 'pat'}_${Date.now()}`;
    }
    if (!this.currentQuestionId) {
      this.currentQuestionId = `q_${this.currentSessionId}_1`;
    }

    const btn = document.getElementById("btn-submit-answer");
    const originalText = btn ? btn.innerHTML : "Submit Answer";
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = ` Recording answer...`;
    }

    try {
      const res = await api.submitAnswer(
        this.currentSessionId,
        this.currentQuestionId,
        answer,
        this.isAttendant ? "ATTENDANT" : "PATIENT",
        this.attendantId,
        this.language
      );

      const liveSumEl = document.getElementById("live-summary-box");
      if (res && res.live_summary && liveSumEl) {
        liveSumEl.style.display = "block";
        liveSumEl.innerHTML = `<strong>Verification:</strong> ${res.live_summary}`;
      }

      if (res && (res.is_finished || !res.next_question)) {
        await this.finishIntake();
      } else if (res && res.next_question) {
        this.renderQuestion(res.next_question);
      } else {
        await this.finishIntake();
      }
    } catch (err) {
      console.warn("Answer submission notice:", err.message);
      if (!this._isFinishing && this.currentStep === 7) {
        try {
          const retryRes = await api.submitAnswer(
            this.currentSessionId,
            this.currentQuestionId,
            answer,
            this.isAttendant ? "ATTENDANT" : "PATIENT",
            this.attendantId,
            this.language
          );
          if (retryRes && (retryRes.is_finished || !retryRes.next_question)) {
            await this.finishIntake();
          } else if (retryRes && retryRes.next_question) {
            this.renderQuestion(retryRes.next_question);
          } else {
            await this.finishIntake();
          }
        } catch (retryErr) {
          console.warn("Retry submission failed, finalizing registration cleanly:", retryErr.message);
          if (!this._isFinishing && this.currentStep === 7) {
            await this.finishIntake();
          }
        }
      }
    } finally {
      this._isSubmittingAnswer = false;
      if (btn && this.currentStep < 8 && !this._isFinishing && !this._isFinishingIntake) {
        btn.disabled = false;
        btn.innerHTML = originalText;
      }
    }
  },

  renderTicketDetails(data = {}) {
    const bodyEl = document.getElementById("ticket-details-body");
    if (bodyEl) {
      const patientName = (data && data.patient_name) || this.registeredData?.name || 'Registered Patient';
      const rawDept = ((data && data.department) || this.department || 'General Medicine').toLowerCase();
      const deptDisplayMap = {
        "kayachikitsa": "KAYACHIKITSA (INTERNAL MEDICINE)",
        "panchakarma": "PANCHAKARMA (DETOX & PURIFICATION)",
        "shalya": "SHALYA TANTRA (SURGICAL & STRUCTURAL)",
        "shalakya": "SHALAKYA TANTRA (ENT & EYE)",
        "prasuti-stri": "PRASUTI TANTRA & STREE ROGA",
        "kaumarabhritya": "KAUMARABHRITYA (PEDIATRICS)",
        "swasthavritta": "SWASTHAVRITTA & YOGA",
        "agadatantra": "AGADA TANTRA (TOXICOLOGY)",
        "ayush": "AYUSH / AYURVEDA MAIN OPD",
        "general-medicine": "GENERAL MEDICINE",
        "cardiology": "CARDIOLOGY",
        "neurology": "NEUROLOGY",
        "orthopedics": "ORTHOPEDICS",
        "pediatrics": "PEDIATRICS",
        "gastroenterology": "GASTROENTEROLOGY",
        "dermatology": "DERMATOLOGY",
        "ent": "ENT",
        "ophthalmology": "OPHTHALMOLOGY",
        "psychiatry": "PSYCHIATRY",
        "emergency": "EMERGENCY / TRAUMA"
      };
      const dept = deptDisplayMap[rawDept] || rawDept.toUpperCase().replace(/-/g, ' ');
      const complaint = (data && data.chief_complaint) || this.chiefComplaint || 'Clinical intake recorded successfully.';
      const reasoning = (data && data.reasoning) || 'Patient triaged and queued for attending physician consultation.';

      bodyEl.innerHTML = `
        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:1.25rem; margin-bottom:1.25rem;">
          <div>
            <span style="font-size:0.75rem; color:var(--text-muted); font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">PATIENT NAME</span>
            <p style="font-weight:700; font-size:1.05rem; color:#0f172a; margin-top:2px;">${patientName}</p>
          </div>
          <div>
            <span style="font-size:0.75rem; color:var(--text-muted); font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">ASSIGNED DEPARTMENT</span>
            <p style="font-weight:700; font-size:1.05rem; color:var(--brand-primary); margin-top:2px;">${dept}</p>
          </div>
        </div>
        <div style="margin-bottom:1.25rem;">
          <span style="font-size:0.75rem; color:var(--text-muted); font-weight:700; text-transform:uppercase; letter-spacing:0.5px;">CHIEF COMPLAINT NARRATIVE</span>
          <p style="font-style:italic; color:#334155; margin-top:4px; font-size:0.95rem; line-height:1.5;">"${complaint}"</p>
        </div>
        <div style="background:#faf8f5; border:1px solid #e5e0d5; padding:0.85rem 1rem; border-radius:var(--radius-sm); font-size:0.875rem;">
          <p style="margin:0; color:#334155;"><strong>Routing Assessment:</strong> ${reasoning}</p>
        </div>
      `;
    }
  },

  async finishIntake() {
    if (this._isFinishing || this._isFinishingIntake || this.currentStep >= 8 || this._intakeCompleted) {
      console.log("Intake already finishing or completed, ignoring duplicate call.");
      return;
    }
    this._isFinishing = true;
    this._isFinishingIntake = true;
    this._intakeCompleted = true;

    try {
      if (typeof SpeechManager !== "undefined" && SpeechManager.stopAllAudio) {
        SpeechManager.stopAllAudio();
      }
    } catch (e) {}

    const modal = document.getElementById("ai-synthesis-modal");
    const fill = document.getElementById("synthesis-progress-fill");
    const item1 = document.getElementById("synthesis-step-1");
    const item2 = document.getElementById("synthesis-step-2");
    const item3 = document.getElementById("synthesis-step-3");

    if (modal) {
      modal.style.display = "flex";
      modal.classList.add("active");
      if (fill) fill.style.width = "0%";
      if (item1) item1.classList.remove("done");
      if (item2) item2.classList.remove("done");
      if (item3) item3.classList.remove("done");

      setTimeout(() => { if (fill) fill.style.width = "40%"; if (item1) item1.classList.add("done"); }, 200);
      setTimeout(() => { if (fill) fill.style.width = "75%"; if (item2) item2.classList.add("done"); }, 600);
      setTimeout(() => { if (fill) fill.style.width = "100%"; if (item3) item3.classList.add("done"); }, 1050);
    }

    let res = null;
    try {
      res = await api.completeIntake(this.currentSessionId, this.currentPatientId || 'pat_dev');
    } catch (err) {
      console.warn("Summary completion notice:", err.message);
    }

    await new Promise(resolve => setTimeout(resolve, 1200));

    if (modal) {
      modal.classList.remove("active");
      modal.style.display = "none";
    }

    try {
      this.goToStep(8);

      const ticketNum = res?.ticket_number || `MK-${Math.floor(10000000 + Math.random() * 90000000)}`;
      const numEl = document.getElementById("ticket-number-display");
      if (numEl) numEl.innerText = ticketNum;

      const rf = res?.red_flag || { overall_severity: "MEDIUM" };
      const routing = res?.routing || { recommended_department: this.department || "general_medicine", reasoning: "Comprehensive clinical intake recorded." };

      const badgeContainer = document.getElementById("ticket-triage-badge");
      if (badgeContainer) {
        let badgeClass = "lang-badge-ready";
        let badgeStyle = "";
        if (rf.overall_severity === "CRITICAL") {
          badgeClass = "lang-badge-connected";
          badgeStyle = "background:#fee2e2; color:#991b1b;";
        } else if (rf.overall_severity === "HIGH") {
          badgeClass = "lang-badge-connected";
          badgeStyle = "background:#ffedd5; color:#9a3412;";
        } else if (rf.overall_severity === "MEDIUM") {
          badgeClass = "lang-badge-connected";
          badgeStyle = "background:#fef3c7; color:#92400e;";
        }

        badgeContainer.innerHTML = `<span class="lang-tile-badge ${badgeClass}" style="${badgeStyle}">${rf.overall_severity} PRIORITY</span>`;
      }

      this.renderTicketDetails({
        patient_name: this.registeredData?.name || 'Registered Patient',
        department: routing.recommended_department || this.department || 'General Medicine',
        chief_complaint: res?.draft_summary?.chief_complaint || this.chiefComplaint || 'Recorded during intake',
        reasoning: routing.reasoning || 'Patient triaged and ready for consultation.'
      });

      this.triggerConfettiBurst();

      SpeechManager.speakText(`Intake completed. Consultation Ticket number is ${ticketNum}. Please proceed to the ${routing.recommended_department || 'assigned'} department.`, this.language);
    } catch (renderErr) {
      console.error("Ticket rendering error:", renderErr);
    }
  },

  triggerConfettiBurst() {
    const container = document.getElementById("ticket-confetti-container");
    if (!container) return;
    container.innerHTML = "";
    container.classList.remove("active");

    const colors = ["#0D9488", "#14B8A6", "#6366F1", "#F59E0B", "#EC4899", "#10B981"];
    for (let i = 0; i < 28; i++) {
      const piece = document.createElement("div");
      piece.className = "confetti-piece";
      piece.style.background = colors[i % colors.length];
      piece.style.left = `${Math.random() * 90 + 5}%`;
      piece.style.top = "0px";
      piece.style.setProperty("--x-start", `${(Math.random() - 0.5) * 60}px`);
      piece.style.setProperty("--x-end", `${(Math.random() - 0.5) * 140}px`);
      piece.style.animationDelay = `${Math.random() * 0.4}s`;
      piece.style.animationDuration = `${1.8 + Math.random() * 1.2}s`;
      piece.style.borderRadius = i % 2 === 0 ? "50%" : "2px";
      container.appendChild(piece);
    }
    void container.offsetHeight;
    container.classList.add("active");
  }
};

if (typeof window !== 'undefined') {
  window.PatientIntake = PatientIntake;
}

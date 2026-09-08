const PatientIntake = {
  currentStep: 1,
  currentSessionId: null,
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

    // 2. IMMEDIATE WELCOMING AUTO-SPEECH
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
    });
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

    // Toggle wizard steps display
    for (let i = 1; i <= 8; i++) {
      const el = document.getElementById(`kiosk-step-${i}`);
      if (el) {
        el.style.display = i === stepNum ? "block" : "none";
      }
    }
    this.currentStep = stepNum;

    try {
      this.updateStepIndicator(stepNum);
    } catch (e) {
      console.warn("Step indicator notice:", e);
    }

    try {
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {}

    // Step 2: Refresh language grid UI and continue button
    if (stepNum === 2) {
      try {
        this.updateLanguageGridUI(this.language);
        this.updateStep2ContinueBtn(this.language);
      } catch (e) {
        console.warn("Step 2 UI update notice:", e);
      }
      setTimeout(() => {
        try {
          if (typeof SpeechManager !== "undefined" && SpeechManager.resumeAudioAndSpeak) {
            SpeechManager.resumeAudioAndSpeak(2, this.language);
          }
        } catch (e) {}
      }, 300);
      return;
    }

    // Step 7: Socratic Intake Interview
    if (stepNum === 7) {
      if (!this.currentSessionId) {
        this.currentSessionId = `sess_${this.currentPatientId || 'pat'}_${Date.now()}`;
      }
      this.currentQuestionId = this.currentQuestionId || `q_${this.currentSessionId}_1`;
      const qTextEl = document.getElementById("current-question-text");
      if (qTextEl && !this.currentQuestionText) {
        qTextEl.innerText = "Preparing clinical inquiry...";
      }
    } else {
      setTimeout(() => {
        try {
          if (typeof SpeechManager !== "undefined" && SpeechManager.resumeAudioAndSpeak) {
            SpeechManager.resumeAudioAndSpeak(stepNum, this.language);
          }
        } catch (e) {}
      }, 350);
    }
  },

  updateStepIndicator(stepNum) {
    for (let i = 1; i <= 8; i++) {
      const node = document.getElementById(`step-node-${i}`);
      const line = document.getElementById(`step-line-${i}`);
      if (node) {
        node.className = "wizard-step-node";
        if (i < stepNum || (i === 8 && stepNum === 8)) {
          node.classList.add("completed");
          node.innerHTML = "✓";
        } else if (i === stepNum) {
          node.classList.add("active");
          node.innerHTML = i;
        } else {
          node.innerHTML = i;
        }
      }
      if (line) {
        line.className = "wizard-step-line" + (i <= stepNum ? " completed" : "");
      }
    }
  },

  acceptConsent() {
    this.consentAccepted = true;
    const chk = document.getElementById("consent-checkbox");
    if (chk) chk.checked = true;
    this.goToStep(4);
  },

  updateLanguageGridUI(lang) {
    document.querySelectorAll(".lang-tile, .lang-tile-card").forEach((tile) => {
      const tileLang = tile.getAttribute("data-lang");
      const badge = tile.querySelector(".lang-tile-badge, .lang-status-pill");
      const check = tile.querySelector(".lang-check-badge");
      if (tileLang === lang) {
        tile.classList.add("selected");
        if (check) check.style.display = "inline-flex";
        if (badge) {
          badge.className = "lang-status-pill pill-connected";
          badge.innerText = "FULLY CONNECTED";
        }
      } else {
        tile.classList.remove("selected");
        if (check) check.style.display = "none";
        if (badge) {
          if (tileLang === "hi") {
            badge.className = "lang-status-pill pill-ready";
            badge.innerText = "TRANSLATION READY";
          } else {
            badge.className = "lang-status-pill pill-fallback";
            badge.innerText = "TEXT FALLBACK";
          }
        }
      }
    });
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
      alert("⚠️ Please check the agreement box to confirm your consent before proceeding.");
      return;
    }
    this.goToStep(4);
  },

  async handleRegistration(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;

    try {
      const name = document.getElementById("reg-name").value.trim();
      const age = parseInt(document.getElementById("reg-age").value, 10);
      const gender = document.getElementById("reg-gender").value;
      const phone = document.getElementById("reg-phone").value.trim();
      const abhaId = document.getElementById("reg-abha").value.trim();
      this.isAttendant = document.getElementById("is-attendant-assisted").checked;

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

      const patient = await api.registerPatient(regData);
      this.currentPatientId = patient.patient_id;
      this.currentSessionId = `sess_${patient.patient_id}_${Date.now()}`;
      this.registeredData = { name, age, gender, phone, abhaId };

      if (this.isAttendant) {
        const attName = document.getElementById("att-name").value.trim();
        const attPhone = document.getElementById("att-phone").value.trim();
        const attRel = document.getElementById("att-rel").value;
        const attRes = await api.registerAttendant(this.currentPatientId, {
          name: attName,
          phone: attPhone,
          relationship_to_patient: attRel
        });
        this.attendantId = attRes.attendant.attendant_id;
      }

      // Submit ABDM Consent
      await api.submitConsent(this.currentPatientId, this.currentSessionId, this.isAttendant, this.attendantId);

      this.goToStep(5);
    } catch (err) {
      alert("Registration error: " + err.message);
    } finally {
      btn.disabled = false;
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

  selectPainLevel(level) {
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
    if (!input || !input.files || !input.files[0]) return;
    const file = input.files[0];
    const previewContainer = document.getElementById("doc-file-selected-preview");
    if (!previewContainer) return;

    const isImage = file.type.startsWith("image/");
    const localUrl = isImage ? URL.createObjectURL(file) : "";
    const sizeMb = (file.size / (1024 * 1024)).toFixed(2);

    previewContainer.style.display = "block";
    previewContainer.innerHTML = `
      <div style="background:#eff6ff; border:1.5px solid #93c5fd; border-radius:8px; padding:0.85rem; margin-top:0.75rem;">
        <div style="display:flex; align-items:center; gap:0.85rem;">
          ${isImage ? `<img src="${localUrl}" style="width:65px; height:65px; object-fit:cover; border-radius:6px; border:1px solid #60a5fa; box-shadow:0 2px 6px rgba(0,0,0,0.15);" />` : `<div style="width:65px; height:65px; background:#dbeafe; border-radius:6px; display:flex; align-items:center; justify-content:center; font-size:2rem; color:#1d4ed8;">📄</div>`}
          <div style="flex:1; overflow:hidden;">
            <p style="font-weight:700; color:#1e40af; margin:0; font-size:0.9rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">📄 ${file.name}</p>
            <p style="font-size:0.8rem; color:#2563eb; margin:0.25rem 0 0 0;">Size: ${sizeMb} MB • Ready for Cloud Encryption & OCR Analysis</p>
          </div>
        </div>
        ${isImage ? `
          <div style="margin-top:0.6rem; text-align:center;">
            <img src="${localUrl}" style="max-width:100%; max-height:180px; border-radius:6px; border:1px solid #bfdbfe; object-fit:contain;" />
          </div>
        ` : ''}
      </div>
    `;
  },

  toggleFullOcrText() {
    const el = document.getElementById("full-ocr-text-container");
    const label = document.getElementById("btn-toggle-ocr-text-label");
    if (!el) return;
    const isExpanded = el.style.maxHeight === "none" || el.style.maxHeight === "1000px";
    if (isExpanded) {
      el.style.maxHeight = "160px";
      if (label) label.innerText = "📖 Show Full Extracted Text ▼";
    } else {
      el.style.maxHeight = "none";
      if (label) label.innerText = "▲ Collapse Text";
    }
  },

  cameraStream: null,
  capturedCameraFile: null,

  triggerCameraCapture() {
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || window.innerWidth <= 768;
    if (isMobile) {
      const camInput = document.getElementById("doc-camera-input");
      if (camInput) {
        camInput.click();
        return;
      }
    }
    this.openCameraModal();
  },

  async openCameraModal() {
    const modal = document.getElementById("camera-capture-modal");
    const video = document.getElementById("camera-video-feed");
    if (!modal || !video) return;

    modal.style.display = "flex";

    try {
      if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 } }
        });
        this.cameraStream = stream;
        video.srcObject = stream;
      } else {
        const camInput = document.getElementById("doc-camera-input");
        if (camInput) camInput.click();
      }
    } catch (err) {
      console.warn("Camera access error:", err);
      this.closeCameraModal();
      const camInput = document.getElementById("doc-camera-input");
      if (camInput) camInput.click();
    }
  },

  closeCameraModal() {
    if (this.cameraStream) {
      try {
        this.cameraStream.getTracks().forEach(track => track.stop());
      } catch (e) {}
      this.cameraStream = null;
    }
    const modal = document.getElementById("camera-capture-modal");
    if (modal) modal.style.display = "none";
  },

  capturePhotoFromWebcam() {
    const video = document.getElementById("camera-video-feed");
    const canvas = document.getElementById("camera-canvas");
    if (!video || !canvas) return;

    const width = video.videoWidth || 640;
    const height = video.videoHeight || 480;

    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, width, height);

    canvas.toBlob((blob) => {
      if (!blob) return;
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
    }, "image/jpeg", 0.92);
  },

  async handleDocUpload(e) {
    e.preventDefault();
    const fileInput = document.getElementById("doc-file-input");
    const file = (fileInput && fileInput.files && fileInput.files.length) ? fileInput.files[0] : this.capturedCameraFile;
    if (!file) {
      this.startSocraticIntake();
      return;
    }

    const btn = document.getElementById("btn-upload-doc");
    btn.disabled = true;
    btn.innerText = "1/3 Uploading & Storing Document...";

    const ocrDiv = document.getElementById("doc-ocr-result");
    if (ocrDiv) {
      ocrDiv.innerHTML = `
        <div style="background:#f8fafc; border:1.5px solid #cbd5e1; border-radius:var(--radius-md); padding:1rem; margin-top:1rem;">
          <div style="display:flex; align-items:center; gap:8px;">
            <span class="spinner" style="display:inline-block;">⏳</span>
            <p style="font-weight:600; color:#334155; font-size:0.95rem;">Uploading to secure cloud vault...</p>
          </div>
        </div>
      `;
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
      
      // Document is securely stored in cloud and metadata recorded (<400ms)
      if (ocrDiv) {
        ocrDiv.innerHTML = `
          <div style="background:#f0fdf4; border:1.5px solid #86efac; border-radius:var(--radius-md); padding:1.15rem; margin-top:1rem;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-size:1.3rem;">✅</span>
              <p style="font-weight:700; color:#15803d; font-size:1rem;">Document Encrypted & Stored ✓</p>
            </div>
            <p style="font-size:0.85rem; color:#166534; margin-top:0.35rem;">
              Your document is securely attached to your clinical consultation record.
            </p>
            <div id="ocr-polling-status" style="font-size:0.8rem; color:#475569; margin-top:0.5rem;">
              <div style="display:flex; align-items:center; gap:6px;">
                <span class="spinner">⏳</span> Digitizing laboratory values and clinical entities in background...
              </div>
            </div>
          </div>
        `;
      }

      // Non-blocking status polling with 800ms intervals
      const docId = res.document_id;
      let attempts = 0;
      const pollOcr = async () => {
        attempts++;
        try {
          const statusRes = await api.getDocumentStatus(docId);
          if (statusRes.ocr_status === "COMPLETED" || statusRes.ocr_status === "OCR_COMPLETE") {
            const pollStatusEl = document.getElementById("ocr-polling-status");
            if (pollStatusEl) {
              const fullText = statusRes.extracted_text || statusRes.extracted_text_preview || 'Clinical entities digitized successfully.';
              const activeViewUrl = statusRes.access_url || docPreviewUrl;
              pollStatusEl.innerHTML = `
                <div style="width:100%; margin-top:0.5rem;">
                  <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:0.5rem; flex-wrap:wrap; gap:0.5rem;">
                    <span style="color:#15803d; font-weight:700; font-size:0.9rem;">✓ OCR Digitization Complete</span>
                    <button type="button" onclick="PatientIntake.toggleFullOcrText()" style="background:#e0f2fe; color:#0369a1; border:1px solid #7dd3fc; padding:4px 10px; border-radius:6px; font-size:0.8rem; font-weight:700; cursor:pointer;">
                      <span id="btn-toggle-ocr-text-label">📖 Show Full Extracted Text ▼</span>
                    </button>
                  </div>

                  ${activeViewUrl ? `
                    <div style="margin-bottom:0.75rem; text-align:center; background:white; border:1px solid #bbf7d0; border-radius:8px; padding:0.6rem; max-height:240px; overflow:hidden; display:flex; align-items:center; justify-content:center;">
                      <img src="${activeViewUrl}" alt="Document Scan Preview" style="max-width:100%; max-height:220px; border-radius:6px; object-fit:contain; box-shadow:0 2px 10px rgba(0,0,0,0.12);" />
                    </div>
                  ` : ''}

                  <div style="font-weight:700; font-size:0.8rem; color:#166534; margin-bottom:0.35rem;">
                    📄 Extracted Clinical Content:
                  </div>
                  <div id="full-ocr-text-container" style="font-size:0.85rem; color:#1e293b; font-family:monospace; background:white; padding:0.85rem 1rem; border-radius:8px; border:1px solid #bbf7d0; max-height:160px; overflow-y:auto; white-space:pre-wrap; word-break:break-word; transition:all 0.3s ease; box-shadow:inset 0 1px 3px rgba(0,0,0,0.05);">
                    ${fullText}
                  </div>
                </div>
              `;
            }
            return true;
          } else if (statusRes.ocr_status === "FAILED") {
            const pollStatusEl = document.getElementById("ocr-polling-status");
            if (pollStatusEl) {
              pollStatusEl.innerHTML = `<span style="color:#64748b;">(Original document safely attached for physician review)</span>`;
            }
            return true;
          }
        } catch (e) {
          console.warn("OCR polling notice:", e.message);
        }
        return false;
      };

      // Speak native confirmation
      const nativeDocSuccess = {
        en: "Medical report uploaded and stored successfully. Proceeding to consultation.",
        hi: "मेडिकल रिपोर्ट सफलतापूर्वक अपलोड और सुरक्षित कर दी गई है।",
        kn: "ವೈದ್ಯಕೀಯ ವರದಿ ಯಶಸ್ವಿಯಾಗಿ ಅಪ್‌ಲೋಡ್ ಆಗಿದೆ.",
        ta: "மருத்துவ அறிக்கை வெற்றிகரமாக பதிவேற்றப்பட்டது.",
        te: "వైద్య నివేదిక విజయవంతంగా అప్‌లోడ్ చేయబడింది.",
        ml: "മെഡിക്കൽ റിപ്പോർട്ട് വിജയകരമായി അപ്‌ಲೋഡ് ചെയ്തു.",
        mr: "वैद्यकीय अहवाल यशस्वीरित्या अपलोड झाला आहे.",
        bn: "মেডিকেল রিপোর্ট সফলভাবে আপলোড হয়েছে।",
        gu: "મેડિકલ રિપોર્ટ સફળતાપૂર્વક અપલોડ થઈ ગયો છે.",
        pa: "ਮੈਡੀਕਲ ਰਿਪੋਰਟ ਸਫਲਤਾਪੂਰਵਕ ਅੱਪਲੋਡ ਹੋ ਗਈ ਹੈ।"
      };
      const docMsg = nativeDocSuccess[this.language] || nativeDocSuccess["en"];
      SpeechManager.speakText(docMsg, this.language);

      // Background poll in parallel — do NOT auto-advance, wait for Proceed button
      const pollInterval = setInterval(async () => {
        const done = await pollOcr();
        if (done || attempts >= 8) {
          clearInterval(pollInterval);
        }
      }, 800);

      // Show Proceed button inside the OCR result area (NO auto-advance)
      btn.style.display = "none";
      const proceedDiv = document.createElement('div');
      proceedDiv.style.cssText = 'margin-top:1rem; text-align:center;';
      proceedDiv.innerHTML = `
        <button type="button" id="btn-proceed-after-ocr" class="btn-primary-action" style="padding:0.75rem 2rem; font-size:1rem; font-weight:700;" onclick="PatientIntake.handleStep6Continue()">
          ✓ Proceed to AI Clinical Interview →
        </button>
      `;
      const ocrParent = document.getElementById('doc-ocr-result');
      if (ocrParent) ocrParent.appendChild(proceedDiv);

    } catch (err) {
      console.warn("Document upload error:", err.message);
      const ocrDiv = document.getElementById("doc-ocr-result");
      if (ocrDiv) {
        ocrDiv.innerHTML = `
          <div style="background:#fef2f2; border:1px solid #fca5a5; border-radius:var(--radius-md); padding:1rem; margin-top:1rem;">
            <p style="font-weight:700; color:#991b1b;">⚠️ Upload Notice</p>
            <p style="font-size:0.85rem; color:#7f1d1d; margin-top:0.25rem;">We could not upload this file, but you can continue with your voice consultation.</p>
            <button type="button" class="btn-primary-action" style="margin-top:0.75rem; padding:0.6rem 1.5rem;" onclick="PatientIntake.handleStep6Continue()">
              Proceed to Interview →
            </button>
          </div>
        `;
      }
    } finally {
      btn.disabled = false;
    }
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
    const input = document.getElementById("patient-answer-input");
    if (input) {
      input.value = label || val;
    }
    this.selectedOptionMeta = { value: val, label: label, weights: weights };
    this.handleAnswerSubmit();
  },

  speakCurrentQuestion() {
    if (this.currentQuestionText) {
      SpeechManager.speakText(this.currentQuestionText, this.language, () => {
        SpeechManager.activeTargetInputId = 'patient-answer-input';
        SpeechManager.activeTargetBtnId = 'btn-mic-toggle';
        SpeechManager.startListeningWithSilenceTimeout(4000);
      });
    }
  },

  async handleAnswerSubmit() {
    SpeechManager.stopListening();
    const input = document.getElementById("patient-answer-input");
    const answer = input ? input.value.trim() : "";
    if (!answer) return;

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
      btn.innerHTML = `<span style="margin-right:6px;">⏳</span> Recording answer...`;
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
      // Auto-retry once in case of serverless wake-up
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
        }
      } catch (retryErr) {
        alert("⚠️ Please tap Submit Answer once more to proceed.");
      }
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerHTML = originalText;
      }
    }
  },

  renderTicketDetails(data = {}) {
    const bodyEl = document.getElementById("ticket-details-body");
    if (bodyEl) {
      const rawDept = (data.department || this.department || 'General Medicine').toLowerCase();
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
      const complaint = data.chief_complaint || this.chiefComplaint || 'Clinical intake recorded successfully.';
      const reasoning = data.reasoning || 'Patient triaged and queued for attending physician consultation.';

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
    this.goToStep(8);
    this.renderTicketDetails();

    try {
      const res = await api.completeIntake(this.currentSessionId, this.currentPatientId || 'pat_dev');
      const ticketNum = res?.ticket_number || `MK-${Math.floor(10000000 + Math.random() * 90000000)}`;
      
      const numEl = document.getElementById("ticket-number-display");
      if (numEl) numEl.innerText = ticketNum;

      const rf = res?.red_flag || { overall_severity: "MEDIUM" };
      const routing = res?.routing || { recommended_department: this.department || "general_medicine", reasoning: "Comprehensive clinical intake recorded." };

      const badgeContainer = document.getElementById("ticket-triage-badge");
      if (badgeContainer) {
        let badgeClass = "lang-badge-ready";
        if (rf.overall_severity === "CRITICAL") badgeClass = "lang-badge-connected' style='background:#fee2e2; color:#991b1b;";
        else if (rf.overall_severity === "HIGH") badgeClass = "lang-badge-connected' style='background:#ffedd5; color:#9a3412;";
        else if (rf.overall_severity === "MEDIUM") badgeClass = "lang-badge-connected' style='background:#fef3c7; color:#92400e;";

        badgeContainer.innerHTML = `<span class="lang-tile-badge ${badgeClass}">${rf.overall_severity} PRIORITY</span>`;
      }

      this.renderTicketDetails({
        patient_name: this.registeredData?.name || 'Registered Patient',
        department: routing.recommended_department || this.department || 'General Medicine',
        chief_complaint: res?.draft_summary?.chief_complaint || this.chiefComplaint || 'Recorded during intake',
        reasoning: routing.reasoning || 'Patient triaged and ready for consultation.'
      });

      SpeechManager.speakText(`Intake completed. Consultation Ticket number is ${ticketNum}. Please proceed to the ${routing.recommended_department || 'assigned'} department.`, this.language);
    } catch (err) {
      console.warn("Summary completion notice:", err.message);
    }
  }
};

if (typeof window !== 'undefined') {
  window.PatientIntake = PatientIntake;
}

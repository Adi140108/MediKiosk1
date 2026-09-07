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

  init() {
    // 1. Restore saved language if user previously chose one
    const savedLang = localStorage.getItem("medikiosk_lang");
    if (savedLang) {
      this.language = savedLang;
    }

    this.bindEvents();
    SpeechManager.init();
    I18n.setLanguage(this.language);
    SpeechManager.setLanguage(this.language);
    this.updateStepIndicator(1);
    this.updateLanguageGridUI(this.language);

    // 2. IMMEDIATE WELCOMING AUTO-SPEECH
    const speakWelcome = () => {
      if (this.currentStep === 1 && !SpeechManager.isSpeaking && !SpeechManager.isMuted) {
        SpeechManager.speakStepGuidance(1, this.language);
      }
    };

    // Immediate attempt on load (50ms)
    setTimeout(speakWelcome, 50);

    // Immediate attempt after 300ms
    setTimeout(speakWelcome, 300);

    // Unlock audio instantly on first gesture (click, touch, pointer, key, mouse)
    const unlockAudio = () => {
      if (SpeechManager.synth) {
        try { SpeechManager.synth.resume(); } catch(e) {}
      }
      speakWelcome();
    };

    ['click', 'touchstart', 'pointerdown', 'keydown', 'mousedown'].forEach(evt => {
      window.addEventListener(evt, unlockAudio, { once: true, passive: true });
    });
  },

  bindEvents() {
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

    if (typeof SpeechManager !== "undefined" && SpeechManager.stopAllAudio) {
      SpeechManager.stopAllAudio();
    }

    for (let i = 1; i <= 8; i++) {
      const el = document.getElementById(`kiosk-step-${i}`);
      if (el) el.style.display = i === stepNum ? "block" : "none";
    }
    this.currentStep = stepNum;
    this.updateStepIndicator(stepNum);
    window.scrollTo({ top: 0, behavior: "smooth" });

    // Step 7: Immediately set localized question text before network calls
    if (stepNum === 7) {
      if (!this.currentSessionId) {
        this.currentSessionId = `sess_${this.currentPatientId || 'pat'}_${Date.now()}`;
      }
      this.currentQuestionId = this.currentQuestionId || `q_${this.currentSessionId}_1`;

      const initialQMap = {
        en: "What is the main health concern or symptom bringing you here today?",
        hi: "आज आपको अस्पताल या क्लिनिक लाने वाली मुख्य स्वास्थ्य समस्या या लक्षण क्या है?",
        kn: "ಇಂದು ನಿಮ್ಮನ್ನು ಆಸ್ಪತ್ರೆಗೆ ಕರೆತಂದ ಮುಖ್ಯ ಆರೋಗ್ಯ ಸಮಸ್ಯೆ ಅಥವಾ ರೋಗಲಕ್ಷಣ ಯಾವುದು?",
        ta: "இன்று உங்களை மருத்துவமனைக்கு வரவழைத்த முக்கிய உடல்நலப் பிரச்சனை அல்லது அறிகுறி என்ன?",
        te: "ఈరోజు మిమ్మల్ని ఇక్కడికి తీసుకువచ్చిన ప్రధాన ఆరోగ్య సమస్య లేదా లక్షణం ఏమిటి?",
        ml: "ഇന്ന് നിങ്ങളെ ഇവിടെ എത്തിച്ച പ്രധാന ആരോഗ്യ പ്രശ്നമോ ലക്ഷണങ്ങളോ എന്താണ്?",
        mr: "आज तुम्हाला येथे आणणारी मुख्य आरोग्य समस्या किंवा लक्षण काय आहे?",
        bn: "আজ আপনাকে এখানে নিয়ে আসার প্রধান স্বাস্থ্য समस्या বা উপসর্গটি কী?",
        gu: "આજે તમને અહીં લાવનારી મુખ્ય સ્વાસ્થ્ય સમસ્યા અથવા લક્ષણ કયું છે?",
        pa: "ਅੱਜ ਤੁਹਾਨੂੰ ਇੱਥੇ ਲਿਆਉਣ ਵਾਲੀ ਮੁੱਖ ਸਿਹਤ ਸਮੱਸਿਆ ਜਾਂ ਲੱਛਣ ਕੀ ਹੈ?"
      };
      const initialQ = initialQMap[this.language] || initialQMap["en"];
      const qTextEl = document.getElementById("current-question-text");
      if (qTextEl) qTextEl.innerText = initialQ;
      this.currentQuestionText = initialQ;
    } else {
      setTimeout(() => {
        SpeechManager.speakStepGuidance(stepNum, this.language);
      }, 350);
    }
  },

  updateStepIndicator(stepNum) {
    for (let i = 1; i <= 8; i++) {
      const node = document.getElementById(`step-node-${i}`);
      const line = document.getElementById(`step-line-${i}`);
      if (node) {
        node.className = "wizard-step-node";
        if (i < stepNum) {
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
        line.className = "wizard-step-line" + (i < stepNum ? " completed" : "");
      }
    }
  },

  updateLanguageGridUI(lang) {
    document.querySelectorAll(".lang-tile").forEach((tile) => {
      if (tile.getAttribute("data-lang") === lang) {
        tile.classList.add("selected");
      } else {
        tile.classList.remove("selected");
      }
    });
  },

  selectLanguage(lang) {
    if (this.autoAdvanceTimer) {
      clearTimeout(this.autoAdvanceTimer);
      this.autoAdvanceTimer = null;
    }

    this.language = lang;
    localStorage.setItem("medikiosk_lang", lang);
    I18n.setLanguage(lang);
    SpeechManager.setLanguage(lang);
    this.updateLanguageGridUI(lang);

    const nativeLangConfirm = {
      en: "English language selected. Welcome to MediKiosk.",
      hi: "हिन्दी भाषा चुनी गई। मेडीकियोस्क में आपका स्वागत है।",
      kn: "ಕನ್ನಡ ಭಾಷೆಯನ್ನು ಆಯ್ಕೆ ಮಾಡಲಾಗಿದೆ. ಮೆಡಿಕಿಯೋಸ್ಕ್‌ಗೆ ಸುಸ್ವಾಗತ.",
      ta: "தமிழ் மொழி தேர்ந்தெடுக்கப்பட்டது. மெடிகியோஸ்கிற்கு வரவேற்கிறோம்.",
      te: "తెలుగు భాష ఎంపిక చేయబడింది. మెడికియోస్క్‌కు స్వాగతం.",
      ml: "മലയാളം ഭാഷ തിരഞ്ഞെടുത്തു. മെഡികിയോസ്കിലേക്ക് സ്വാഗതം.",
      mr: "मराठी भाषा निवडली आहे. मेडीकियोस्क मध्ये आपले स्वागत आहे.",
      bn: "বাংলা भाषा নির্বাচন করা হয়েছে। মেডিকিয়স্কে আপনাকে স্বাগতম।",
      gu: "ગુજરાતી ભાષા પસંદ કરવામાં આવી છે. મેડીકિયોસ્કમાં આપનું સ્વાગત છે.",
      pa: "ਪੰਜਾਬੀ ਭਾਸ਼ਾ ਚੁਣੀ ਗਈ ਹੈ। ਮੈਡੀਕਿਓਸਕ ਵਿੱਚ ਤੁਹਾਡਾ ਸੁਆਗਤ ਹੈ।"
    };
    const confirmMsg = nativeLangConfirm[lang] || `Language selected: ${lang}`;
    SpeechManager.speakText(confirmMsg, lang);

    // Auto-advance seamlessly to Step 3 (Consent) after 1.2s so patient flow is frictionless
    this.autoAdvanceTimer = setTimeout(() => {
      if (this.currentStep === 2) {
        this.goToStep(3);
      }
    }, 1200);
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
    this.goToStep(6);
  },

  async handleDocUpload(e) {
    e.preventDefault();
    const fileInput = document.getElementById("doc-file-input");
    if (!fileInput.files.length) {
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
      const file = fileInput.files[0];
      const formData = new FormData();
      formData.append("file", file);
      formData.append("session_id", this.currentSessionId || `sess_${Date.now()}`);
      formData.append("patient_id", this.currentPatientId || `pat_${Date.now()}`);
      formData.append("document_type", "medical_report");
      formData.append("perform_ocr", "true");

      const res = await api.uploadDocument(formData);
      
      // Document is securely stored in cloud and metadata recorded (<400ms)
      if (ocrDiv) {
        ocrDiv.innerHTML = `
          <div style="background:#f0fdf4; border:1.5px solid #86efac; border-radius:var(--radius-md); padding:1.15rem; margin-top:1rem;">
            <div style="display:flex; align-items:center; gap:8px;">
              <span style="font-size:1.3rem;">✅</span>
              <p style="font-weight:700; color:#15803d; font-size:1rem;">Document Stored ✓ — Running Background OCR</p>
            </div>
            <p style="font-size:0.85rem; color:#166534; margin-top:0.35rem;">
              Your document is securely encrypted and attached to your clinical consultation record.
            </p>
            <div id="ocr-polling-status" style="font-size:0.8rem; color:#475569; margin-top:0.5rem; display:flex; align-items:center; gap:6px;">
              <span class="spinner">⏳</span> Digitizing laboratory values and clinical entities in background...
            </div>
          </div>
        `;
      }

      btn.innerText = "2/3 Document Stored ✓";

      // Non-blocking status polling with 800ms intervals
      const docId = res.document_id;
      let attempts = 0;
      const pollOcr = async () => {
        attempts++;
        try {
          const statusRes = await api.getDocumentStatus(docId);
          if (statusRes.ocr_status === "COMPLETED") {
            const pollStatusEl = document.getElementById("ocr-polling-status");
            if (pollStatusEl) {
              const textSnippet = statusRes.extracted_text_preview || 'Clinical entities digitized successfully.';
              pollStatusEl.innerHTML = `
                <div style="width:100%;">
                  <span style="color:#15803d; font-weight:700;">✓ OCR Digitization Complete</span>
                  <div style="font-size:0.8rem; color:#1e293b; margin-top:0.4rem; font-family:monospace; background:white; padding:0.5rem; border-radius:6px; border:1px solid #bbf7d0; max-height:80px; overflow-y:auto;">
                    ${textSnippet}
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
        ml: "മെഡിക്കൽ റിപ്പോർട്ട് വിജയകരമായി അപ്‌ലോഡ് ചെയ്തു.",
        mr: "वैद्यकीय अहवाल यशस्वीरित्या अपलोड झाला आहे.",
        bn: "মেডিকেল रिपोर्ट সফলভাবে আপলোড হয়েছে।",
        gu: "મેડિકલ રિપોર્ટ સફળતાપૂર્વક અપલોડ થઈ ગયો છે.",
        pa: "ਮੈਡੀਕਲ ਰਿਪੋਰਟ ਸਫਲਤਾਪੂਰਵਕ ਅੱਪਲੋਡ ਹੋ ਗਈ ਹੈ।"
      };
      const docMsg = nativeDocSuccess[this.language] || nativeDocSuccess["en"];
      SpeechManager.speakText(docMsg, this.language);

      // Fast auto-advance to consultation after 1.5s while background task finishes
      setTimeout(() => {
        this.startSocraticIntake();
      }, 1500);

      // Background poll in parallel
      const pollInterval = setInterval(async () => {
        const done = await pollOcr();
        if (done || attempts >= 8) {
          clearInterval(pollInterval);
        }
      }, 800);

    } catch (err) {
      console.warn("Document upload error:", err.message);
      const ocrDiv = document.getElementById("doc-ocr-result");
      if (ocrDiv) {
        ocrDiv.innerHTML = `
          <div style="background:#fef2f2; border:1px solid #fca5a5; border-radius:var(--radius-md); padding:1rem; margin-top:1rem;">
            <p style="font-weight:700; color:#991b1b;">⚠️ Upload Notice</p>
            <p style="font-size:0.85rem; color:#7f1d1d; margin-top:0.25rem;">We could not upload this file, but you can continue with your voice consultation.</p>
          </div>
        `;
      }
      setTimeout(() => this.startSocraticIntake(), 1200);
    } finally {
      btn.disabled = false;
      btn.innerText = "Upload & Run OCR";
    }
  },

  async startSocraticIntake() {
    this.goToStep(7);

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
        this.currentSessionId
      );

      if (res.session_id) {
        this.currentSessionId = res.session_id;
      }
      if (res.question && res.question.question_id) {
        this.currentQuestionId = res.question.question_id;
      }

      // If initial complaint was entered, seed it
      const complaintText = document.getElementById("chief-complaint-input")?.value.trim();
      if (complaintText) {
        const answerRes = await api.submitAnswer(
          this.currentSessionId,
          this.currentQuestionId,
          complaintText,
          this.isAttendant ? "ATTENDANT" : "PATIENT",
          this.attendantId,
          this.language
        );
        if (answerRes && answerRes.next_question) {
          this.renderQuestion(answerRes.next_question);
        } else if (res.question) {
          this.renderQuestion(res.question);
        }
      } else if (res.question) {
        this.renderQuestion(res.question);
      }
    } catch (err) {
      console.warn("Intake session initialization notice:", err.message);
      const initialQMap = {
        en: "What is the main health concern or symptom bringing you here today?",
        hi: "आज आपको अस्पताल या क्लिनिक लाने वाली मुख्य स्वास्थ्य समस्या या लक्षण क्या है?",
        kn: "ಇಂದು ನಿಮ್ಮನ್ನು ಆಸ್ಪತ್ರೆಗೆ ಕರೆತಂದ ಮುಖ್ಯ ಆರೋಗ್ಯ ಸಮಸ್ಯೆ ಅಥವಾ ರೋಗಲಕ್ಷಣ ಯಾವುದು?",
        ta: "இன்று உங்களை மருத்துவமனைக்கு வரவழைத்த முக்கிய உடல்நலப் பிரச்சனை அல்லது அறிகுறி என்ன?",
        te: "ఈరోజు మిమ్మల్ని ఇక్కడికి తీసుకువచ్చిన ప్రధాన ఆరోగ్య సమస్య లేదా లక్షణం ఏమిటి?",
        ml: "ഇന്ന് നിങ്ങളെ ഇവിടെ എത്തിച്ച പ്രധാന ആരോഗ്യ പ്രശ്നമോ ലക്ഷണങ്ങളോ എന്താണ്?",
        mr: "आज तुम्हाला येथे आणणारी मुख्य आरोग्य समस्या किंवा लक्षण काय आहे?",
        bn: "আজ আপনাকে এখানে নিয়ে আসার প্রধান স্বাস্থ্য সমস্যা বা উপসর্গটি কী?",
        gu: "આજે તમને અહીં લાવનારી મુખ્ય સ્વાસ્થ્ય સમસ્યા અથવા લક્ષણ કયું છે?",
        pa: "ਅੱਜ ਤੁਹਾਨੂੰ ਇੱਥੇ ਲਿਆਉਣ ਵਾਲੀ ਮੁੱਖ ਸਿਹਤ ਸਮੱਸਿਆ ਜਾਂ ਲੱਛਣ ਕੀ ਹੈ?"
      };
      const q = initialQMap[this.language] || initialQMap["en"];
      this.renderQuestion({
        question_id: `q_${this.currentSessionId || 'default'}_1`,
        question: q,
        objective: "Identify chief complaint"
      });
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

    const input = document.getElementById("patient-answer-input");
    if (input) {
      input.value = "";
      input.focus();
    }

    // Auto-speak question in patient's selected language using Indian female voice TTS, then auto-open mic
    SpeechManager.speakText(this.currentQuestionText, this.language, () => {
      SpeechManager.startListeningWithSilenceTimeout(4000);
    });
  },

  speakCurrentQuestion() {
    if (this.currentQuestionText) {
      SpeechManager.speakText(this.currentQuestionText, this.language, () => {
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

  async finishIntake() {
    this.goToStep(8);

    try {
      const res = await api.completeIntake(this.currentSessionId, this.currentPatientId || 'pat_dev');
      const ticketNum = `MK-${Math.floor(10000000 + Math.random() * 90000000)}`;
      
      const numEl = document.getElementById("ticket-number-display");
      if (numEl) numEl.innerText = ticketNum;

      const rf = res?.red_flag || { overall_severity: "MEDIUM" };
      const routing = res?.routing || { recommended_department: "general_medicine", reasoning: "Comprehensive clinical intake recorded." };

      const badgeContainer = document.getElementById("ticket-triage-badge");
      if (badgeContainer) {
        let badgeClass = "lang-badge-connected";
        if (rf.overall_severity === "CRITICAL") badgeClass = "lang-badge-connected' style='background:#fee2e2; color:#991b1b;";
        else if (rf.overall_severity === "HIGH") badgeClass = "lang-badge-connected' style='background:#ffedd5; color:#9a3412;";
        else if (rf.overall_severity === "MEDIUM") badgeClass = "lang-badge-connected' style='background:#fef3c7; color:#92400e;";

        badgeContainer.innerHTML = `<span class="lang-tile-badge ${badgeClass}">${rf.overall_severity} PRIORITY</span>`;
      }

      const bodyEl = document.getElementById("ticket-details-body");
      if (bodyEl) {
        bodyEl.innerHTML = `
          <div style="display:grid; grid-template-columns: 1fr 1fr; gap:1.25rem; margin-bottom:1rem;">
            <div>
              <span style="font-size:0.8rem; color:var(--text-muted); font-weight:700;">PATIENT NAME</span>
              <p style="font-weight:700; font-size:1.05rem;">${this.registeredData?.name || 'Patient'}</p>
            </div>
            <div>
              <span style="font-size:0.8rem; color:var(--text-muted); font-weight:700;">ASSIGNED DEPARTMENT</span>
              <p style="font-weight:700; font-size:1.05rem; color:var(--brand-primary);">${(routing.recommended_department || 'General Medicine').toUpperCase()}</p>
            </div>
          </div>
          <div style="margin-bottom:1rem;">
            <span style="font-size:0.8rem; color:var(--text-muted); font-weight:700;">CHIEF COMPLAINT NARRATIVE</span>
            <p style="font-style:italic; color:#334155;">"${res?.draft_summary?.chief_complaint || 'Recorded during intake'}"</p>
          </div>
          <div style="background:#faf8f5; border:1px solid #e5e0d5; padding:0.85rem; border-radius:var(--radius-sm); font-size:0.875rem;">
            <p><strong>Routing Assessment:</strong> ${routing.reasoning || 'Patient triaged and ready for consultation.'}</p>
          </div>
        `;
      }

      SpeechManager.speakText(`Intake completed. Consultation Ticket number is ${ticketNum}. Please proceed to the ${routing.recommended_department || 'assigned'} department.`, this.language);
    } catch (err) {
      console.warn("Summary completion notice:", err.message);
    }
  }
};

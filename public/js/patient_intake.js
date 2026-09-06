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
    this.bindEvents();
    SpeechManager.init();
    I18n.setLanguage("en");
    this.updateStepIndicator(1);
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
    for (let i = 1; i <= 8; i++) {
      const el = document.getElementById(`kiosk-step-${i}`);
      if (el) el.style.display = i === stepNum ? "block" : "none";
    }
    this.currentStep = stepNum;
    this.updateStepIndicator(stepNum);
    window.scrollTo({ top: 0, behavior: "smooth" });
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

  selectLanguage(lang) {
    this.language = lang;
    I18n.setLanguage(lang);
    SpeechManager.setLanguage(lang);

    // Update active tile in grid
    document.querySelectorAll(".lang-tile").forEach((tile) => {
      if (tile.getAttribute("data-lang") === lang) {
        tile.classList.add("selected");
      } else {
        tile.classList.remove("selected");
      }
    });

    const langNames = {
      en: "English", hi: "हिन्दी (Hindi)", kn: "ಕನ್ನಡ (Kannada)",
      ta: "தமிழ் (Tamil)", te: "తెలుగు (Telugu)", ml: "മലയാളം (Malayalam)",
      mr: "मराठी (Marathi)", bn: "বাংলা (Bengali)", gu: "ગુજરાતી (Gujarati)", pa: "ਪੰਜਾਬੀ (Punjabi)"
    };
    SpeechManager.speakText(`Language selected: ${langNames[lang] || lang}`, lang);
  },

  handleConsentNext() {
    const consentBox = document.getElementById("consent-checkbox");
    if (consentBox && !consentBox.checked) {
      alert("Please agree to the privacy and intake terms to continue.");
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

  handleComplaintNext() {
    const input = document.getElementById("chief-complaint-input");
    this.painLevel = document.getElementById("pain-range")?.value || 7;
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
    btn.innerText = "Analyzing & Extracting OCR...";

    try {
      const file = fileInput.files[0];
      const formData = new FormData();
      formData.append("file", file);
      formData.append("session_id", this.currentSessionId);
      formData.append("patient_id", this.currentPatientId);
      formData.append("document_type", "medical_report");
      formData.append("perform_ocr", "true");

      const res = await api.uploadDocument(formData);
      const ocrDiv = document.getElementById("doc-ocr-result");
      if (ocrDiv && res.ocr) {
        ocrDiv.innerHTML = `
          <div style="background:#f0fdf4; border:1px solid #86efac; border-radius:var(--radius-md); padding:1rem;">
            <p style="font-weight:700; color:#166534;">✓ Document Stored (${res.metadata.storage_provider}) & OCR Digitized</p>
            <p style="font-size:0.85rem; color:#14532d; margin-top:0.35rem; font-family:monospace; background:white; padding:0.5rem; border-radius:4px;">
              ${res.ocr.extracted_text || 'Structured entities extracted successfully.'}
            </p>
          </div>
        `;
      }
    } catch (err) {
      alert("Document upload notice: " + err.message);
    } finally {
      btn.disabled = false;
      btn.innerText = "Upload & Run OCR";
      setTimeout(() => this.startSocraticIntake(), 1200);
    }
  },

  async startSocraticIntake() {
    this.goToStep(7);

    try {
      const res = await api.startIntake(
        this.currentPatientId,
        this.language,
        this.isAttendant,
        this.attendantId
      );

      // If initial complaint was entered, seed it
      const complaintText = document.getElementById("chief-complaint-input")?.value.trim();
      if (complaintText) {
        // Pre-submit initial complaint
        const answerRes = await api.submitAnswer(
          this.currentSessionId,
          res.question.question_id,
          complaintText,
          this.isAttendant ? "ATTENDANT" : "PATIENT",
          this.attendantId,
          this.language
        );
        if (answerRes.next_question) {
          this.renderQuestion(answerRes.next_question);
        } else {
          this.renderQuestion(res.question);
        }
      } else {
        this.renderQuestion(res.question);
      }
    } catch (err) {
      alert("Intake session initialization failed: " + err.message);
    }
  },

  renderQuestion(question) {
    this.currentQuestionId = question.question_id;
    this.currentQuestionText = question.question;

    const qTextEl = document.getElementById("current-question-text");
    const qBadgeEl = document.getElementById("current-question-badge");
    const qAyurEl = document.getElementById("current-ayur-badge");

    if (qTextEl) qTextEl.innerText = question.question;
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

    // Auto-speak question using TTS
    SpeechManager.speakText(question.question, this.language);
  },

  speakCurrentQuestion() {
    if (this.currentQuestionText) {
      SpeechManager.speakText(this.currentQuestionText, this.language);
    }
  },

  async handleAnswerSubmit() {
    const input = document.getElementById("patient-answer-input");
    const answer = input.value.trim();
    if (!answer) return;

    const btn = document.getElementById("btn-submit-answer");
    btn.disabled = true;

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
      if (res.live_summary && liveSumEl) {
        liveSumEl.style.display = "block";
        liveSumEl.innerHTML = `<strong>Verification:</strong> ${res.live_summary}`;
      }

      if (res.is_finished || !res.next_question) {
        await this.finishIntake();
      } else {
        this.renderQuestion(res.next_question);
      }
    } catch (err) {
      alert("Answer submission failed: " + err.message);
    } finally {
      btn.disabled = false;
    }
  },

  async finishIntake() {
    this.goToStep(8);

    try {
      const res = await api.completeIntake(this.currentSessionId, this.currentPatientId);
      const ticketNum = `MK-${Math.floor(10000000 + Math.random() * 90000000)}`;
      
      const numEl = document.getElementById("ticket-number-display");
      if (numEl) numEl.innerText = ticketNum;

      const rf = res.red_flag;
      const routing = res.routing;

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
              <p style="font-weight:700; font-size:1.05rem; color:var(--brand-primary);">${routing.recommended_department.toUpperCase()}</p>
            </div>
          </div>
          <div style="margin-bottom:1rem;">
            <span style="font-size:0.8rem; color:var(--text-muted); font-weight:700;">CHIEF COMPLAINT NARRATIVE</span>
            <p style="font-style:italic; color:#334155;">"${res.draft_summary.chief_complaint}"</p>
          </div>
          <div style="background:#faf8f5; border:1px solid #e5e0d5; padding:0.85rem; border-radius:var(--radius-sm); font-size:0.875rem;">
            <p><strong>Routing Assessment:</strong> ${routing.reasoning}</p>
          </div>
        `;
      }

      SpeechManager.speakText(`Intake completed. Consultation Ticket number is ${ticketNum}. Please proceed to the ${routing.recommended_department} department.`, this.language);
    } catch (err) {
      alert("Summary completion notice: " + err.message);
    }
  }
};


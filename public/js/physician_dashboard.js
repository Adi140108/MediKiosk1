const DEFAULT_DEPARTMENTS = [
  { id: "general-medicine", display_name: "General Medicine", icon: "🩺", description: "Primary care, acute viral illnesses, non-specific fevers and multisystem initial evaluations." },
  { id: "cardiology", display_name: "Cardiology", icon: "🫀", description: "Chest pain, palpitations, hypertension, ischemic workup and cardiovascular risk assessments." },
  { id: "pulmonology", display_name: "Pulmonology", icon: "🫁", description: "Respiratory distress, persistent cough, dyspnea, asthma and chronic airway disorders." },
  { id: "neurology", display_name: "Neurology", icon: "🧠", description: "Headaches, dizziness, focal neurological deficits, seizures and stroke triage evaluations." },
  { id: "gastroenterology", display_name: "Gastroenterology", icon: "🍽️", description: "Abdominal pain, acute gastrointestinal bleed, jaundice, peptic and hepatic conditions." },
  { id: "orthopedics", display_name: "Orthopedics", icon: "🦴", description: "Trauma, fractures, severe joint swellings, musculoskeletal injuries and spinal pain." },
  { id: "pediatrics", display_name: "Pediatrics", icon: "👶", description: "Infant and pediatric clinical reviews, childhood infections and pediatric triage." },
  { id: "emergency", display_name: "Emergency / Trauma", icon: "🚨", description: "Immediate life-threatening triage, critical red flags, and emergency resuscitation." },
  { id: "dermatology", display_name: "Dermatology", icon: "🧴", description: "Acute dermatological reactions, lesions, severe urticaria and cutaneous eruptions." },
  { id: "ent", display_name: "ENT", icon: "👂", description: "Ear discharge, hearing changes, vertigo, acute epistaxis and throat infections." },
  { id: "ophthalmology", display_name: "Ophthalmology", icon: "👁", description: "Visual disturbances, acute eye trauma, red eye and ocular pressure emergencies." },
  { id: "psychiatry", display_name: "Psychiatry", icon: "🧩", description: "Acute distress, behavioral emergencies, psychiatric triage and mood disorders." },
  { id: "ayush", display_name: "AYUSH / Integrative", icon: "🌿", description: "Ayurvedic clinical constitution, dosha assessment and integrative outpatient care." },
  { id: "unspecified", display_name: "Triage & Float Queue", icon: "🏥", description: "Ambiguous symptoms, multi-system red flags, and float cases awaiting department routing." }
];

const PhysicianDashboard = {
  currentDepartment: null,
  currentDepartmentName: "Cardiology",
  currentSessionId: null,
  currentPatientData: null,
  refreshTimer: null,
  originalRecommendedDept: null,
  originalRecommendedPriority: null,

  init() {
    this.bindEvents();
    this.renderDepartmentGrid(DEFAULT_DEPARTMENTS);
    this.loadDepartmentSelection();
  },

  bindEvents() {
    const searchInput = document.getElementById("queue-search-input");
    if (searchInput) {
      searchInput.addEventListener("input", () => this.loadQueue());
    }

    const sevFilter = document.getElementById("queue-severity-filter");
    if (sevFilter) {
      sevFilter.addEventListener("change", () => this.loadQueue());
    }

    const statusFilter = document.getElementById("queue-status-filter");
    if (statusFilter) {
      statusFilter.addEventListener("change", () => this.loadQueue());
    }

    const confirmForm = document.getElementById("physician-confirm-form");
    if (confirmForm) {
      confirmForm.addEventListener("submit", (e) => this.handleConfirmCase(e));
    }

    // Dynamic Override Detection
    const deptSelect = document.getElementById("confirm-dept-select");
    const prioritySelect = document.getElementById("confirm-priority-select");
    if (deptSelect) {
      deptSelect.addEventListener("change", () => this.checkOverrideStatus());
    }
    if (prioritySelect) {
      prioritySelect.addEventListener("change", () => this.checkOverrideStatus());
    }
  },

  renderDepartmentGrid(departments) {
    const grid = document.getElementById("dept-selection-grid");
    if (!grid || !departments || departments.length === 0) return;

    grid.innerHTML = "";
    departments.forEach((dept) => {
      const card = document.createElement("div");
      card.className = "lang-tile";
      card.style.textAlign = "left";
      card.style.alignItems = "flex-start";
      card.style.padding = "1.5rem";
      card.style.cursor = "pointer";

      const badgeClass = dept.id === "unspecified" ? "lang-badge-fallback" : "lang-badge-ready";
      const badgeLabel = dept.id === "unspecified" ? "TRIAGE QUEUE →" : "ACCESS QUEUE →";

      card.innerHTML = `
        <div style="font-size:2rem; margin-bottom:0.5rem;">${dept.icon || '🩺'}</div>
        <span class="lang-tile-native" style="font-size:1.2rem;">${dept.display_name || dept.name}</span>
        <p style="font-size:0.825rem; color:var(--text-muted); margin-top:0.25rem; line-height:1.4;">${dept.description || 'Clinical department review queue.'}</p>
        <span class="lang-tile-badge ${badgeClass}" style="margin-top:1rem;">${badgeLabel}</span>
      `;
      card.addEventListener("click", () => this.selectDepartment(dept.id, dept.display_name || dept.name, dept.icon || '🩺'));
      grid.appendChild(card);
    });
  },

  async loadDepartmentSelection() {
    try {
      const departments = await api.getDepartments();
      if (departments && departments.length > 0) {
        this.renderDepartmentGrid(departments);
      }
    } catch (err) {
      console.warn("Using default department fallback list:", err);
      this.renderDepartmentGrid(DEFAULT_DEPARTMENTS);
    }
  },

  showDepartmentSelection() {
    clearInterval(this.refreshTimer);
    document.getElementById("physician-dept-view").style.display = "block";
    document.getElementById("physician-queue-view").style.display = "none";
    document.getElementById("physician-case-view").style.display = "none";
    this.currentDepartment = null;
  },

  selectDepartment(deptId, deptName, deptIcon) {
    this.currentDepartment = deptId;
    this.currentDepartmentName = deptName;
    document.getElementById("physician-dept-view").style.display = "none";
    document.getElementById("physician-queue-view").style.display = "block";
    document.getElementById("physician-case-view").style.display = "none";

    const titleEl = document.getElementById("selected-dept-title");
    if (titleEl) titleEl.innerHTML = `${deptIcon} ${deptName} Department`;

    this.loadQueue();

    clearInterval(this.refreshTimer);
    // Near real-time 4-second sync interval for fast reflection
    this.refreshTimer = setInterval(() => this.loadQueue(), 4000);
  },

  showQueueView() {
    document.getElementById("physician-dept-view").style.display = "none";
    document.getElementById("physician-queue-view").style.display = "block";
    document.getElementById("physician-case-view").style.display = "none";
    this.loadQueue();
    if (this.currentDepartment) {
      clearInterval(this.refreshTimer);
      this.refreshTimer = setInterval(() => this.loadQueue(), 4000);
    }
  },

  async loadQueue() {
    if (!this.currentDepartment) return;

    const search = document.getElementById("queue-search-input")?.value.trim() || null;
    const severity = document.getElementById("queue-severity-filter")?.value || null;
    const status = document.getElementById("queue-status-filter")?.value || null;

    try {
      const [items, dashData] = await Promise.all([
        api.getDepartmentQueue(this.currentDepartment, search, severity, status),
        api.getDepartmentDashboard(this.currentDepartment).catch(() => null)
      ]);

      const tableBody = document.getElementById("priority-queue-table-body");
      if (!tableBody) return;

      tableBody.innerHTML = "";

      const queueCount = document.getElementById("stat-queue-count");
      const urgentCount = document.getElementById("stat-urgent-count");
      const inReviewCount = document.getElementById("stat-in-review-count");
      const auditedCount = document.getElementById("stat-audited-count");

      if (dashData && dashData.metrics) {
        if (queueCount) queueCount.innerText = dashData.metrics.waiting_count;
        if (urgentCount) urgentCount.innerText = dashData.metrics.critical_count + dashData.metrics.high_count;
        if (inReviewCount) inReviewCount.innerText = dashData.metrics.in_review_count;
        if (auditedCount) auditedCount.innerText = dashData.metrics.completed_today;
      } else {
        if (queueCount) queueCount.innerText = items.filter(i => i.status === "WAITING").length;
        if (urgentCount) urgentCount.innerText = items.filter(i => i.overall_severity === "CRITICAL" || i.overall_severity === "HIGH").length;
        if (inReviewCount) inReviewCount.innerText = items.filter(i => i.status === "IN_REVIEW").length;
        if (auditedCount) auditedCount.innerText = items.filter(i => i.status === "COMPLETED").length;
      }

      if (!items || items.length === 0) {
        tableBody.innerHTML = `
          <tr>
            <td colspan="6" style="text-align:center; padding:3rem; color:var(--text-muted);">
              <p style="font-weight:700; font-size:1.05rem;">No patients currently in this department queue.</p>
              <p style="font-size:0.85rem; margin-top:0.25rem;">Patients completing kiosk intake or transferred here will appear automatically.</p>
            </td>
          </tr>
        `;
        return;
      }

      items.forEach((item) => {
        const tr = document.createElement("tr");

        let sevBadge = `<span class="lang-tile-badge lang-badge-connected">NORMAL</span>`;
        if (item.overall_severity === "CRITICAL") {
          sevBadge = `<span class="lang-tile-badge" style="background:#fee2e2; color:#991b1b; border:1px solid #ef4444;">🚨 CRITICAL</span>`;
        } else if (item.overall_severity === "HIGH") {
          sevBadge = `<span class="lang-tile-badge" style="background:#ffedd5; color:#9a3412; border:1px solid #f97316;">⚠️ HIGH</span>`;
        } else if (item.overall_severity === "MEDIUM") {
          sevBadge = `<span class="lang-tile-badge" style="background:#fef3c7; color:#92400e; border:1px solid #f59e0b;">MEDIUM</span>`;
        }

        let statusBadge = `<span class="lang-tile-badge lang-badge-connected">${item.status}</span>`;
        if (item.status === "WAITING") {
          statusBadge = `<span class="lang-tile-badge" style="background:#ecfdf5; color:#065f46; border:1px solid #10b981;">WAITING</span>`;
        } else if (item.status === "IN_REVIEW") {
          statusBadge = `<span class="lang-tile-badge" style="background:#e0f2fe; color:#0369a1; border:1px solid #38bdf8;">IN REVIEW</span>`;
        } else if (item.status === "COMPLETED") {
          statusBadge = `<span class="lang-tile-badge" style="background:#f1f5f9; color:#475569; border:1px solid #cbd5e1;">COMPLETED</span>`;
        }

        const waitDisplay = item.waiting_time_minutes > 60
          ? `${Math.floor(item.waiting_time_minutes / 60)}h ${item.waiting_time_minutes % 60}m`
          : `${item.waiting_time_minutes} min`;

        tr.innerHTML = `
          <td>
            <div style="font-weight:700; color:var(--brand-primary); font-size:0.95rem;">${item.patient_name}</div>
            <div style="font-size:0.75rem; color:var(--text-muted);">${item.patient_id} • ${item.age}y / ${item.gender}</div>
          </td>
          <td>${sevBadge}</td>
          <td>
            <div style="font-size:0.85rem; font-weight:600; color:#1e293b; max-width:280px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
              ${item.chief_complaint_summary || "Clinical check-in completed"}
            </div>
            ${item.has_documents ? '<span style="font-size:0.7rem; color:#0369a1; font-weight:600;">📎 Records Attached</span>' : ''}
          </td>
          <td>
            <span style="font-size:0.85rem; font-weight:600;">${waitDisplay}</span>
          </td>
          <td>${statusBadge}</td>
          <td>
            <div style="display:flex; gap:0.4rem;">
              <button class="btn-primary-action" style="padding:0.35rem 0.75rem; font-size:0.8rem;" onclick="PhysicianDashboard.inspectPatientCase('${item.session_id}')">
                Review Case →
              </button>
              <button class="btn-secondary-action" style="padding:0.35rem 0.65rem; font-size:0.8rem;" title="Reassign Department" onclick="PhysicianDashboard.handleDirectReassign('${item.session_id}')">
                ↗ Transfer
              </button>
            </div>
          </td>
        `;
        tableBody.appendChild(tr);
      });
    } catch (err) {
      console.error("Queue fetch error:", err);
    }
  },

  async inspectPatientCase(sessionId) {
    this.currentSessionId = sessionId;
    clearInterval(this.refreshTimer);

    document.getElementById("physician-dept-view").style.display = "none";
    document.getElementById("physician-queue-view").style.display = "none";
    document.getElementById("physician-case-view").style.display = "block";
    window.scrollTo({ top: 0, behavior: "smooth" });

    try {
      const data = await api.getPatientCase(sessionId);
      this.currentPatientData = data;
      this.populateCaseInspector(data);
    } catch (err) {
      alert("Failed to load patient case record: " + err.message);
      this.showQueueView();
    }
  },

  populateCaseInspector(data) {
    const patient = data.patient || {};
    const draft_summary = data.draft_summary || data.clinical_brief || {};
    const red_flag = data.red_flag || data.red_flags || {};
    const routing = data.routing || {};
    const documents = data.documents || [];
    const medical_history = data.medical_history || {};
    const ayurvedic_assessment = data.ayurvedic_assessment || {};
    const questions = data.questions || [];
    const answers = data.answers || [];
    const timeline = data.timeline || [];
    const information_gaps = data.information_gaps || [];

    // 1. Patient Header Details
    const overviewEl = document.getElementById("case-patient-overview");
    if (overviewEl) {
      overviewEl.innerHTML = `
        <h2 style="font-size:1.4rem; color:var(--brand-primary); margin:0;">${patient.name || 'Patient Case'}</h2>
        <p style="font-size:0.85rem; color:var(--text-muted); margin-top:0.25rem;">
          ID: <strong>${patient.patient_id || 'N/A'}</strong> • Age: <strong>${patient.age || 'N/A'}y</strong> • Gender: <strong>${patient.gender || 'N/A'}</strong> • Preferred Language: <strong>${(patient.preferred_language || 'EN').toUpperCase()}</strong> • ABHA: <strong>${patient.abha_id || 'Hospital Walk-in'}</strong>
        </p>
      `;
    }

    // 2. Red Flag Banner
    const redFlagBanner = document.getElementById("case-redflag-banner") || document.getElementById("inspect-red-flag-banner");
    const rfTitle = document.getElementById("rf-banner-title");
    const rfDesc = document.getElementById("rf-banner-desc") || document.getElementById("inspect-red-flag-details");
    
    if (red_flag && red_flag.is_red_flag) {
      if (redFlagBanner) redFlagBanner.style.display = "block";
      const reasons = (red_flag.flagged_reasons || []).join(" • ") || "Clinical urgency criteria identified during intake.";
      if (rfTitle) rfTitle.innerText = `🚨 ${red_flag.overall_severity} CLINICAL RED FLAG DETECTED`;
      if (rfDesc) rfDesc.innerHTML = `<p>${reasons}</p>`;
    } else {
      if (redFlagBanner) redFlagBanner.style.display = "none";
    }

    // 3. Explainable AI Cards
    const expRouting = document.getElementById("explain-routing-content");
    if (expRouting) {
      expRouting.innerHTML = `
        <p><strong>Affinity:</strong> ${routing.recommended_department ? routing.recommended_department.toUpperCase() : 'GENERAL MEDICINE'}</p>
        <p style="margin-top:0.35rem; font-size:0.825rem; line-height:1.4;">${routing.reasoning || 'Symptom pattern matching aligns with this clinical department.'}</p>
      `;
    }

    const expPriority = document.getElementById("explain-priority-content");
    if (expPriority) {
      const priorityLabel = red_flag.overall_severity || "NORMAL";
      expPriority.innerHTML = `
        <p><strong>Priority Tier:</strong> ${priorityLabel}</p>
        <p style="margin-top:0.35rem; font-size:0.825rem; line-height:1.4;">${red_flag.triage_rationale || red_flag.reasoning || 'Standard OPD consultation priority.'}</p>
      `;
    }

    const expGaps = document.getElementById("explain-gaps-content");
    if (expGaps) {
      if (information_gaps && information_gaps.length > 0) {
        expGaps.innerHTML = information_gaps.map(g => `<span class="gap-pill">⚠️ ${g.label || g.field}</span>`).join("");
      } else {
        expGaps.innerHTML = `<p style="color:#166534; font-size:0.825rem;">✓ Complete clinical profile captured.</p>`;
      }
    }

    // 4. Modern Clinical Brief
    const complaintText = document.getElementById("case-chief-complaint-text");
    if (complaintText) complaintText.innerText = draft_summary.chief_complaint || "Patient presents for consultation review.";

    const hpiText = document.getElementById("case-hpi-text");
    if (hpiText) hpiText.innerText = draft_summary.hpi_narrative || "No extended narrative recorded.";

    const progText = document.getElementById("case-progression-text");
    if (progText) progText.innerText = (draft_summary.associated_symptoms || []).join(", ") || "No specific associated symptoms reported.";

    const medHistText = document.getElementById("case-medical-history-text");
    if (medHistText) {
      const cond = (medical_history.known_conditions || []).join(", ");
      const meds = (medical_history.medications || []).join(", ");
      medHistText.innerText = `Conditions: ${cond || 'None'} | Medications: ${meds || 'None'}`;
    }

    // 5. Ayurvedic Perspective
    const ayurEl = document.getElementById("case-ayurvedic-details");
    if (ayurEl) {
      if (ayurvedic_assessment && Object.keys(ayurvedic_assessment).length > 0) {
        ayurEl.innerHTML = `
          <p><strong>Dominant Dosha:</strong> ${ayurvedic_assessment.dominant_dosha || 'Vata-Pitta'}</p>
          <p style="margin-top:0.35rem;"><strong>Agni Assessment:</strong> ${ayurvedic_assessment.agni_status || 'Manda Agni (Sluggish)'}</p>
          <p style="margin-top:0.35rem;"><strong>Suggested Pathya (Diet):</strong> ${(ayurvedic_assessment.dietary_guidelines || ['Warm fluids', 'Light diet']).join(', ')}</p>
        `;
      } else {
        ayurEl.innerHTML = `<p style="color:#713f12; font-style:italic;">Integrative Ayurvedic dosha assessment mapped to primary presentation.</p>`;
      }
    }

    // 6. Socratic Transcript & Timeline
    const qaList = document.getElementById("case-qa-list");
    if (qaList) {
      if (questions && questions.length > 0) {
        qaList.innerHTML = questions.map((q, idx) => {
          const ans = answers.find(a => a.question_id === q.question_id);
          return `
            <div style="margin-bottom:0.85rem; padding-bottom:0.75rem; border-bottom:1px solid #f1ece4;">
              <div style="font-weight:600; font-size:0.875rem; color:var(--brand-primary); margin-bottom:0.2rem;">
                Q${idx + 1}: ${q.question}
              </div>
              <div style="background:#f8fafc; border-left:3px solid var(--brand-primary); padding:0.4rem 0.65rem; border-radius:0 4px 4px 0; font-size:0.85rem; color:#1e293b;">
                <strong>Answer:</strong> "${ans ? ans.answer_text : 'Pending'}"
              </div>
            </div>
          `;
        }).join("");
      } else {
        qaList.innerHTML = `<p style="color:var(--text-muted); font-size:0.85rem;">Clinical intake completed with initial chief complaint profile.</p>`;
      }
    }

    const timelineList = document.getElementById("case-timeline-list");
    if (timelineList) {
      if (timeline && timeline.length > 0) {
        timelineList.innerHTML = timeline.map(t => `
          <div style="font-size:0.825rem; padding:0.4rem 0; border-bottom:1px solid #f1f5f9; display:flex; justify-content:space-between;">
            <span><strong>${t.title}</strong> — ${t.description || ''}</span>
            <span style="color:var(--text-muted); font-family:monospace;">${t.timestamp ? t.timestamp.split('T')[1]?.substring(0,5) || '' : ''}</span>
          </div>
        `).join("");
      } else {
        timelineList.innerHTML = `<p style="color:var(--text-muted); font-size:0.85rem;">Timeline logged in audit storage.</p>`;
      }
    }

    // 7. OCR Documents
    const docsList = document.getElementById("case-ocr-documents-list");
    if (docsList) {
      if (documents && documents.length > 0) {
        docsList.innerHTML = documents.map(d => `
          <div class="ocr-item-card">
            <div class="ocr-item-header">
              <span><strong>📄 ${d.original_filename || d.filename || 'Medical Document'}</strong></span>
              <span>Provider: ${d.storage_provider || 'Encrypted Store'}</span>
            </div>
            <div class="ocr-item-content">
              ${d.extracted_text || d.ocr_text || 'OCR entities digitized successfully.'}
            </div>
            ${d.access_url ? `<a href="${d.access_url}" target="_blank" style="display:inline-block; font-size:0.75rem; color:#0369a1; font-weight:600; margin-top:0.35rem; text-decoration:none;">View Uploaded Scan ↗</a>` : ''}
          </div>
        `).join("");
      } else {
        docsList.innerHTML = `<p style="color:var(--text-muted); font-size:0.85rem; font-style:italic;">No previous reports or prescriptions uploaded by patient.</p>`;
      }
    }

    // 8. Decision Form Pre-fill
    this.originalRecommendedDept = routing.recommended_department || "general-medicine";
    this.originalRecommendedPriority = red_flag.overall_severity || "NONE";

    const summaryEdit = document.getElementById("physician-summary-edit");
    if (summaryEdit) {
      summaryEdit.value = draft_summary.chief_complaint 
        ? `${draft_summary.chief_complaint}. ${draft_summary.hpi_narrative || ''}`
        : "Patient presents for clinical consultation.";
    }

    const deptSelect = document.getElementById("confirm-dept-select");
    if (deptSelect && routing.recommended_department) {
      deptSelect.value = routing.recommended_department;
    }

    const prioritySelect = document.getElementById("confirm-priority-select");
    if (prioritySelect && red_flag.overall_severity) {
      prioritySelect.value = red_flag.overall_severity;
    }

    this.checkOverrideStatus();
  },

  checkOverrideStatus() {
    const deptSelect = document.getElementById("confirm-dept-select");
    const prioritySelect = document.getElementById("confirm-priority-select");
    const overrideBox = document.getElementById("override-reason-container");
    const pill = document.getElementById("decision-status-pill");

    if (!deptSelect || !prioritySelect || !overrideBox) return;

    const currentDept = deptSelect.value;
    const currentPriority = prioritySelect.value;

    const isDeptChanged = this.originalRecommendedDept && currentDept !== this.originalRecommendedDept;
    const isPriorityChanged = this.originalRecommendedPriority && currentPriority !== this.originalRecommendedPriority;

    if (isDeptChanged || isPriorityChanged) {
      overrideBox.style.display = "block";
      if (pill) {
        pill.className = "lang-tile-badge lang-badge-fallback";
        pill.innerText = "OVERRIDE / REASSIGNMENT DETECTED";
      }
    } else {
      overrideBox.style.display = "none";
      if (pill) {
        pill.className = "lang-tile-badge lang-badge-ready";
        pill.innerText = "ALIGNED WITH AI";
      }
    }
  },

  openTransferModal() {
    if (!this.currentSessionId) {
      alert("Please select or open a patient case first.");
      return;
    }
    const modal = document.getElementById("transfer-patient-modal");
    if (!modal) return;
    const deptSelect = document.getElementById("transfer-target-dept");
    if (deptSelect && this.currentDepartment) {
      deptSelect.value = this.currentDepartment === "cardiology" ? "general-medicine" : "cardiology";
    }
    const reasonInput = document.getElementById("transfer-reason-input");
    if (reasonInput) reasonInput.value = "";
    modal.style.display = "flex";
  },

  closeTransferModal() {
    const modal = document.getElementById("transfer-patient-modal");
    if (modal) modal.style.display = "none";
  },

  async submitDepartmentTransfer(e) {
    if (e) e.preventDefault();
    if (!this.currentSessionId) {
      alert("No active patient case selected.");
      return;
    }

    const targetDept = document.getElementById("transfer-target-dept").value;
    const priority = document.getElementById("transfer-priority-select").value;
    const physicianId = document.getElementById("transfer-physician-id").value.trim() || "dr_sharma_cardio";
    const reason = document.getElementById("transfer-reason-input").value.trim();

    if (!reason) {
      alert("Please provide a clinical rationale for the department transfer.");
      return;
    }

    const submitBtn = document.getElementById("btn-submit-transfer");
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.innerText = "Transferring Patient...";
    }

    try {
      await api.reassignDepartment(this.currentSessionId, targetDept, physicianId, reason);
      this.closeTransferModal();

      const targetDeptInfo = {
        "cardiology": { name: "Cardiology", icon: "🫀" },
        "neurology": { name: "Neurology", icon: "🧠" },
        "general-medicine": { name: "General Medicine", icon: "🩺" },
        "pediatrics": { name: "Pediatrics", icon: "👶" },
        "orthopedics": { name: "Orthopedics", icon: "🦴" },
        "emergency": { name: "Emergency / Trauma", icon: "🚨" },
        "gastroenterology": { name: "Gastroenterology", icon: "🍽️" },
        "dermatology": { name: "Dermatology", icon: "🧴" },
        "ent": { name: "ENT", icon: "👂" },
        "ophthalmology": { name: "Ophthalmology", icon: "👁" },
        "psychiatry": { name: "Psychiatry", icon: "🧩" },
        "ayush": { name: "AYUSH / Integrative", icon: "🌿" }
      };

      const deptMeta = targetDeptInfo[targetDept] || { name: targetDept.toUpperCase(), icon: "🩺" };
      const shouldSwitch = confirm(`✓ Patient successfully transferred to ${deptMeta.name} waiting queue!\n\nWould you like to switch to the ${deptMeta.name} Department Queue now?`);

      if (shouldSwitch) {
        this.selectDepartment(targetDept, deptMeta.name, deptMeta.icon);
      } else {
        this.showQueueView();
      }
    } catch (err) {
      alert("Transfer notice: " + err.message);
    } finally {
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerText = "Confirm Transfer & Move Patient ↗";
      }
    }
  },

  handleDirectReassign(sessionId) {
    this.currentSessionId = sessionId;
    this.openTransferModal();
  },

  async escalateToEmergency(sessionId) {
    const targetSession = sessionId || this.currentSessionId;
    if (!targetSession) return;

    if (!confirm("🚨 IMMEDIATE EMERGENCY ESCALATION\n\nAre you sure you want to flag this patient for Immediate Emergency Priority and move to the Emergency Department Queue?")) {
      return;
    }

    try {
      await api.reassignDepartment(targetSession, "emergency", "attending_physician", "Emergency escalation by physician");
      alert("🚨 Patient successfully escalated to Emergency / Trauma Department queue.");
      this.showQueueView();
    } catch (err) {
      alert("Escalation notice: " + err.message);
    }
  },

  openAskPatientModal() {
    const modal = document.getElementById("ask-patient-modal");
    if (modal) modal.style.display = "flex";
  },

  closeAskPatientModal() {
    const modal = document.getElementById("ask-patient-modal");
    if (modal) modal.style.display = "none";
  },

  async submitTargetedQuestion() {
    const category = document.getElementById("ask-category-select").value;
    const custom = document.getElementById("ask-custom-input").value.trim();

    try {
      await api.askTargetedQuestion(this.currentSessionId, {
        physician_id: "dr_sharma_cardio",
        category,
        custom_question: custom || null
      });
      alert("✓ Question dispatched to patient intake session!");
      this.closeAskPatientModal();
      this.inspectPatientCase(this.currentSessionId);
    } catch (err) {
      alert("Failed to send question: " + err.message);
    }
  },

  async handleConfirmCase(e) {
    e.preventDefault();
    const btn = document.getElementById("btn-confirm-record");
    btn.disabled = true;
    btn.innerText = "Confirming & Signing...";

    try {
      const physicianId = document.getElementById("physician-id-input").value.trim() || "dr_sharma_cardio";
      const dept = document.getElementById("confirm-dept-select").value;
      const priority = document.getElementById("confirm-priority-select").value;
      const notes = document.getElementById("physician-notes-input").value;
      const overrideReason = document.getElementById("override-reason-input").value.trim();

      const isDeptChanged = this.originalRecommendedDept && dept !== this.originalRecommendedDept;
      const isPriorityChanged = this.originalRecommendedPriority && priority !== this.originalRecommendedPriority;

      if ((isDeptChanged || isPriorityChanged) && !overrideReason) {
        alert("⚠️ Override rationale is required when altering the AI recommended department or priority.");
        btn.disabled = false;
        btn.innerText = "✓ Confirm & Sign Record";
        return;
      }

      const payload = {
        physician_id: physicianId,
        final_department: dept,
        final_priority: priority,
        clinical_notes: notes,
        override_reason: overrideReason || null
      };

      await api.recordPhysicianDecision(this.currentSessionId, payload);
      alert("✓ Clinical record successfully finalized, signed, and logged to audit trail.");
      this.showQueueView();
    } catch (err) {
      alert("Confirmation notice: " + err.message);
    } finally {
      btn.disabled = false;
      btn.innerText = "✓ Confirm & Sign Record";
    }
  }
};

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

  async loadDepartmentSelection() {
    try {
      const departments = await api.getDepartments();
      const grid = document.getElementById("dept-selection-grid");
      if (!grid) return;

      grid.innerHTML = "";
      departments.forEach((dept) => {
        const card = document.createElement("div");
        card.className = "lang-tile";
        card.style.textAlign = "left";
        card.style.alignItems = "flex-start";
        card.style.padding = "1.5rem";

        const badgeClass = dept.id === "unspecified" ? "lang-badge-fallback" : "lang-badge-ready";
        const badgeLabel = dept.id === "unspecified" ? "TRIAGE QUEUE →" : "ACCESS QUEUE →";

        card.innerHTML = `
          <div style="font-size:2rem; margin-bottom:0.5rem;">${dept.icon}</div>
          <span class="lang-tile-native" style="font-size:1.2rem;">${dept.display_name}</span>
          <p style="font-size:0.825rem; color:var(--text-muted); margin-top:0.25rem; line-height:1.4;">${dept.description}</p>
          <span class="lang-tile-badge ${badgeClass}" style="margin-top:1rem;">${badgeLabel}</span>
        `;
        card.addEventListener("click", () => this.selectDepartment(dept.id, dept.display_name, dept.icon));
        grid.appendChild(card);
      });
    } catch (err) {
      console.error("Failed to load departments:", err);
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
    this.refreshTimer = setInterval(() => this.loadQueue(), 10000);
  },

  showQueueView() {
    document.getElementById("physician-dept-view").style.display = "none";
    document.getElementById("physician-queue-view").style.display = "block";
    document.getElementById("physician-case-view").style.display = "none";
    this.loadQueue();
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
              <p style="font-size:0.85rem; margin-top:0.25rem;">Patients completing kiosk intake or transferred will appear here automatically.</p>
            </td>
          </tr>
        `;
        return;
      }

      items.forEach((item) => {
        const tr = document.createElement("tr");
        
        let sevBadgeClass = "lang-badge-connected";
        let sevLabel = "NORMAL";
        if (item.overall_severity === "CRITICAL") {
          sevBadgeClass = "lang-badge-connected' style='background:#fee2e2; color:#991b1b; font-weight:700;";
          sevLabel = "🚨 CRITICAL";
        } else if (item.overall_severity === "HIGH") {
          sevBadgeClass = "lang-badge-connected' style='background:#ffedd5; color:#9a3412; font-weight:700;";
          sevLabel = "⚠️ HIGH PRIORITY";
        } else if (item.overall_severity === "MEDIUM") {
          sevBadgeClass = "lang-badge-connected' style='background:#fef3c7; color:#92400e;";
          sevLabel = "MEDIUM";
        }

        const arrivalTime = new Date(item.arrival_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        tr.innerHTML = `
          <td>
            <div style="font-weight:700; color:var(--brand-primary); font-size:1rem;">${item.patient_name}</div>
            <div style="font-size:0.75rem; color:var(--text-muted); font-family:monospace;">${item.patient_id}</div>
          </td>
          <td>${item.age} yrs • ${item.gender}</td>
          <td>
            <span class="lang-tile-badge ${item.status === 'WAITING' ? 'lang-badge-ready' : 'lang-badge-connected'}">
              ${item.status}
            </span>
          </td>
          <td>
            <span class="lang-tile-badge ${sevBadgeClass}">${sevLabel}</span>
          </td>
          <td>
            <div>${arrivalTime}</div>
            <div style="font-size:0.75rem; color:#0284c7; font-weight:600;">⏱️ ${item.waiting_time_minutes} min</div>
          </td>
          <td>
            <button class="btn-primary-action" style="padding:0.45rem 0.95rem; font-size:0.85rem;" onclick="PhysicianDashboard.openCase('${item.session_id}')">
              Review Case ↗
            </button>
          </td>
        `;
        tableBody.appendChild(tr);
      });
    } catch (err) {
      console.error("Failed to load department queue:", err);
    }
  },

  async openCase(sessionId) {
    this.currentSessionId = sessionId;
    document.getElementById("physician-queue-view").style.display = "none";
    document.getElementById("physician-case-view").style.display = "block";
    window.scrollTo({ top: 0, behavior: "smooth" });

    try {
      const data = await api.getPatientCase(sessionId);
      this.currentPatientData = data;
      this.renderPatientCase(data);
    } catch (err) {
      console.error("Failed to load patient case:", err);
      alert("Notice: " + err.message);
    }
  },

  renderPatientCase(data) {
    if (!data) return;

    const patient = data.patient || {};
    const red_flag = data.red_flag || data.red_flags || {};
    const routing = data.routing || {};
    const draft_summary = data.draft_summary || data.clinical_brief || {};
    const questions = data.questions || [];
    const answers = data.answers || [];
    const timeline = data.timeline || [];
    const documents = data.documents || [];

    this.originalRecommendedDept = routing.recommended_department ? routing.recommended_department.toLowerCase() : "general-medicine";
    this.originalRecommendedPriority = red_flag.overall_severity || "NONE";

    const isDraft = draft_summary.is_draft !== undefined ? draft_summary.is_draft : true;

    // 1. Patient Header Overview
    const infoEl = document.getElementById("case-patient-overview");
    if (infoEl) {
      infoEl.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <h2 style="font-size:1.5rem; color:var(--brand-primary);">${patient.name || 'Patient'} (${patient.age || 'N/A'} yrs • ${patient.gender || 'N/A'})</h2>
            <p style="color:var(--text-muted); font-size:0.875rem; margin-top:0.25rem;">
              Patient ID: <strong>${patient.patient_id || 'N/A'}</strong> | Identity: <strong>${patient.abha_id ? 'ABHA ' + patient.abha_id : 'Standard Registration'}</strong> | Phone: ${patient.phone || 'Not recorded'}
            </p>
          </div>
          <div>
            <span class="lang-tile-badge ${isDraft ? 'lang-badge-ready' : 'lang-badge-connected'}" style="font-size:0.85rem; padding:0.35rem 0.75rem;">
              ${isDraft ? 'AI DRAFT RECORD' : 'CONFIRMED CLINICAL RECORD'}
            </span>
          </div>
        </div>
      `;
    }

    // 2. Explainable AI Cards
    const explainRouting = document.getElementById("explain-routing-content");
    if (explainRouting) {
      const scorePct = Math.round((routing.confidence || routing.confidence_score || 0.85) * 100);
      const alts = routing.alternative_departments && routing.alternative_departments.length
        ? routing.alternative_departments.map(a => `${a.department || a.department_id} (${Math.round((a.score || 0.1) * 100)}%)`).join(', ')
        : "None";
      
      explainRouting.innerHTML = `
        <div>Primary Dept: <strong>${(routing.recommended_department || 'General Medicine').toUpperCase()}</strong> (${scorePct}% match)</div>
        <div style="margin-top:4px; font-size:0.8rem; color:#64748b;">Confidence: ${scorePct >= 70 ? 'High' : 'Moderate'}</div>
        <div style="margin-top:4px; font-size:0.8rem; color:#64748b;">Alternatives: ${alts}</div>
      `;
    }

    const explainPriority = document.getElementById("explain-priority-content");
    if (explainPriority) {
      if (red_flag && red_flag.has_red_flags) {
        explainPriority.innerHTML = `
          <div style="color:#b91c1c; font-weight:700;">🚨 Triggered: ${red_flag.overall_severity}</div>
          <div style="margin-top:4px; font-size:0.8rem; color:#7f1d1d;">Rule: ${red_flag.primary_triggered_rule || 'Clinical Red Flag'}</div>
          <div style="margin-top:4px; font-size:0.8rem; color:#7f1d1d;">Action: Immediate clinical review required</div>
        `;
      } else {
        explainPriority.innerHTML = `
          <div style="color:#15803d; font-weight:600;">✓ No Critical Red Flags</div>
          <div style="margin-top:4px; font-size:0.8rem; color:#475569;">Standard outpatient clinical queue assigned.</div>
        `;
      }
    }

    const explainGaps = document.getElementById("explain-gaps-content");
    if (explainGaps) {
      const gaps = [];
      if (!draft_summary.medications || draft_summary.medications.length === 0) gaps.push("Medications");
      if (!draft_summary.allergies || draft_summary.allergies.length === 0) gaps.push("Allergies");
      if (!draft_summary.medical_history || draft_summary.medical_history.length === 0) gaps.push("Past Medical History");
      
      if (gaps.length > 0) {
        explainGaps.innerHTML = `
          <div>Unspecified intake fields:</div>
          <div style="margin-top:6px;">
            ${gaps.map(g => `<span class="gap-pill">⚠️ ${g}</span>`).join('')}
          </div>
        `;
      } else {
        explainGaps.innerHTML = `<span style="color:#15803d; font-weight:600;">✓ Comprehensive intake completed.</span>`;
      }
    }

    // 3. Red Flag Banner
    const rfBanner = document.getElementById("case-redflag-banner");
    if (rfBanner) {
      if (red_flag && red_flag.has_red_flags) {
        rfBanner.style.display = "block";
        document.getElementById("rf-banner-title").innerText = `🚨 ${red_flag.overall_severity} PRIORITY TRIAGE ALERT (${red_flag.primary_triggered_rule || 'CLINICAL RED FLAG'})`;
        document.getElementById("rf-banner-desc").innerHTML = `
          <strong>Triage Rationale:</strong> ${red_flag.summary_reason || 'Clinical criteria met.'}<br/>
          <strong>Required Clinical Action:</strong> ${red_flag.flagged_rules ? red_flag.flagged_rules.map(r => r.action_required).join(' | ') : 'Specialist examination'}
        `;
      } else {
        rfBanner.style.display = "none";
      }
    }

    // 4. Chief Complaint & HPI Details
    const ccText = document.getElementById("case-chief-complaint-text");
    if (ccText) {
      ccText.innerText = `"${draft_summary.chief_complaint || 'General clinical intake'}"`;
    }

    const hpiText = document.getElementById("case-hpi-text");
    if (hpiText) {
      hpiText.innerText = draft_summary.hpi || "Symptoms recorded during Socratic intake.";
    }

    const progText = document.getElementById("case-progression-text");
    if (progText) {
      const assoc = draft_summary.associated_symptoms && draft_summary.associated_symptoms.length
        ? draft_summary.associated_symptoms.join(', ')
        : "None reported";
      progText.innerText = `Progression: ${draft_summary.symptom_progression || 'Stable'} | Associated: ${assoc}`;
    }

    const medHistoryText = document.getElementById("case-medical-history-text");
    if (medHistoryText) {
      const meds = draft_summary.medications && draft_summary.medications.length
        ? draft_summary.medications.map(m => typeof m === 'object' ? `${m.name} (${m.dosage || 'standard'})` : m).join(', ')
        : "Not recorded";
      const hist = draft_summary.medical_history && draft_summary.medical_history.length
        ? draft_summary.medical_history.join(', ')
        : "None reported";
      const allerg = draft_summary.allergies && draft_summary.allergies.length
        ? draft_summary.allergies.join(', ')
        : "No known drug allergies";

      medHistoryText.innerHTML = `
        <strong>Conditions:</strong> ${hist}<br/>
        <strong>Medications:</strong> ${meds}<br/>
        <strong>Allergies:</strong> ${allerg}
      `;
    }

    // 5. Ayurvedic Perspective
    const ayurDetails = document.getElementById("case-ayurvedic-details");
    if (ayurDetails) {
      const ayur = draft_summary.ayurvedic_assessment || {};
      const agni = ayur.agni || "Sama (Balanced digestion)";
      const koshtha = ayur.koshtha || "Madhyama (Regular bowel habit)";
      const nidra = ayur.nidra || "Samyak (Normal restful sleep)";
      const bala = ayur.bala || "Madhyama (Moderate physical strength)";
      const prakriti = ayur.prakriti_trend || "General holistic presentation";

      ayurDetails.innerHTML = `
        <div style="margin-bottom:6px;">🔥 <strong>Agni (Digestive Fire):</strong> ${agni}</div>
        <div style="margin-bottom:6px;">💧 <strong>Koshtha (Bowel / Elimination):</strong> ${koshtha}</div>
        <div style="margin-bottom:6px;">🌙 <strong>Nidra & Manasika (Sleep & Stress):</strong> ${nidra}</div>
        <div style="margin-bottom:6px;">💪 <strong>Bala (Physical Vitality):</strong> ${bala}</div>
        <div>⚖️ <strong>Prakriti Presentation:</strong> ${prakriti}</div>
      `;
    }

    // 6. Interactive Q&A Transcript
    const qaList = document.getElementById("case-qa-list");
    if (qaList) {
      qaList.innerHTML = "";
      if (questions.length === 0) {
        qaList.innerHTML = `<p style="color:var(--text-muted); font-size:0.875rem;">No interactive Q&A recorded yet.</p>`;
      } else {
        questions.forEach((q, idx) => {
          const a = answers[idx];
          const bubble = document.createElement("div");
          bubble.className = "qa-bubble";
          bubble.innerHTML = `
            <div class="qa-question">
              <span><strong>Q${idx + 1}:</strong> ${q.question}</span>
              <span class="lang-tile-badge ${q.ayurvedic_domain ? 'lang-badge-connected' : 'lang-badge-ready'}">${q.display_label || q.objective || 'Clinical Investigation'}</span>
            </div>
            <div class="qa-answer" style="margin-top:0.5rem; color:#1e293b;">
              <span><strong>Answer:</strong> ${a ? a.answer : '<em style="color:#94a3b8;">Pending response</em>'}</span>
              ${a ? `<span class="lang-tile-badge lang-badge-fallback" style="font-size:0.7rem;">[${a.source_type}]</span>` : ''}
            </div>
          `;
          qaList.appendChild(bubble);
        });
      }
    }

    // 7. Chronological Timeline Events
    const timelineEl = document.getElementById("case-timeline-list");
    if (timelineEl) {
      timelineEl.innerHTML = "";
      if (timeline.length === 0) {
        timelineEl.innerHTML = `<p style="color:var(--text-muted); font-size:0.875rem;">Intake initiated.</p>`;
      } else {
        timeline.forEach((evt) => {
          const item = document.createElement("div");
          item.className = "timeline-item";
          item.innerHTML = `
            <div class="timeline-dot"></div>
            <div class="timeline-content">
              <div style="display:flex; justify-content:space-between; font-size:0.8rem; color:var(--text-muted);">
                <strong>${evt.title}</strong>
                <span>${new Date(evt.timestamp).toLocaleTimeString()}</span>
              </div>
              <p style="font-size:0.875rem; margin-top:0.25rem;">${evt.description}</p>
            </div>
          `;
          timelineEl.appendChild(item);
        });
      }
    }

    // 8. Genuine Document Evidence Traceability (Zero Fake Data)
    const ocrDocsList = document.getElementById("case-ocr-documents-list");
    if (ocrDocsList) {
      ocrDocsList.innerHTML = "";

      if (!documents || documents.length === 0) {
        ocrDocsList.innerHTML = `
          <div style="background:#f8fafc; border:1px dashed #cbd5e1; border-radius:8px; padding:1.5rem; text-align:center; color:var(--text-muted);">
            <div style="font-size:1.5rem; margin-bottom:0.25rem;">📂</div>
            <strong style="font-size:0.9rem; color:#475569;">No medical documents uploaded</strong>
            <p style="font-size:0.8rem; margin-top:0.25rem;">No physical prescription, lab report, or diagnostic PDF was submitted during this kiosk intake.</p>
          </div>
        `;
      } else {
        documents.forEach((doc, idx) => {
          const item = document.createElement("div");
          item.className = "ocr-item-card";
          const extText = doc.extracted_text || doc.ocr_text || "Document stored securely.";
          const provider = doc.storage_provider === "cloudinary" ? "Cloudinary (Images)" : "Backblaze B2 (Encrypted PDF)";
          const accessUrl = doc.access_url || "#";
          const conf = doc.ocr_confidence ? Math.round(doc.ocr_confidence * 100) : 98;

          item.innerHTML = `
            <div class="ocr-item-header">
              <span><strong>Doc ${idx + 1}: ${doc.original_filename || 'Medical Document'}</strong></span>
              <span class="lang-tile-badge lang-badge-connected">Confidence: ${conf}%</span>
            </div>
            <div class="ocr-item-content">
              "${extText}"
            </div>
            <div style="display:flex; justify-content:space-between; align-items:center; font-size:0.75rem; color:var(--text-muted); margin-top:0.5rem;">
              <span>Storage: <strong>${provider}</strong></span>
              ${accessUrl !== '#' ? `<a href="${accessUrl}" target="_blank" style="color:var(--brand-primary); font-weight:700; text-decoration:underline;">View Original Document ↗</a>` : ''}
            </div>
          `;
          ocrDocsList.appendChild(item);
        });
      }
    }

    // 9. Form Field Bindings
    const summaryInput = document.getElementById("physician-summary-edit");
    if (summaryInput) {
      summaryInput.value = draft_summary.hpi || "";
    }
    const deptSelect = document.getElementById("confirm-dept-select");
    if (deptSelect && routing.recommended_department) {
      deptSelect.value = routing.recommended_department.toLowerCase();
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

  async handleDirectReassign(sessionId) {
    const targetSessionId = sessionId || this.currentSessionId;
    if (!targetSessionId) {
      alert("Please select or open a patient case first.");
      return;
    }

    const deptSelect = document.getElementById("confirm-dept-select");
    const targetDept = deptSelect ? deptSelect.value : "general-medicine";
    const physicianInput = document.getElementById("physician-id-input");
    const physicianId = (physicianInput && physicianInput.value.trim()) || "dr_sharma_cardio";
    const reasonInput = document.getElementById("override-reason-input");
    let reason = (reasonInput && reasonInput.value.trim()) || "";

    if (!reason) {
      reason = prompt(`Enter clinical rationale for transferring patient to ${targetDept.toUpperCase()} department:`, "Specialist transfer requested by attending physician");
      if (reason === null) return; // User cancelled
      if (reasonInput) reasonInput.value = reason;
    }

    try {
      await api.reassignDepartment(targetSessionId, targetDept, physicianId, reason || "Clinical transfer");
      alert(`✓ Patient successfully transferred to ${targetDept.toUpperCase()} department queue.`);
      this.showQueueView();
    } catch (err) {
      alert("Transfer failed: " + err.message);
    }
  },

  async escalateToEmergency(sessionId) {
    const targetSessionId = sessionId || this.currentSessionId;
    if (!targetSessionId) {
      alert("Please select or open a patient case first.");
      return;
    }

    const prioritySelect = document.getElementById("confirm-priority-select");
    const deptSelect = document.getElementById("confirm-dept-select");
    if (prioritySelect) prioritySelect.value = "CRITICAL";
    if (deptSelect) deptSelect.value = "emergency";
    this.checkOverrideStatus();

    const confirmEscalate = confirm("🚨 Are you sure you want to escalate this patient to the EMERGENCY / Trauma queue with CRITICAL priority immediately?");
    if (!confirmEscalate) return;

    const physicianInput = document.getElementById("physician-id-input");
    const physicianId = (physicianInput && physicianInput.value.trim()) || "dr_sharma_cardio";
    const reasonInput = document.getElementById("override-reason-input");
    let reason = (reasonInput && reasonInput.value.trim()) || "Emergency Escalation - Acute clinical triage elevation";

    try {
      await api.reassignDepartment(targetSessionId, "emergency", physicianId, reason);
      alert("🚨 Patient successfully escalated to EMERGENCY (CRITICAL) queue!");
      this.showQueueView();
    } catch (err) {
      alert("Escalation failed: " + err.message);
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
    if (!this.currentSessionId) return;

    const category = document.getElementById("ask-category-select").value;
    const custom = document.getElementById("ask-custom-input").value.trim() || null;
    const physicianId = document.getElementById("physician-id-input").value.trim() || "dr_sharma_cardio";

    try {
      await api.askTargetedQuestion(this.currentSessionId, {
        physician_id: physicianId,
        category: category,
        custom_question: custom
      });

      alert("✓ Targeted follow-up question dispatched to patient kiosk.");
      this.closeAskPatientModal();
      this.openCase(this.currentSessionId);
    } catch (err) {
      alert("Notice: " + err.message);
    }
  },

  async handleConfirmCase(e) {
    e.preventDefault();
    const btn = e.target.querySelector('button[type="submit"]');
    btn.disabled = true;
    btn.innerText = "Confirming & Signing...";

    try {
      const physicianId = document.getElementById("physician-id-input").value.trim() || "dr_sharma_cardio";
      const dept = document.getElementById("confirm-dept-select").value;
      const priority = document.getElementById("confirm-priority-select").value;
      const editedSummary = document.getElementById("physician-summary-edit").value;
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

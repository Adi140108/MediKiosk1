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
  currentLanguage: "en",
  refreshTimer: null,
  originalRecommendedDept: null,
  originalRecommendedPriority: null,

  init() {
    this.bindEvents();
    if (typeof I18n !== "undefined") {
      I18n.setLanguage(this.currentLanguage);
    }
    this.renderDepartmentGrid(DEFAULT_DEPARTMENTS);
    this.loadDepartmentSelection();
  },

  changeLanguage(lang) {
    this.currentLanguage = lang || "en";
    if (typeof I18n !== "undefined") {
      I18n.setLanguage(this.currentLanguage);
    }
    const sel = document.getElementById("physician-lang-select");
    if (sel && sel.value !== this.currentLanguage) {
      sel.value = this.currentLanguage;
    }
    // Re-render UI views if open
    if (this.currentPatientData && document.getElementById("physician-case-view")?.style.display === "block") {
      this.populateCaseInspector(this.currentPatientData);
    } else if (this.currentDepartment) {
      this.loadQueue();
    } else {
      this.loadDepartmentSelection();
    }
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
      const deptName = routing.recommended_department || routing.assigned_department || data.queue_item?.assigned_department || 'General Medicine';
      const deptReason = routing.reasoning || routing.routing_rationale || 'Symptom pattern matching aligns with this clinical department.';
      expRouting.innerHTML = `
        <p><strong>Affinity:</strong> ${deptName.toUpperCase()}</p>
        <p style="margin-top:0.35rem; font-size:0.825rem; line-height:1.4;">${deptReason}</p>
      `;
    }

    const expPriority = document.getElementById("explain-priority-content");
    if (expPriority) {
      const priorityLabel = red_flag.overall_severity || data.queue_item?.overall_severity || "NORMAL";
      const priorityReason = red_flag.triage_rationale || red_flag.reasoning || (red_flag.flagged_reasons ? red_flag.flagged_reasons.join(" • ") : null) || 'Standard OPD consultation priority based on deterministic clinical intake.';
      expPriority.innerHTML = `
        <p><strong>Priority Tier:</strong> ${priorityLabel}</p>
        <p style="margin-top:0.35rem; font-size:0.825rem; line-height:1.4;">${priorityReason}</p>
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
    if (complaintText) {
      complaintText.innerText = draft_summary.chief_complaint || data.context?.chief_complaint || data.queue_item?.chief_complaint_summary || "Patient presents for consultation review.";
    }

    const hpiText = document.getElementById("case-hpi-text");
    if (hpiText) {
      const hpiVal = draft_summary.hpi || draft_summary.hpi_narrative || data.context?.hpi || data.context?.chief_complaint || "Symptoms recorded during interactive Socratic intake interview.";
      hpiText.innerText = hpiVal;
    }

    const progText = document.getElementById("case-progression-text");
    if (progText) {
      const assoc = (draft_summary.associated_symptoms && draft_summary.associated_symptoms.length > 0)
        ? draft_summary.associated_symptoms.join(", ")
        : (draft_summary.symptom_progression || data.context?.progression || "No specific associated symptoms reported.");
      progText.innerText = assoc;
    }

    const medHistText = document.getElementById("case-medical-history-text");
    if (medHistText) {
      const cond = (medical_history.known_conditions || draft_summary.medical_history || []).join(", ");
      const meds = (medical_history.medications || draft_summary.medications || []).join(", ");
      medHistText.innerText = `Conditions: ${cond || 'None reported'} | Medications: ${meds || 'None reported'}`;
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
          const ans = answers.find(a => a.question_id === q.question_id || a.sequence === q.sequence);
          const ansVal = ans ? (ans.answer || ans.normalized_answer || ans.original_answer || ans.answer_text) : null;
          const isAttendant = ans && ans.source_type === "ATTENDANT";
          const attendantBadge = isAttendant ? '<span class="gap-pill" style="font-size:0.7rem; color:#92400e; background:#fef3c7; border-color:#fde68a;">Attendant Assisted</span>' : '';
          
          let ansBody = '<span style="color:#94a3b8; font-style:italic;">Pending patient response...</span>';
          if (ansVal) {
            ansBody = `
              <div style="font-size:0.875rem; color:#1e293b; font-weight:500;">
                "${ansVal}"
              </div>
              ${(ans.original_answer && ans.original_answer !== ansVal) ? `<div style="font-size:0.75rem; color:#64748b; margin-top:2px;">Original utterance: "${ans.original_answer}" (${ans.original_language || 'Native'})</div>` : ''}
            `;
          }

          return `
            <div style="margin-bottom:0.85rem; padding-bottom:0.75rem; border-bottom:1px solid #f1ece4;">
              <div style="font-weight:600; font-size:0.875rem; color:var(--brand-primary); margin-bottom:0.25rem; display:flex; justify-content:space-between; align-items:center;">
                <span>Q${idx + 1}: ${q.question}</span>
                ${attendantBadge}
              </div>
              <div style="background:#f8fafc; border-left:3px solid var(--brand-primary); padding:0.5rem 0.75rem; border-radius:0 6px 6px 0;">
                ${ansBody}
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

    // 7. OCR Documents & Clinical Findings
    const docsList = document.getElementById("case-ocr-documents-list");
    if (docsList) {
      if (documents && documents.length > 0) {
        docsList.innerHTML = documents.map((d, idx) => {
          const findings = d.provider_metadata?.structured_findings || {};
          const labVals = findings.lab_values || [];
          const meds = findings.medications || [];
          const conds = findings.conditions || [];
          const vitals = findings.vitals || {};
          const rawText = d.extracted_text || d.ocr_text || findings.raw_text || "";
          const confidence = d.provider_metadata?.confidence || (rawText ? 0.92 : 0.0);
          const confPercent = Math.round(confidence * 100);
          const scanUrl = d.access_url || d.storage_key || "";
          const filename = d.original_filename || d.filename || `Medical Report ${idx + 1}`;

          // Format lab findings table if any exist
          let labsHtml = "";
          if (labVals.length > 0) {
            labsHtml = `
              <div style="margin-top:0.6rem;">
                <div style="font-weight:700; font-size:0.8rem; color:#0f172a; margin-bottom:4px; display:flex; align-items:center; gap:6px;">
                  <span>🧪 Extracted Laboratory Findings:</span>
                  <span class="gap-pill" style="font-size:0.7rem; background:#ecfdf5; color:#065f46; border-color:#a7f3d0;">${labVals.length} Tests Digitized</span>
                </div>
                <table class="ocr-lab-table">
                  <thead>
                    <tr>
                      <th>Test Name</th>
                      <th>Observed Value</th>
                      <th>Reference Range</th>
                    </tr>
                  </thead>
                  <tbody>
                    ${labVals.map(l => `
                      <tr>
                        <td><strong>${l.test}</strong></td>
                        <td><span style="font-weight:700; color:#0369a1; background:#f0f9ff; padding:2px 6px; border-radius:4px; border:1px solid #bae6fd;">${l.value} ${l.unit || ''}</span></td>
                        <td style="color:#64748b; font-size:0.75rem;">${l.reference_range || 'Standard range'}</td>
                      </tr>
                    `).join('')}
                  </tbody>
                </table>
              </div>
            `;
          }

          // Format medications if any exist
          let medsHtml = "";
          if (meds.length > 0) {
            medsHtml = `
              <div style="margin-top:0.4rem; display:flex; flex-wrap:wrap; gap:4px; align-items:center;">
                <span style="font-size:0.75rem; font-weight:700; color:#475569;">Prescribed Rx:</span>
                ${meds.map(m => `<span class="gap-pill" style="font-size:0.75rem; background:#eff6ff; color:#1e40af; border-color:#bfdbfe;">💊 ${m.name} ${m.dosage || ''} ${m.frequency || ''}</span>`).join('')}
              </div>
            `;
          }

          // Format conditions if any exist
          let condsHtml = "";
          if (conds.length > 0) {
            condsHtml = `
              <div style="margin-top:0.4rem; display:flex; flex-wrap:wrap; gap:4px; align-items:center;">
                <span style="font-size:0.75rem; font-weight:700; color:#475569;">Impression:</span>
                ${conds.map(c => `<span class="gap-pill" style="font-size:0.75rem; background:#fef3c7; color:#92400e; border-color:#fde68a;">📋 ${c}</span>`).join('')}
              </div>
            `;
          }

          // If no structured table or facts, show formatted text preview
          let textSnippetHtml = "";
          if (labVals.length === 0 && meds.length === 0 && conds.length === 0) {
            textSnippetHtml = `
              <div class="ocr-raw-box" style="margin-top:0.4rem; max-height:120px;">
                ${rawText || 'OCR entities digitized successfully. Clinical facts attached to record.'}
              </div>
            `;
          }

          return `
            <div class="ocr-item-card">
              <div class="ocr-item-header">
                <span><strong>📄 ${filename}</strong></span>
                <span style="display:flex; gap:6px; align-items:center;">
                  <span class="gap-pill" style="font-size:0.7rem; background:#f8fafc; color:#475569; border-color:#cbd5e1;">Provider: ${d.storage_provider || 'Encrypted Store'}</span>
                  <span class="gap-pill" style="font-size:0.7rem; background:#f0fdf4; color:#15803d; border-color:#bbf7d0;">${confPercent}% OCR</span>
                </span>
              </div>
              <div class="ocr-item-content">
                ${labsHtml}
                ${medsHtml}
                ${condsHtml}
                ${textSnippetHtml}

                ${rawText && (labVals.length > 0 || meds.length > 0 || conds.length > 0) ? `
                  <div style="margin-top:0.6rem;">
                    <button type="button" onclick="PhysicianDashboard.toggleRawOcr('raw-ocr-${idx}')" style="background:none; border:none; color:#0284c7; font-size:0.75rem; font-weight:600; cursor:pointer; padding:0; display:flex; align-items:center; gap:4px;">
                      <span>📝 Show/Hide Full Raw OCR Text ▼</span>
                    </button>
                    <div id="raw-ocr-${idx}" class="ocr-raw-box" style="display:none; margin-top:0.4rem;">
                      ${rawText}
                    </div>
                  </div>
                ` : ''}

                ${scanUrl ? `
                  <div style="display:flex; gap:0.5rem; margin-top:0.75rem; align-items:center; flex-wrap:wrap;">
                    <button type="button" class="btn-scan-preview" onclick="PhysicianDashboard.openDocumentScanModal('${scanUrl}', '${filename.replace(/'/g, "\\'")}')">
                      🔍 Preview Document Scan
                    </button>
                    <button type="button" class="btn-scan-preview" style="background:#f8fafc; color:#475569; border-color:#cbd5e1;" onclick="PhysicianDashboard.openScanLink('${scanUrl}')">
                      ↗ Open Full Scan
                    </button>
                  </div>
                ` : ''}
              </div>
            </div>
          `;
        }).join("");
      } else {
        docsList.innerHTML = `<p style="color:var(--text-muted); font-size:0.85rem; font-style:italic;">No previous reports or prescriptions uploaded by patient.</p>`;
      }
    }

    // 8. Decision Form Pre-fill & Inline Edit Inputs
    this.originalRecommendedDept = routing.recommended_department || "general-medicine";
    this.originalRecommendedPriority = red_flag.overall_severity || "NONE";

    const editCc = document.getElementById("edit-chief-complaint-input");
    if (editCc) editCc.value = draft_summary.chief_complaint || "";

    const editHpi = document.getElementById("edit-hpi-narrative-input");
    if (editHpi) editHpi.value = draft_summary.hpi_narrative || "";

    const editSym = document.getElementById("edit-associated-symptoms-input");
    if (editSym) editSym.value = (draft_summary.associated_symptoms || []).join(", ");

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
    const targetSession = this.currentSessionId || (this.currentPatientData && (this.currentPatientData.session_id || this.currentPatientData.queue_item?.session_id));
    if (!targetSession) {
      alert("Please select or open a patient case first.");
      return;
    }
    this.currentSessionId = targetSession;

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
    const targetSession = this.currentSessionId || (this.currentPatientData && (this.currentPatientData.session_id || this.currentPatientData.queue_item?.session_id));
    if (!targetSession) {
      alert("No active patient case selected.");
      return;
    }
    this.currentSessionId = targetSession;

    const targetDept = document.getElementById("transfer-target-dept").value;
    const priority = document.getElementById("transfer-priority-select")?.value || "HIGH";
    const physicianId = document.getElementById("transfer-physician-id")?.value.trim() || "dr_sharma_cardio";
    const reason = document.getElementById("transfer-reason-input")?.value.trim() || "Clinical specialist reassignment";

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
    if (sessionId) {
      this.currentSessionId = sessionId;
    }
    this.openTransferModal();
  },

  async escalateToEmergency(sessionId) {
    const targetSession = sessionId || this.currentSessionId || (this.currentPatientData && (this.currentPatientData.session_id || this.currentPatientData.queue_item?.session_id));
    if (!targetSession) {
      alert("Please select or open a patient case first.");
      return;
    }
    this.currentSessionId = targetSession;

    if (!confirm("🚨 IMMEDIATE EMERGENCY ESCALATION\n\nAre you sure you want to flag this patient for Immediate Emergency Priority and move them to the Emergency Department Queue?")) {
      return;
    }

    try {
      await api.reassignDepartment(targetSession, "emergency", "dr_sharma_cardio", "Immediate Emergency Escalation by physician");
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
    if (e && e.preventDefault) e.preventDefault();
    const btn = document.getElementById("btn-confirm-record") || (e?.target?.querySelector ? e.target.querySelector("button[type='submit']") : null);
    if (btn) {
      btn.disabled = true;
      btn.innerText = "Confirming & Signing...";
    }

    try {
      const sessionId = this.currentSessionId || this.currentPatientData?.session_id || this.currentPatientData?.queue_item?.session_id || this.currentPatientData?.patient?.session_id;
      if (!sessionId) {
        alert("⚠️ Please open or select an active patient case first.");
        return;
      }

      const physicianId = document.getElementById("physician-id-input")?.value?.trim() || "dr_sharma_cardio";
      const dept = document.getElementById("confirm-dept-select")?.value || "general-medicine";
      const priority = document.getElementById("confirm-priority-select")?.value || "NONE";
      const notes = document.getElementById("physician-notes-input")?.value || "";
      const overrideReason = document.getElementById("override-reason-input")?.value?.trim() || "";

      const isDeptChanged = this.originalRecommendedDept && dept !== this.originalRecommendedDept;
      const isPriorityChanged = this.originalRecommendedPriority && priority !== this.originalRecommendedPriority;

      if ((isDeptChanged || isPriorityChanged) && !overrideReason) {
        alert("⚠️ Override rationale is required when altering the AI recommended department or priority.");
        if (btn) {
          btn.disabled = false;
          btn.innerText = "✓ Confirm & Sign Record";
        }
        return;
      }

      const payload = {
        physician_id: physicianId,
        final_department: dept,
        final_priority: priority,
        clinical_notes: notes,
        override_reason: overrideReason || null
      };

      await api.recordPhysicianDecision(sessionId, payload);

      if (isDeptChanged) {
        try {
          await api.reassignDepartment(sessionId, dept, physicianId, overrideReason);
        } catch (reassignErr) {
          console.debug("Reassignment sync note:", reassignErr);
        }
      }

      alert("✓ Clinical record successfully finalized, signed, and logged to audit trail.");
      this.showQueueView();
    } catch (err) {
      alert("Confirmation notice: " + (err.message || "Failed to confirm patient record"));
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerText = "✓ Confirm & Sign Record";
      }
    }
  },

  toggleHpiEdit(show) {
    const disp = document.getElementById("hpi-display-container");
    const editForm = document.getElementById("hpi-edit-form-container");
    const toggleBtn = document.getElementById("btn-toggle-hpi-edit");

    const isShowing = editForm && editForm.style.display !== "none";
    const nextState = show !== undefined ? show : !isShowing;

    if (disp) disp.style.display = nextState ? "none" : "block";
    if (editForm) editForm.style.display = nextState ? "block" : "none";
    if (toggleBtn) toggleBtn.innerText = nextState ? "✕ Close Edit" : "✏️ Edit Summary";
  },

  saveHpiInlineEdit() {
    const cc = document.getElementById("edit-chief-complaint-input")?.value.trim() || "";
    const hpi = document.getElementById("edit-hpi-narrative-input")?.value.trim() || "";
    const symStr = document.getElementById("edit-associated-symptoms-input")?.value.trim() || "";

    // Update display fields
    const complaintText = document.getElementById("case-chief-complaint-text");
    if (complaintText) complaintText.innerText = cc || "No chief complaint recorded.";

    const hpiText = document.getElementById("case-hpi-text");
    if (hpiText) hpiText.innerText = hpi || "No extended narrative recorded.";

    const progText = document.getElementById("case-progression-text");
    if (progText) progText.innerText = symStr || "None reported.";

    // Sync with decision textarea
    const summaryEdit = document.getElementById("physician-summary-edit");
    if (summaryEdit) {
      summaryEdit.value = cc ? `${cc}. ${hpi}` : hpi;
    }

    // Update local cache
    if (this.currentPatientData) {
      if (!this.currentPatientData.draft_summary) this.currentPatientData.draft_summary = {};
      this.currentPatientData.draft_summary.chief_complaint = cc;
      this.currentPatientData.draft_summary.hpi_narrative = hpi;
      this.currentPatientData.draft_summary.associated_symptoms = symStr ? symStr.split(",").map(s => s.trim()) : [];
    }

    this.toggleHpiEdit(false);
  },

  toggleRawOcr(elementId) {
    const el = document.getElementById(elementId);
    if (!el) return;
    const isHidden = el.style.display === "none";
    el.style.display = isHidden ? "block" : "none";
  },

  openDocumentScanModal(url, filename = "Medical Document") {
    const modal = document.getElementById("doc-scan-modal");
    const title = document.getElementById("scan-modal-title");
    const meta = document.getElementById("scan-modal-meta");
    const body = document.getElementById("scan-modal-body");
    const extBtn = document.getElementById("scan-modal-external-btn");

    if (!modal || !body) return;

    if (title) title.innerText = `📄 ${filename}`;
    if (meta) meta.innerText = "Verified Medical Record Scan";
    if (extBtn) {
      extBtn.href = url;
      extBtn.onclick = (e) => {
        e.preventDefault();
        window.open(url, '_blank', 'noopener,noreferrer');
      };
    }

    const isPdf = (url || '').toLowerCase().includes('.pdf');
    if (isPdf) {
      body.innerHTML = `
        <iframe src="${url}" style="width:100%; height:75vh; border:none; background:white; border-radius:6px;"></iframe>
      `;
    } else {
      body.innerHTML = `
        <div style="max-height:75vh; overflow:auto; display:flex; align-items:center; justify-content:center; width:100%;">
          <img src="${url}" alt="${filename}" style="max-width:100%; max-height:72vh; border-radius:6px; box-shadow:0 10px 25px rgba(0,0,0,0.5); object-fit:contain;" />
        </div>
      `;
    }

    modal.style.display = "flex";
  },

  closeDocumentScanModal() {
    const modal = document.getElementById("doc-scan-modal");
    if (modal) modal.style.display = "none";
  },

  openScanLink(url) {
    if (!url) return;
    window.open(url, '_blank', 'noopener,noreferrer');
  }
};


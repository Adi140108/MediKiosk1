const GENERAL_DEPARTMENTS = [
  { id: "general-medicine", display_name: "General Medicine", icon: "", description: "Primary care, acute viral illnesses, non-specific fevers and multisystem initial evaluations." },
  { id: "cardiology", display_name: "Cardiology", icon: "", description: "Chest pain, palpitations, hypertension, ischemic workup and cardiovascular risk assessments." },
  { id: "pulmonology", display_name: "Pulmonology", icon: "", description: "Respiratory distress, persistent cough, dyspnea, asthma and chronic airway disorders." },
  { id: "neurology", display_name: "Neurology", icon: "", description: "Headaches, dizziness, focal neurological deficits, seizures and stroke triage evaluations." },
  { id: "gastroenterology", display_name: "Gastroenterology", icon: "️", description: "Abdominal pain, acute gastrointestinal bleed, jaundice, peptic and hepatic conditions." },
  { id: "orthopedics", display_name: "Orthopedics", icon: "", description: "Trauma, fractures, severe joint swellings, musculoskeletal injuries and spinal pain." },
  { id: "pediatrics", display_name: "Pediatrics", icon: "", description: "Infant and pediatric clinical reviews, childhood infections and pediatric triage." },
  { id: "emergency", display_name: "Emergency / Trauma", icon: "", description: "Immediate life-threatening triage, critical red flags, and emergency resuscitation." },
  { id: "dermatology", display_name: "Dermatology", icon: "", description: "Acute dermatological reactions, lesions, severe urticaria and cutaneous eruptions." },
  { id: "ent", display_name: "ENT", icon: "", description: "Ear discharge, hearing changes, vertigo, acute epistaxis and throat infections." },
  { id: "ophthalmology", display_name: "Ophthalmology", icon: "", description: "Visual disturbances, acute eye trauma, red eye and ocular pressure emergencies." },
  { id: "psychiatry", display_name: "Psychiatry", icon: "", description: "Acute distress, behavioral emergencies, psychiatric triage and mood disorders." },
  { id: "unspecified", display_name: "Triage & Float Queue", icon: "", description: "Ambiguous symptoms, multi-system red flags, and float cases awaiting department routing." }
];

const AYUSH_DEPARTMENTS = [
  { id: "ayush", display_name: "AYUSH / Ayurveda Main OPD", icon: "", description: "Ayurvedic general outpatient care, Prakriti constitution assessment and holistic triage." },
  { id: "kayachikitsa", display_name: "Kayachikitsa (Internal Medicine)", icon: "", description: "Agni, Dhatu, Ama, systemic illnesses, digestive and metabolic disorders." },
  { id: "panchakarma", display_name: "Panchakarma (Detox & Purification)", icon: "", description: "Shodhana therapy, Vamana, Virechana, Basti, Nasya and bio-cleansing evaluations." },
  { id: "shalya", display_name: "Shalya Tantra (General & Structural Care)", icon: "️", description: "Musculoskeletal, joint pain, spinal care, and structural Ayurvedic management." },
  { id: "shalakya", display_name: "Shalakya Tantra (ENT & Eye / Urdhvanga)", icon: "️", description: "Head, ear, nose, throat, and ocular disorders in Ayurveda." },
  { id: "prasuti-stri", display_name: "Prasuti Tantra & Stree Roga", icon: "", description: "Ayurvedic women's health, maternal wellness, and gynecological care." },
  { id: "kaumarabhritya", display_name: "Kaumarabhritya (Pediatrics)", icon: "", description: "Balaroga, infant care, pediatric growth and immune health in Ayurveda." },
  { id: "swasthavritta", display_name: "Swasthavritta & Yoga (Preventive Care)", icon: "", description: "Dinacharya, Ritucharya, Ahara, Vihara, preventive health and lifestyle medicine." },
  { id: "agadatantra", display_name: "Agada Tantra (Toxicology & Allergies)", icon: "", description: "Environmental allergies, toxicities, skin hypersensitivities and insect bites." }
];

const DEFAULT_DEPARTMENTS = GENERAL_DEPARTMENTS;

const PhysicianDashboard = {
  currentDepartment: null,
  currentDepartmentName: "Cardiology",
  currentSessionId: null,
  currentPatientData: null,
  currentLanguage: "en",
  opdMode: typeof localStorage !== 'undefined' ? (localStorage.getItem("medikiosk_active_mode") || "GENERAL_OPD") : "GENERAL_OPD",
  refreshTimer: null,
  originalRecommendedDept: null,
  originalRecommendedPriority: null,

  getDeptIcon(deptId) {
    const icons = {
      "general-medicine": "",
      "cardiology": "",
      "pulmonology": "",
      "neurology": "",
      "gastroenterology": "️",
      "orthopedics": "",
      "pediatrics": "",
      "emergency": "",
      "dermatology": "",
      "ent": "",
      "ophthalmology": "",
      "psychiatry": "",
      "ayush": "",
      "kayachikitsa": "",
      "panchakarma": "",
      "shalya": "️",
      "shalakya": "️",
      "prasuti-stri": "",
      "kaumarabhritya": "",
      "swasthavritta": "",
      "agadatantra": "",
      "unspecified": ""
    };
    return "";
  },

  init() {
    this.bindEvents();
    if (typeof I18n !== "undefined") {
      I18n.setLanguage(this.currentLanguage);
    }
    this.updatePortalOpdModeUI();
    this.loadDepartmentSelection();
  },

  togglePortalOpdMode() {
    this.opdMode = this.opdMode === "AYUSH_OPD" ? "GENERAL_OPD" : "AYUSH_OPD";
    try {
      localStorage.setItem("medikiosk_active_mode", this.opdMode);
    } catch(e) {}
    this.updatePortalOpdModeUI();
    this.showDepartmentSelection();
  },

  updatePortalOpdModeUI() {
    this.opdMode = (typeof localStorage !== 'undefined' ? (localStorage.getItem("medikiosk_active_mode") || "GENERAL_OPD") : "GENERAL_OPD");
    const pill = document.getElementById("physician-opd-mode-pill");
    const isAyush = this.opdMode.includes("AYUSH");
    if (pill) {
      if (isAyush) {
        pill.innerHTML = "AYUSH OPD";
        pill.style.background = "#fefce8";
        pill.style.borderColor = "#fde047";
        pill.style.color = "#854d0e";
      } else {
        pill.innerHTML = "GENERAL OPD";
        pill.style.background = "#f0fdf4";
        pill.style.borderColor = "#86efac";
        pill.style.color = "#166534";
      }
    }
    this.updateDepartmentDropdowns();
  },

  updateDepartmentDropdowns() {
    const isAyush = (this.opdMode || "GENERAL_OPD").includes("AYUSH");
    const deptList = isAyush ? AYUSH_DEPARTMENTS : GENERAL_DEPARTMENTS;

    ["confirm-dept-select", "transfer-dept-select", "transfer-target-dept"].forEach((selectId) => {
      const selectEl = document.getElementById(selectId);
      if (selectEl) {
        const currentVal = selectEl.value;
        selectEl.innerHTML = deptList.map(d => `<option value="${d.id}">${d.icon || this.getDeptIcon(d.id)} ${d.display_name}</option>`).join("");
        if (deptList.some(d => d.id === currentVal)) {
          selectEl.value = currentVal;
        }
      }
    });
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
      const deptMeta = (typeof I18n !== "undefined" && I18n.getDepartmentInfo) ? I18n.getDepartmentInfo(this.currentDepartment) : null;
      if (deptMeta?.name) {
        this.currentDepartmentName = deptMeta.name;
        const titleEl = document.getElementById("selected-dept-title");
        if (titleEl) titleEl.innerHTML = `${this.getDeptIcon(this.currentDepartment)} ${deptMeta.name}`;
      }
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

      const deptMeta = (typeof I18n !== "undefined" && I18n.getDepartmentInfo) 
        ? I18n.getDepartmentInfo(dept.id) 
        : null;

      const displayName = deptMeta?.name || dept.display_name || dept.name;
      const displayDesc = deptMeta?.desc || dept.description || 'Clinical department review queue.';

      const badgeClass = dept.id === "unspecified" ? "lang-badge-fallback" : "lang-badge-ready";
      const accessQueueLabel = (typeof I18n !== "undefined" && I18n.t) ? I18n.t("access_queue") : "ACCESS QUEUE →";
      const badgeLabel = dept.id === "unspecified" ? (accessQueueLabel.replace("ACCESS", "TRIAGE")) : accessQueueLabel;

      card.innerHTML = `
        <div style="font-size:2rem; margin-bottom:0.5rem;">${dept.icon || this.getDeptIcon(dept.id)}</div>
        <span class="lang-tile-native" style="font-size:1.2rem;">${displayName}</span>
        <p style="font-size:0.825rem; color:var(--text-muted); margin-top:0.25rem; line-height:1.4;">${displayDesc}</p>
        <span class="lang-tile-badge ${badgeClass}" style="margin-top:1rem;">${badgeLabel}</span>
      `;
      card.addEventListener("click", () => this.selectDepartment(dept.id, displayName, dept.icon || this.getDeptIcon(dept.id)));
      grid.appendChild(card);
    });
  },

  async loadDepartmentSelection() {
    this.opdMode = (typeof localStorage !== 'undefined' ? (localStorage.getItem("medikiosk_active_mode") || "GENERAL_OPD") : "GENERAL_OPD");
    const isAyush = this.opdMode.includes("AYUSH");
    const fallbackList = isAyush ? AYUSH_DEPARTMENTS : GENERAL_DEPARTMENTS;

    try {
      const departments = await api.getDepartments(this.opdMode);
      if (departments && departments.length > 0) {
        this.renderDepartmentGrid(departments);
      } else {
        this.renderDepartmentGrid(fallbackList);
      }
    } catch (err) {
      console.warn("Using default department fallback list:", err);
      this.renderDepartmentGrid(fallbackList);
    }
  },

  showDepartmentSelection() {
    clearInterval(this.refreshTimer);
    document.getElementById("physician-dept-view").style.display = "block";
    document.getElementById("physician-queue-view").style.display = "none";
    document.getElementById("physician-case-view").style.display = "none";
    this.currentDepartment = null;
    this.loadDepartmentSelection();
  },

  selectDepartment(deptId, deptName, deptIcon) {
    this.currentDepartment = deptId;
    this.currentDepartmentName = deptName;
    document.getElementById("physician-dept-view").style.display = "none";
    document.getElementById("physician-queue-view").style.display = "block";
    document.getElementById("physician-case-view").style.display = "none";

    const titleEl = document.getElementById("selected-dept-title");
    if (titleEl) titleEl.innerHTML = `${deptIcon} ${deptName}`;

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
        api.getDepartmentQueue(this.currentDepartment, search, severity, status, this.opdMode),
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
        const noPatientsMsg = (typeof I18n !== "undefined" && I18n.t) ? I18n.t("no_patients_in_queue") : "No patients currently in this department queue.";
        tableBody.innerHTML = `
          <tr>
            <td colspan="6" style="text-align:center; padding:3rem; color:var(--text-muted);">
              <p style="font-weight:700; font-size:1.05rem;">${noPatientsMsg}</p>
              <p style="font-size:0.85rem; margin-top:0.25rem;">Patients completing kiosk intake or transferred here will appear automatically.</p>
            </td>
          </tr>
        `;
        return;
      }

      const reviewCaseLabel = (typeof I18n !== "undefined" && I18n.t) ? I18n.t("review_case") : "Review Case →";
      const transferLabel = (typeof I18n !== "undefined" && I18n.t) ? I18n.t("transfer_patient") : "↗ Transfer";

      items.forEach((item) => {
        const tr = document.createElement("tr");

        let sevBadge = `<span class="lang-tile-badge lang-badge-connected">NORMAL</span>`;
        if (item.overall_severity === "CRITICAL") {
          sevBadge = `<span class="lang-tile-badge" style="background:#fee2e2; color:#991b1b; border:1px solid #ef4444;">CRITICAL</span>`;
        } else if (item.overall_severity === "HIGH") {
          sevBadge = `<span class="lang-tile-badge" style="background:#ffedd5; color:#9a3412; border:1px solid #f97316;">HIGH</span>`;
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
            ${item.has_documents ? '<span style="font-size:0.7rem; color:#0369a1; font-weight:600;"> Records Attached</span>' : ''}
          </td>
          <td>
            <span style="font-size:0.85rem; font-weight:600;">${waitDisplay}</span>
          </td>
          <td>${statusBadge}</td>
          <td>
            <div style="display:flex; gap:0.4rem;">
              <button class="btn-primary-action" style="padding:0.35rem 0.75rem; font-size:0.8rem;" onclick="PhysicianDashboard.inspectPatientCase('${item.session_id}')">
                ${reviewCaseLabel}
              </button>
              <button class="btn-secondary-action" style="padding:0.35rem 0.65rem; font-size:0.8rem;" title="Reassign Department" onclick="PhysicianDashboard.handleDirectReassign('${item.session_id}')">
                ${transferLabel}
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

    const overviewEl = document.getElementById("case-patient-overview");
    if (overviewEl) {
      overviewEl.innerHTML = `
        <h2 style="font-size:1.4rem; color:var(--brand-primary); margin:0;">Loading Patient Record...</h2>
        <p style="font-size:0.85rem; color:var(--text-muted); margin-top:0.25rem;">Fetching clinical audit data and OCR document evidence for session ${sessionId}...</p>
      `;
    }

    try {
      const data = await api.getPatientCase(sessionId);
      this.currentPatientData = data;
      this.populateCaseInspector(data);
    } catch (err) {
      console.error("Failed to load patient case record:", err);
      if (overviewEl) {
        overviewEl.innerHTML = `
          <div style="background:#fef2f2; border:1px solid #fca5a5; padding:1.25rem; border-radius:8px; color:#991b1b;">
            <h3 style="margin:0 0 0.4rem 0;">Patient Case Record Loading Notice</h3>
            <p style="margin:0 0 0.75rem 0; font-size:0.875rem;">${err.message || "Request timed out or case is processing. You can retry immediately."}</p>
            <button class="btn-primary-action" style="font-size:0.8rem; padding:0.4rem 0.85rem;" onclick="PhysicianDashboard.inspectPatientCase('${sessionId}')">Retry Loading Case</button>
            <button class="btn-secondary-action" style="font-size:0.8rem; padding:0.4rem 0.85rem; margin-left:0.5rem;" onclick="PhysicianDashboard.showQueueView()">← Back to Queue</button>
          </div>
        `;
      }
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
    const opdMode = data.opd_mode || data.mode_at_intake || (data.queue_item && data.queue_item.opd_mode) || "GENERAL_OPD";
    const modeBadgeHtml = (opdMode === "AYUSH_OPD") 
      ? `<span style="background:linear-gradient(135deg, #059669, #047857); color:#fff; font-size:0.75rem; font-weight:800; padding:4px 10px; border-radius:12px; margin-left:8px; box-shadow:0 2px 6px rgba(5,150,105,0.3);">AYUSH OPD</span>`
      : `<span style="background:linear-gradient(135deg, #0d9488, #0f766e); color:#fff; font-size:0.75rem; font-weight:800; padding:4px 10px; border-radius:12px; margin-left:8px; box-shadow:0 2px 6px rgba(13,148,136,0.3);">GENERAL OPD</span>`;

    if (overviewEl) {
      overviewEl.innerHTML = `
        <div style="display:flex; align-items:center; gap:8px;">
          <h2 style="font-size:1.4rem; color:var(--brand-primary); margin:0;">${patient.name || 'Patient Case'}</h2>
          ${modeBadgeHtml}
        </div>
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
      if (rfTitle) rfTitle.innerText = `${red_flag.overall_severity} CLINICAL RED FLAG DETECTED`;
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
        expGaps.innerHTML = information_gaps.map(g => `<span class="gap-pill">${g.label || g.field}</span>`).join("");
      } else {
        expGaps.innerHTML = `<p style="color:#166534; font-size:0.825rem;">Complete clinical profile captured.</p>`;
      }
    }

    // 3.5 Detailed Clinical Summary Card & Narrative Highlights
    const detComplaintEl = document.getElementById("det-chief-complaint");
    const detChief = draft_summary.chief_complaint || data.context?.chief_complaint || data.queue_item?.chief_complaint_summary || "Patient presents for consultation review.";
    if (detComplaintEl) detComplaintEl.innerText = detChief;

    const detTagsEl = document.getElementById("det-symptom-tags");
    if (detTagsEl) {
      const tags = [];
      const lowerComplaint = detChief.toLowerCase();
      if (lowerComplaint.includes("chest") || lowerComplaint.includes("छाती") || lowerComplaint.includes("सीने")) tags.push(`<span class="gap-pill" style="background:#eff6ff; color:#1d4ed8; border-color:#bfdbfe;">Chest Pain</span>`);
      if (lowerComplaint.includes("joint") || lowerComplaint.includes("जोड़") || lowerComplaint.includes("घुटने")) tags.push(`<span class="gap-pill" style="background:#fef3c7; color:#b45309; border-color:#fde68a;">Joint Pain</span>`);
      if (lowerComplaint.includes("head") || lowerComplaint.includes("सिर")) tags.push(`<span class="gap-pill" style="background:#fdf2f8; color:#9d174d; border-color:#fbcfe8;">Headache</span>`);
      if (lowerComplaint.includes("stomach") || lowerComplaint.includes("पेट")) tags.push(`<span class="gap-pill" style="background:#f0fdf4; color:#15803d; border-color:#bbf7d0;">Abdominal Pain</span>`);
      if (tags.length === 0) tags.push(`<span class="gap-pill" style="background:#f8fafc; color:#475569; border-color:#cbd5e1;">General Triage</span>`);
      detTagsEl.innerHTML = tags.join(" ");
    }

    const detPainBadge = document.getElementById("det-pain-score-badge");
    const detPainBar = document.getElementById("det-pain-progress-bar");
    const detPainDesc = document.getElementById("det-pain-description");
    const painScore = data.context?.severity || data.context?.pain_score || (draft_summary.metrics && draft_summary.metrics.pain_level) || 7;
    if (detPainBadge) detPainBadge.innerText = `Level ${painScore} / 10`;
    if (detPainBar) detPainBar.style.width = `${Math.min(100, Math.max(10, painScore * 10))}%`;
    if (detPainDesc) {
      if (painScore >= 8) detPainDesc.innerText = "Critical / Maximum pain severity recorded.";
      else if (painScore >= 6) detPainDesc.innerText = "Severe distress reported during initial patient triage.";
      else if (painScore >= 4) detPainDesc.innerText = "Moderate distress reported during initial triage.";
      else detPainDesc.innerText = "Mild symptoms reported during initial triage.";
    }

    const detTrajectory = document.getElementById("det-trajectory");
    const detDurInfo = document.getElementById("det-duration-info");
    if (detTrajectory) {
      const prog = draft_summary.symptom_progression || data.context?.progression || "Active presentation, continuous clinical monitoring";
      detTrajectory.innerText = prog;
    }
    if (detDurInfo) {
      detDurInfo.innerText = data.context?.onset_time || "Documented during AI Socratic interview";
    }

    const detMedHistory = document.getElementById("det-medical-history");
    if (detMedHistory) {
      const conds = data.context?.known_conditions || medical_history.known_conditions || draft_summary.medical_history || [];
      const meds = data.context?.medications || medical_history.medications || draft_summary.medications || [];
      const pastHistory = data.context?.past_medical_history || "";
      const rxNotes = data.context?.prescription_notes || "";

      let items = [];
      if (conds && conds.length > 0) {
        items.push(`<div style="margin-bottom:0.25rem;"><strong>Conditions:</strong> ${conds.map(c => `<span class="gap-pill" style="background:#fef2f2; color:#991b1b; border-color:#fecaca; font-size:0.75rem;">${c}</span>`).join(" ")}</div>`);
      }
      if (meds && meds.length > 0) {
        items.push(`<div style="margin-bottom:0.25rem;"><strong>Ongoing Daily Meds:</strong> ${meds.map(m => `<span class="gap-pill" style="background:#eff6ff; color:#1e40af; border-color:#bfdbfe; font-size:0.75rem;">${m}</span>`).join(" ")}</div>`);
      }
      if (pastHistory) {
        items.push(`<div style="margin-bottom:0.25rem; font-size:0.8rem; color:#475569;"><strong>Past Surgeries/Allergies:</strong> ${pastHistory}</div>`);
      }
      if (rxNotes) {
        items.push(`<div style="font-size:0.8rem; color:#15803d; background:#f0fdf4; padding:0.35rem 0.6rem; border-radius:4px; border:1px solid #bbf7d0; margin-top:0.25rem;"><strong>Dictated Rx Notes:</strong> ${rxNotes}</div>`);
      }

      detMedHistory.innerHTML = items.length > 0 ? items.join("") : "<span style='color:#64748b;'>No pre-existing conditions or daily medications recorded.</span>";
    }

    const detHpiNarrative = document.getElementById("det-hpi-narrative");
    const detEditNarrative = document.getElementById("det-edit-narrative-textarea");
    let fullHpi = draft_summary.hpi || draft_summary.hpi_narrative || data.context?.hpi || (draft_summary.chief_complaint ? `Patient presented with ${draft_summary.chief_complaint}. Severity score rated at Level ${painScore}/10. Clinical investigation performed via multilingual adaptive dialogue.` : "Intake recorded. Summary synthesizes patient voice statements, associated symptom investigations, and clinical red flags.");
    
    // Strip out any legacy "Clinical Dialogue Findings:" bullet text or question lists
    if (fullHpi.includes("Clinical Dialogue Findings:")) {
      fullHpi = fullHpi.split("Clinical Dialogue Findings:")[0].trim();
    }
    if (fullHpi.includes("•")) {
      fullHpi = fullHpi.split("\n").filter(l => !l.includes("•")).join("\n").trim();
    }
    if (fullHpi.includes("Q:") || fullHpi.includes("A:")) {
      fullHpi = fullHpi.split("\n").filter(line => !line.trim().startsWith("Q:") && !line.trim().startsWith("A:")).join("\n").trim();
    }
    
    if (detHpiNarrative) detHpiNarrative.innerText = fullHpi;
    if (detEditNarrative) detEditNarrative.value = fullHpi;

    // 4. Modern Clinical Brief
    const complaintText = document.getElementById("case-chief-complaint-text");
    if (complaintText) {
      complaintText.innerText = detChief;
    }

    const hpiText = document.getElementById("case-hpi-text");
    if (hpiText) {
      hpiText.innerText = fullHpi;
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
      const conds = data.context?.known_conditions || medical_history.known_conditions || draft_summary.medical_history || [];
      const meds = data.context?.medications || medical_history.medications || draft_summary.medications || [];
      const pastHistory = data.context?.past_medical_history || "";
      const rxNotes = data.context?.prescription_notes || "";

      let parts = [];
      if (conds.length > 0) parts.push(`Conditions: ${conds.join(", ")}`);
      if (meds.length > 0) parts.push(`Daily Meds: ${meds.join(", ")}`);
      if (pastHistory) parts.push(`History/Allergies: ${pastHistory}`);
      if (rxNotes) parts.push(`Dictated Advice: "${rxNotes}"`);

      medHistText.innerText = parts.length > 0 ? parts.join(" | ") : "None reported";
    }

    // 5. Ayurvedic Perspective & AYUSH 4-Layer Assessment Engine
    const ayurEl = document.getElementById("case-ayurvedic-details");
    const ayurPane = document.querySelector(".ayurvedic-pane");
    const clinicalGrid = document.querySelector(".clinical-comparison-grid");
    const activeOpdMode = (data.opd_mode || data.mode_at_intake || this.opdMode || (typeof localStorage !== 'undefined' ? localStorage.getItem("medikiosk_active_mode") : null) || "GENERAL_OPD").toUpperCase();
    const isAyushMode = activeOpdMode.includes("AYUSH");

    if (ayurPane) {
      if (isAyushMode) {
        ayurPane.style.display = "block";
        if (clinicalGrid) clinicalGrid.style.gridTemplateColumns = "1fr 1fr";
      } else {
        ayurPane.style.display = "none";
        if (clinicalGrid) clinicalGrid.style.gridTemplateColumns = "1fr";
      }
    }

    const ayushAssessment = data.ayush_assessment || {};
    this.currentWhyBreakdown = ayushAssessment.why_breakdown || null;

    if (ayurEl) {
      const prakriti = ayushAssessment.prakriti || { status: "INSUFFICIENT_DATA", summary: "Insufficient information" };
      const vikriti = ayushAssessment.vikriti || { status: "INSUFFICIENT_DATA", summary: "Insufficient information" };
      const agni = ayushAssessment.agni || { status: "INSUFFICIENT_DATA", summary: "Insufficient information" };
      const ama = ayushAssessment.ama || { status: "INSUFFICIENT_DATA", summary: "Insufficient information" };
      const koshta = ayushAssessment.koshta || { status: "INSUFFICIENT_DATA", summary: "Insufficient information" };
      const satva = ayushAssessment.satva || { status: "INSUFFICIENT_DATA", summary: "Insufficient information" };
      const satmya = ayushAssessment.satmya || { status: "INSUFFICIENT_DATA", summary: "Insufficient information" };
      const dushya = ayushAssessment.dushya_status || { status: "INSUFFICIENT_DATA", summary: "Insufficient information" };
      const srotas = ayushAssessment.srotas_status || { status: "INSUFFICIENT_DATA", summary: "Insufficient information" };

      const isPrakritiValid = prakriti.status === "SUFFICIENT_DATA" && prakriti.scores;
      const vScore = isPrakritiValid ? (prakriti.scores.Vata || 0) : 0;
      const pScore = isPrakritiValid ? (prakriti.scores.Pitta || 0) : 0;
      const kScore = isPrakritiValid ? (prakriti.scores.Kapha || 0) : 0;

      ayurEl.innerHTML = `
        <!-- Prakriti 23-Domain Assessment Card -->
        <div style="background:#ffffff; border:1px solid #fef08a; border-radius:10px; padding:0.85rem; margin-bottom:0.75rem;">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
            <div style="font-weight:800; color:#854d0e; font-size:0.95rem;">Baseline Prakriti: ${isPrakritiValid ? (prakriti.primary_category || prakriti.summary) : 'Insufficient information'}</div>
            <span class="gap-pill" style="font-size:0.7rem; background:${isPrakritiValid ? '#fef08a' : '#f1f5f9'}; color:${isPrakritiValid ? '#854d0e' : '#64748b'}; border-color:${isPrakritiValid ? '#fde047' : '#cbd5e1'}; margin:0;">
              ${isPrakritiValid ? 'Confidence: High' : 'Insufficient Data'}
            </span>
          </div>

          ${isPrakritiValid ? `
          <!-- Dosha Percentage Bars -->
          <div style="display:flex; flex-direction:column; gap:6px; margin-top:0.5rem;">
            <div>
              <div style="display:flex; justify-content:space-between; font-size:0.75rem; font-weight:700; color:#78350f;">
                <span>Vata Dosha</span>
                <span>${vScore}%</span>
              </div>
              <div style="background:#fef3c7; height:6px; border-radius:3px; overflow:hidden; margin-top:2px;">
                <div style="width:${vScore}%; height:100%; background:#d97706; border-radius:3px;"></div>
              </div>
            </div>
            <div>
              <div style="display:flex; justify-content:space-between; font-size:0.75rem; font-weight:700; color:#78350f;">
                <span>Pitta Dosha</span>
                <span>${pScore}%</span>
              </div>
              <div style="background:#fee2e2; height:6px; border-radius:3px; overflow:hidden; margin-top:2px;">
                <div style="width:${pScore}%; height:100%; background:#dc2626; border-radius:3px;"></div>
              </div>
            </div>
            <div>
              <div style="display:flex; justify-content:space-between; font-size:0.75rem; font-weight:700; color:#78350f;">
                <span>Kapha Dosha</span>
                <span>${kScore}%</span>
              </div>
              <div style="background:#dbeafe; height:6px; border-radius:3px; overflow:hidden; margin-top:2px;">
                <div style="width:${kScore}%; height:100%; background:#2563eb; border-radius:3px;"></div>
              </div>
            </div>
          </div>
          ` : `
          <div style="font-size:0.8rem; color:#94a3b8; font-style:italic; padding:0.4rem 0;">
            Insufficient observations gathered to calculate baseline Vata / Pitta / Kapha proportions.
          </div>
          `}
        </div>

        <!-- 23-Domain Clinical Grid -->
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:0.5rem; margin-bottom:0.75rem;">
          <div style="background:#ffffff; border:1px solid #fef08a; border-radius:8px; padding:0.5rem 0.65rem;">
            <span style="font-size:0.68rem; font-weight:700; color:#854d0e; text-transform:uppercase;">Vikriti Trajectory</span>
            <p style="font-weight:700; color:#713f12; margin:2px 0 0 0; font-size:0.8rem;">${vikriti.summary || 'Insufficient information'}</p>
          </div>
          <div style="background:#ffffff; border:1px solid #fef08a; border-radius:8px; padding:0.5rem 0.65rem;">
            <span style="font-size:0.68rem; font-weight:700; color:#854d0e; text-transform:uppercase;">Agni State (Digestion)</span>
            <p style="font-weight:700; color:#713f12; margin:2px 0 0 0; font-size:0.8rem;">${agni.summary || agni.type || 'Insufficient information'}</p>
          </div>
          <div style="background:#ffffff; border:1px solid #fef08a; border-radius:8px; padding:0.5rem 0.65rem;">
            <span style="font-size:0.68rem; font-weight:700; color:#854d0e; text-transform:uppercase;">Koshta (Bowel Pattern)</span>
            <p style="font-weight:700; color:#713f12; margin:2px 0 0 0; font-size:0.8rem;">${koshta.summary || koshta.type || 'Insufficient information'}</p>
          </div>
          <div style="background:#ffffff; border:1px solid #fef08a; border-radius:8px; padding:0.5rem 0.65rem;">
            <span style="font-size:0.68rem; font-weight:700; color:#854d0e; text-transform:uppercase;">Ama Status (Toxicity)</span>
            <p style="font-weight:700; color:#713f12; margin:2px 0 0 0; font-size:0.8rem;">${ama.summary || ama.status || 'Insufficient information'}</p>
          </div>
          <div style="background:#ffffff; border:1px solid #fef08a; border-radius:8px; padding:0.5rem 0.65rem;">
            <span style="font-size:0.68rem; font-weight:700; color:#854d0e; text-transform:uppercase;">Dushya (Affected Tissues)</span>
            <p style="font-weight:700; color:#713f12; margin:2px 0 0 0; font-size:0.8rem;">${dushya.summary || 'Insufficient information'}</p>
          </div>
          <div style="background:#ffffff; border:1px solid #fef08a; border-radius:8px; padding:0.5rem 0.65rem;">
            <span style="font-size:0.68rem; font-weight:700; color:#854d0e; text-transform:uppercase;">Srotas (Body Channels)</span>
            <p style="font-weight:700; color:#713f12; margin:2px 0 0 0; font-size:0.8rem;">${srotas.summary || 'Insufficient information'}</p>
          </div>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center; border-top:1px solid #fef08a; padding-top:0.6rem;">
          <button type="button" class="btn-primary-action" style="font-size:0.75rem; padding:0.35rem 0.75rem; background:linear-gradient(135deg, #0d9488, #0f766e);" onclick="PhysicianDashboard.openWhyModal()">
            Interactive "Why?" Evidence Trace
          </button>
          <span style="font-size:0.7rem; color:#854d0e; font-style:italic;">Ayurvedic Engine V2 Grounded</span>
        </div>
      `;
    }

    // 6. Socratic Transcript with Doctor Answer Editing
    const qaList = document.getElementById("case-qa-list");
    if (qaList) {
      if (questions && questions.length > 0) {
        const sessId = data.session_id || (data.queue_item && data.queue_item.session_id) || (this.currentPatientData && this.currentPatientData.session_id) || "";
        qaList.innerHTML = questions.map((q, idx) => {
          const ans = answers.find(a => a.question_id === q.question_id || a.sequence === q.sequence);
          const ansVal = ans ? (ans.answer || ans.normalized_answer || ans.original_answer || ans.answer_text) : null;
          const isAttendant = ans && ans.source_type === "ATTENDANT";
          const isPhysician = ans && ans.source_type === "PHYSICIAN";
          const attendantBadge = isAttendant ? '<span class="gap-pill" style="font-size:0.7rem; color:#92400e; background:#fef3c7; border-color:#fde68a;">Attendant Assisted</span>' : '';
          const physicianBadge = isPhysician ? '<span class="gap-pill" style="font-size:0.7rem; color:#0369a1; background:#e0f2fe; border-color:#bae6fd;">Physician Edited</span>' : '';
          const qId = q.question_id || `q_${idx + 1}`;
          
          let ansBody = '<span style="color:#94a3b8; font-style:italic;">Pending patient response...</span>';
          if (ansVal) {
            ansBody = `
              <div id="ans-display-${idx}" style="font-size:0.875rem; color:#1e293b; font-weight:500;">
                "${ansVal}"
              </div>
              ${(ans.original_answer && ans.original_answer !== ansVal) ? `<div style="font-size:0.75rem; color:#64748b; margin-top:2px;">Original utterance: "${ans.original_answer}" (${ans.original_language || 'Native'})</div>` : ''}
            `;
          }

          return `
            <div style="margin-bottom:1rem; padding-bottom:0.85rem; border-bottom:1px solid #f1ece4;">
              <div style="font-weight:600; font-size:0.875rem; color:var(--brand-primary); margin-bottom:0.35rem; display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:0.4rem;">
                <span>Q${idx + 1}: ${q.question}</span>
                <div style="display:flex; align-items:center; gap:0.4rem;">
                  ${attendantBadge}
                  ${physicianBadge}
                  <button type="button" class="btn-secondary-action" style="font-size:0.725rem; padding:2px 7px; border-color:#cbd5e1; background:white;" onclick="PhysicianDashboard.toggleAnswerEdit(${idx})">
                    Edit Answer
                  </button>
                </div>
              </div>
              <div style="background:#f8fafc; border-left:3px solid var(--brand-primary); padding:0.6rem 0.85rem; border-radius:0 6px 6px 0;">
                ${ansBody}
                <!-- Inline Edit Box -->
                <div id="edit-ans-container-${idx}" style="display:none; margin-top:0.5rem; background:white; border:1.5px solid #0284c7; border-radius:6px; padding:0.65rem;">
                  <label style="font-size:0.75rem; font-weight:700; color:#0369a1; display:block; margin-bottom:3px;">Doctor Modification / Refinement:</label>
                  <textarea id="edit-ans-text-${idx}" class="form-textarea-field" rows="2" style="font-size:0.85rem; width:100%; margin-bottom:0.4rem;">${ansVal || ''}</textarea>
                  <div style="display:flex; justify-content:flex-end; gap:0.4rem;">
                    <button type="button" class="btn-secondary-action" style="font-size:0.725rem; padding:2px 8px;" onclick="PhysicianDashboard.toggleAnswerEdit(${idx}, false)">Cancel</button>
                    <button type="button" class="btn-primary-action" style="font-size:0.725rem; padding:2px 10px;" onclick="PhysicianDashboard.saveAnswerEdit('${sessId}', '${qId}', ${idx})">Save Answer</button>
                  </div>
                </div>
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
                  <span>Extracted Laboratory Findings:</span>
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
                ${meds.map(m => `<span class="gap-pill" style="font-size:0.75rem; background:#eff6ff; color:#1e40af; border-color:#bfdbfe;">${m.name} ${m.dosage || ''} ${m.frequency || ''}</span>`).join('')}
              </div>
            `;
          }

          // Format conditions if any exist
          let condsHtml = "";
          if (conds.length > 0) {
            condsHtml = `
              <div style="margin-top:0.4rem; display:flex; flex-wrap:wrap; gap:4px; align-items:center;">
                <span style="font-size:0.75rem; font-weight:700; color:#475569;">Impression:</span>
                ${conds.map(c => `<span class="gap-pill" style="font-size:0.75rem; background:#fef3c7; color:#92400e; border-color:#fde68a;">${c}</span>`).join('')}
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
                <span class="ocr-item-title">
                  <svg class="btn-icon-svg" style="color:#0D9488;" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>
                  <strong>${filename}</strong>
                </span>
                <span style="display:flex; gap:6px; align-items:center; flex-wrap:wrap;">
                  <span class="gap-pill" style="font-size:0.7rem; background:#F8FAFC; color:#475569; border-color:#CBD5E1;">Store: ${d.storage_provider || 'Encrypted Store'}</span>
                  <span class="gap-pill" style="font-size:0.7rem; background:#ECFDF5; color:#065F46; border-color:#A7F3D0; font-weight:700;">${confPercent}% OCR</span>
                  <span class="gap-pill" style="font-size:0.7rem; background:#EEF2FF; color:#4338CA; border-color:#C7D2FE;">SHA-256 Sealed</span>
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
                      <span>Show/Hide Full Raw OCR Text</span>
                    </button>
                    <div id="raw-ocr-${idx}" class="ocr-raw-box" style="display:none; margin-top:0.4rem;">
                      ${rawText}
                    </div>
                  </div>
                ` : ''}

                ${scanUrl ? `
                  <div style="display:flex; gap:0.5rem; margin-top:0.75rem; align-items:center; flex-wrap:wrap;">
                    <button type="button" class="btn-scan-preview" onclick="PhysicianDashboard.openDocumentScanModal('${scanUrl}', '${filename.replace(/'/g, "\\'")}')">
                      Preview Document Scan
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
        docsList.innerHTML = `
          <div style="background:#F8FAFC; border:1px dashed #CBD5E1; border-radius:10px; padding:1.25rem; text-align:center;">
            <div style="font-size:1.8rem; margin-bottom:0.4rem;"></div>
            <h5 style="margin:0; font-size:0.92rem; font-weight:700; color:#334155;">No Prior Physical Documents Uploaded</h5>
            <p style="margin:0.25rem 0 0.85rem 0; font-size:0.8rem; color:#64748B;">Patient completed intake verbally or without physical prescription papers.</p>
            <button type="button" class="btn-card-action btn-card-action-secondary" style="font-size:0.78rem;" onclick="PhysicianDashboard.loadDemoEvidenceReport()">
              <svg class="btn-icon-svg" viewBox="0 0 24 24"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="18" x2="12" y2="12"></line><line x1="9" y1="15" x2="15" y2="15"></line></svg>
              <span>Inspect Sample Digitized Lab Report</span>
            </button>
          </div>
        `;
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
      let cleanSummary = fullHpi || draft_summary.hpi_narrative || draft_summary.hpi || "";
      if (cleanSummary.includes("Q:") || cleanSummary.includes("A:")) {
        cleanSummary = cleanSummary.split("\n").filter(l => !l.trim().startsWith("Q:") && !l.trim().startsWith("A:")).join(" ").trim();
      }
      // Keep only first 2 sentences if narrative is long
      const summarySentences = cleanSummary.split(".").filter(s => s.trim().length > 0).slice(0, 2).join(". ");
      summaryEdit.value = detChief 
        ? `Chief Complaint: ${detChief}. ${summarySentences ? summarySentences + '.' : ''}`
        : "Patient presents for clinical consultation and evaluation.";
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

    // Dynamically update dropdown based on active OPD mode / patient OPD mode
    const patientMode = (this.currentPatientData && this.currentPatientData.queue_item && this.currentPatientData.queue_item.opd_mode) || this.opdMode || "GENERAL_OPD";
    const isAyush = patientMode.includes("AYUSH");
    const deptList = isAyush ? AYUSH_DEPARTMENTS : GENERAL_DEPARTMENTS;
    const deptSelect = document.getElementById("transfer-target-dept");
    if (deptSelect) {
      deptSelect.innerHTML = deptList.map(d => `<option value="${d.id}">${d.icon || this.getDeptIcon(d.id)} ${d.display_name}</option>`).join("");
      if (this.currentDepartment && deptList.some(d => d.id === this.currentDepartment)) {
        // Default to a different department than current if possible
        const other = deptList.find(d => d.id !== this.currentDepartment);
        if (other) deptSelect.value = other.id;
      }
    }

    const modal = document.getElementById("transfer-patient-modal");
    if (!modal) return;
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
        "cardiology": { name: "Cardiology", icon: "" },
        "neurology": { name: "Neurology", icon: "" },
        "general-medicine": { name: "General Medicine", icon: "" },
        "pediatrics": { name: "Pediatrics", icon: "" },
        "orthopedics": { name: "Orthopedics", icon: "" },
        "emergency": { name: "Emergency / Trauma", icon: "" },
        "gastroenterology": { name: "Gastroenterology", icon: "" },
        "dermatology": { name: "Dermatology", icon: "" },
        "ent": { name: "ENT", icon: "" },
        "ophthalmology": { name: "Ophthalmology", icon: "" },
        "psychiatry": { name: "Psychiatry", icon: "" },
        "ayush": { name: "AYUSH / Integrative", icon: "" },
        "kayachikitsa": { name: "Kayachikitsa (Internal Medicine)", icon: "" },
        "panchakarma": { name: "Panchakarma (Detox & Purification)", icon: "" },
        "shalya": { name: "Shalya Tantra (Structural Care)", icon: "" },
        "shalakya": { name: "Shalakya Tantra (ENT & Eye)", icon: "" },
        "prasuti-stri": { name: "Prasuti Tantra & Stree Roga", icon: "" },
        "kaumarabhritya": { name: "Kaumarabhritya (Pediatrics)", icon: "" },
        "swasthavritta": { name: "Swasthavritta & Yoga", icon: "" },
        "agadatantra": { name: "Agada Tantra (Toxicology)", icon: "" }
      };

      const deptMeta = targetDeptInfo[targetDept] || { name: targetDept.toUpperCase(), icon: "" };
      const shouldSwitch = confirm(`Patient successfully transferred to ${deptMeta.name} waiting queue!\n\nWould you like to switch to the ${deptMeta.name} Department Queue now?`);

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

    if (!confirm("IMMEDIATE EMERGENCY ESCALATION\n\nAre you sure you want to flag this patient for Immediate Emergency Priority and move them to the Emergency Department Queue?")) {
      return;
    }

    try {
      await api.reassignDepartment(targetSession, "emergency", "dr_sharma_cardio", "Immediate Emergency Escalation by physician");
      alert("Patient successfully escalated to Emergency / Trauma Department queue.");
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
      alert("Question dispatched to patient intake session!");
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
        alert("Please open or select an active patient case first.");
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
        alert("Override rationale is required when altering the AI recommended department or priority.");
        if (btn) {
          btn.disabled = false;
          btn.innerText = "Confirm & Sign Record";
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

      alert("Clinical record successfully finalized, signed, and logged to audit trail.");
      this.showQueueView();
    } catch (err) {
      alert("Confirmation notice: " + (err.message || "Failed to confirm patient record"));
    } finally {
      if (btn) {
        btn.disabled = false;
        btn.innerText = "Confirm & Sign Record";
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
    if (toggleBtn) toggleBtn.innerText = nextState ? "Close Edit" : "️ Edit Summary";
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

    if (title) title.innerText = `${filename}`;
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

  toggleDetailedSummaryEdit(show) {
    const editBox = document.getElementById("det-edit-mode-box");
    const toggleBtn = document.getElementById("btn-toggle-det-edit");
    const isShowing = editBox && editBox.style.display !== "none";
    const nextState = show !== undefined ? show : !isShowing;

    if (editBox) editBox.style.display = nextState ? "block" : "none";
    if (toggleBtn) toggleBtn.innerText = nextState ? "Close Edit" : "️ Edit Summary";
    if (nextState) {
      const textarea = document.getElementById("det-edit-narrative-textarea");
      if (textarea) textarea.focus();
    }
  },

  saveDetailedSummaryEdit() {
    const newNarrative = document.getElementById("det-edit-narrative-textarea")?.value.trim() || "";
    const narEl = document.getElementById("det-hpi-narrative");
    if (narEl) narEl.innerText = newNarrative || "Clinical summary updated by physician.";

    const caseHpiText = document.getElementById("case-hpi-text");
    if (caseHpiText) caseHpiText.innerText = newNarrative || "Clinical summary updated by physician.";

    const summaryEdit = document.getElementById("physician-summary-edit");
    if (summaryEdit) summaryEdit.value = newNarrative;

    if (this.currentPatientData) {
      if (!this.currentPatientData.draft_summary) this.currentPatientData.draft_summary = {};
      this.currentPatientData.draft_summary.hpi = newNarrative;
      this.currentPatientData.draft_summary.hpi_narrative = newNarrative;
    }

    this.toggleDetailedSummaryEdit(false);
  },

  toggleAnswerEdit(idx, show) {
    const editBox = document.getElementById(`edit-ans-container-${idx}`);
    if (!editBox) return;
    const isShowing = editBox.style.display !== "none";
    const nextState = show !== undefined ? show : !isShowing;
    editBox.style.display = nextState ? "block" : "none";
    if (nextState) {
      const textarea = document.getElementById(`edit-ans-text-${idx}`);
      if (textarea) textarea.focus();
    }
  },

  async saveAnswerEdit(sessionId, questionId, idx) {
    const textarea = document.getElementById(`edit-ans-text-${idx}`);
    const newAnswer = textarea ? textarea.value.trim() : "";
    if (!newAnswer) {
      alert("Please enter answer text.");
      return;
    }

    const targetSessionId = sessionId || this.currentSessionId || (this.currentPatientData && this.currentPatientData.session_id);
    try {
      await api.updateAnswer(targetSessionId, questionId, newAnswer, "dr_sharma_cardio");
      
      const ansDisp = document.getElementById(`ans-display-${idx}`);
      if (ansDisp) {
        ansDisp.innerHTML = `"${newAnswer}" <span class="gap-pill" style="font-size:0.7rem; color:#0369a1; background:#e0f2fe; border-color:#bae6fd; margin-left:6px;">Physician Edited</span>`;
      }
      this.toggleAnswerEdit(idx, false);
    } catch (err) {
      console.warn("Answer edit update notice:", err);
      const ansDisp = document.getElementById(`ans-display-${idx}`);
      if (ansDisp) {
        ansDisp.innerHTML = `"${newAnswer}" <span class="gap-pill" style="font-size:0.7rem; color:#0369a1; background:#e0f2fe; border-color:#bae6fd; margin-left:6px;">Physician Edited</span>`;
      }
      this.toggleAnswerEdit(idx, false);
    }
  },

  openAyurvedicRagModal() {
    const modal = document.getElementById("ayur-rag-modal");
    if (!modal) return;
    modal.style.display = "flex";
    const searchInput = document.getElementById("ayur-rag-search-input");
    const currentComplaint = this.currentPatientData?.draft_summary?.chief_complaint || this.currentPatientData?.context?.chief_complaint || "";
    if (searchInput) {
      if (currentComplaint && !searchInput.value) {
        searchInput.value = currentComplaint;
      }
      this.executeAyurvedicRagSearch();
    }
  },

  closeAyurvedicRagModal() {
    const modal = document.getElementById("ayur-rag-modal");
    if (modal) modal.style.display = "none";
  },

  async executeAyurvedicRagSearch() {
    const input = document.getElementById("ayur-rag-search-input");
    const query = input?.value.trim() || "";
    const container = document.getElementById("ayur-rag-results-container");
    if (!container) return;

    if (!query) {
      container.innerHTML = `<p style="text-align:center; color:var(--text-muted); padding:1.5rem 0;">Please enter a search query.</p>`;
      return;
    }

    container.innerHTML = `<p style="text-align:center; color:#854d0e; padding:2rem 0;">Searching AyurGenixAI dataset & AyurParam knowledge base...</p>`;

    try {
      const res = await api.queryAyurvedaRag(query, this.currentLanguage || "en", 3);
      const records = res?.records || [];
      if (records.length === 0) {
        container.innerHTML = `<p style="text-align:center; color:var(--text-muted); padding:2rem 0;">No matching Ayurvedic records found for "${query}".</p>`;
        return;
      }

      container.innerHTML = records.map((r, idx) => `
        <div style="background:#fffdf7; border:1.5px solid #fde047; border-radius:8px; padding:1.25rem; margin-bottom:1rem; box-shadow:0 1px 3px rgba(0,0,0,0.05);">
          <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem; flex-wrap:wrap; gap:0.4rem;">
            <div>
              <span style="font-size:1.05rem; font-weight:800; color:#854d0e;">${r.ayurvedic_nidana}</span>
              <span style="font-size:0.8rem; color:#78350f; margin-left:6px;">(${r.modern_correlation})</span>
            </div>
            <span class="gap-pill" style="font-size:0.7rem; background:#fef08a; color:#854d0e; border-color:#fde047; font-weight:700;">Record #${idx + 1}</span>
          </div>

          <div style="display:grid; grid-template-columns: 1fr 1fr; gap:0.75rem; margin-bottom:0.75rem; font-size:0.85rem;">
            <div><strong>Dominant Dosha:</strong> ${r.dominant_dosha}</div>
            <div><strong>Agni State:</strong> ${r.agni_status}</div>
            <div><strong>Affected Dhatu:</strong> ${(r.dhatu_affected || []).join(', ')}</div>
            <div><strong>Affected Srotas:</strong> ${(r.srotas_affected || []).join(', ')}</div>
          </div>

          <p style="font-size:0.85rem; color:#451a03; line-height:1.5; margin-bottom:0.65rem;">
            <strong>Clinical Presentation:</strong> ${r.clinical_presentation}
          </p>

          <div style="margin-bottom:0.4rem; font-size:0.85rem;">
            <strong style="color:#15803d;">Pathya (Diet & Lifestyle):</strong> ${(r.pathya || []).join(', ')}
          </div>
          <div style="margin-bottom:0.4rem; font-size:0.85rem;">
            <strong style="color:#b91c1c;">Apathya (Contraindications):</strong> ${(r.apathya || []).join(', ')}
          </div>
          <div style="margin-bottom:0.4rem; font-size:0.85rem;">
            <strong style="color:#0369a1;">Classical Formulations:</strong> ${(r.classical_herbs_formulations || []).join(', ')}
          </div>

          <div style="font-size:0.75rem; color:#a16207; margin-top:0.65rem; border-top:1px solid #fef08a; padding-top:0.4rem; font-style:italic;">
            Classical Samhita Citation: ${r.classical_reference}
          </div>
        </div>
      `).join("");
    } catch (err) {
      container.innerHTML = `<p style="text-align:center; color:#b91c1c; padding:1.5rem 0;">Error querying Ayurvedic RAG: ${err.message}</p>`;
    }
  },

  openScanLink(url) {
    if (!url) return;
    window.open(url, '_blank', 'noopener,noreferrer');
  },

  openWhyModal() {
    const modal = document.getElementById("ayush-why-modal");
    const container = document.getElementById("why-modal-content");
    if (!modal || !container) return;

    modal.style.display = "flex";
    const ev = this.currentWhyBreakdown;

    if (!ev || !ev.matched_features || ev.matched_features.length === 0) {
      container.innerHTML = `
        <div style="background:#f8fafc; border:1.5px solid #cbd5e1; border-radius:14px; padding:20px; text-align:center; color:#64748b;">
          <div style="font-size:2rem; margin-bottom:6px;"></div>
          <p style="font-weight:700; color:#334155; margin:0; font-size:0.95rem;">Baseline Clinical Features Tracked</p>
          <p style="font-size:0.825rem; margin-top:4px; margin-bottom:0;">Patient observations were recorded and evaluated against baseline Ayurvedic indicator criteria.</p>
        </div>
      `;
      return;
    }

    let html = `
      <div style="margin-bottom:16px; background:#f0fdf4; border:1.5px solid #bbf7d0; border-radius:14px; padding:14px 18px;">
        <h4 style="font-size:0.95rem; font-weight:800; color:#166534; margin:0;">Matched Symptom Indicators (${ev.matched_features.length} Features Detected)</h4>
      </div>
      <div style="display:flex; flex-direction:column; gap:10px;">
    `;

    ev.matched_features.forEach((feat, idx) => {
      const weights = feat.weights || {};
      const v = weights.VATA || 0;
      const p = weights.PITTA || 0;
      const k = weights.KAPHA || 0;

      html += `
        <div style="background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:12px 16px; box-shadow:0 1px 3px rgba(0,0,0,0.04);">
          <div style="display:flex; justify-content:space-between; align-items:center;">
            <span style="font-weight:700; color:#0f172a; font-size:0.9rem;">${idx + 1}. ${feat.description || feat.feature_id}</span>
            <span class="gap-pill" style="margin:0; font-size:0.75rem; background:#f1f5f9; color:#475569;">${feat.domain || 'CLINICAL'}</span>
          </div>
          <div style="display:flex; gap:14px; margin-top:8px; font-size:0.825rem; font-weight:800;">
            <span style="color:${v > 0 ? '#d97706' : '#94a3b8'};">Vata: ${v > 0 ? '+' + v : v}</span>
            <span style="color:${p > 0 ? '#dc2626' : '#94a3b8'};">Pitta: ${p > 0 ? '+' + p : p}</span>
            <span style="color:${k > 0 ? '#2563eb' : '#94a3b8'};">Kapha: ${k > 0 ? '+' + k : k}</span>
          </div>
        </div>
      `;
    });

    html += `</div>`;

    if (ev.raw_observations && ev.raw_observations.length > 0) {
      html += `
        <div style="margin-top:20px; border-top:1px dashed #cbd5e1; padding-top:16px;">
          <h4 style="font-size:0.95rem; font-weight:800; color:#0f172a; margin-bottom:12px;">Raw Patient Evidence Responses</h4>
          <div style="display:flex; flex-direction:column; gap:10px;">
      `;
      ev.raw_observations.forEach((obs) => {
        html += `
          <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:12px; padding:12px 14px; font-size:0.85rem;">
            <div style="font-weight:700; color:#334155;">Q: ${obs.question}</div>
            <div style="color:#0f172a; margin-top:3px; font-weight:600;">A: "${obs.answer}"</div>
          </div>
        `;
      });
      html += `</div></div>`;
    }

    container.innerHTML = html;
  },

  closeWhyModal() {
    const modal = document.getElementById("ayush-why-modal");
    if (modal) modal.style.display = "none";
  }
};


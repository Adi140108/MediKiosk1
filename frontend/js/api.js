const API_BASE = "/api/v1";

// Lightweight in-memory and sessionStorage department cache
let memoryDeptCache = null;

async function fetchWithTimeout(resource, options = {}, timeoutMs = 15000) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(resource, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    if (error.name === 'AbortError') {
      throw new Error(`Request timed out after ${timeoutMs}ms`);
    }
    throw error;
  }
}

const api = {
  async getDepartments(opdMode = "GENERAL_OPD", forceRefresh = false) {
    const mode = typeof opdMode === "string" ? opdMode : "GENERAL_OPD";
    const cacheKey = `medikiosk_departments_${mode}`;
    if (!forceRefresh) {
      if (typeof memoryDeptCache === "object" && memoryDeptCache && memoryDeptCache[mode]) return memoryDeptCache[mode];
      try {
        const cached = sessionStorage.getItem(cacheKey);
        if (cached) {
          const parsed = JSON.parse(cached);
          if (!memoryDeptCache || typeof memoryDeptCache !== "object") memoryDeptCache = {};
          memoryDeptCache[mode] = parsed;
          this.getDepartments(mode, true).catch(() => {});
          return parsed;
        }
      } catch (e) {}
    }

    const res = await fetchWithTimeout(`${API_BASE}/physician/departments?opd_mode=${encodeURIComponent(mode)}`, {}, 12000);
    if (!res.ok) throw new Error("Failed to fetch departments");
    const data = await res.json();
    if (!memoryDeptCache || typeof memoryDeptCache !== "object") memoryDeptCache = {};
    memoryDeptCache[mode] = data;
    try {
      sessionStorage.setItem(cacheKey, JSON.stringify(data));
    } catch (e) {}
    return data;
  },

  async getDepartmentDashboard(deptId, opdMode = "GENERAL_OPD") {
    const res = await fetchWithTimeout(`${API_BASE}/physician/departments/${deptId}/dashboard?opd_mode=${encodeURIComponent(opdMode)}`, {}, 12000);
    if (!res.ok) throw new Error("Failed to fetch department dashboard");
    return res.json();
  },

  async registerPatient(data) {
    const res = await fetchWithTimeout(`${API_BASE}/patients/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    }, 6000);
    if (!res.ok) throw new Error("Patient registration failed");
    return res.json();
  },

  async registerAttendant(patientId, data) {
    const res = await fetchWithTimeout(`${API_BASE}/patients/${patientId}/attendant`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    }, 6000);
    if (!res.ok) throw new Error("Attendant registration failed");
    return res.json();
  },

  async submitConsent(patientId, sessionId, isAttendant = false, attendantId = null) {
    const res = await fetchWithTimeout(`${API_BASE}/patients/${patientId}/consent?session_id=${sessionId}&is_attendant=${isAttendant}${attendantId ? `&attendant_id=${attendantId}` : ''}`, {
      method: "POST"
    }, 6000);
    if (!res.ok) throw new Error("Consent submission failed");
    return res.json();
  },

  async uploadDocument(formData) {
    const res = await fetchWithTimeout(`${API_BASE}/documents/upload`, {
      method: "POST",
      body: formData
    }, 30000);
    if (!res.ok) {
      let errMsg = "Document upload failed";
      try {
        const err = await res.json();
        errMsg = err.detail || errMsg;
      } catch (e) {
        errMsg = (await res.text().catch(() => '')) || `Upload failed with status ${res.status}`;
      }
      throw new Error(errMsg);
    }
    return res.json();
  },

  async getDocumentStatus(documentId) {
    const res = await fetchWithTimeout(`${API_BASE}/documents/${documentId}/status`, {}, 3500);
    if (!res.ok) throw new Error("Failed to fetch document status");
    return res.json();
  },

  async startIntake(patientId, language = "en", isAttendant = false, attendantId = null, sessionId = null, chiefComplaint = null, painLevel = null, knownConditions = [], medications = [], pastMedicalHistory = null, prescriptionNotes = null, opdMode = "GENERAL_OPD") {
    const res = await fetchWithTimeout(`${API_BASE}/intake/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        patient_id: patientId,
        session_id: sessionId || null,
        language: language,
        opd_mode: opdMode || "GENERAL_OPD",
        is_attendant_assisted: isAttendant,
        attendant_id: attendantId,
        chief_complaint: chiefComplaint || null,
        pain_level: painLevel || null,
        known_conditions: knownConditions || [],
        medications: medications || [],
        past_medical_history: pastMedicalHistory || null,
        prescription_notes: prescriptionNotes || null
      })
    }, 25000);
    if (!res.ok) throw new Error("Failed to start intake session");
    return res.json();
  },

  async updateAnswer(sessionId, questionId, newAnswer, physicianId = "unknown_physician") {
    const res = await fetchWithTimeout(`${API_BASE}/intake/answer/update`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        question_id: questionId,
        new_answer: newAnswer,
        physician_id: physicianId
      })
    }, 15000);
    if (!res.ok) throw new Error("Failed to update answer");
    return res.json();
  },

  async submitAnswer(sessionId, questionId, answer, sourceType = "PATIENT", attendantId = null, language = "en") {
    const res = await fetchWithTimeout(`${API_BASE}/intake/answer`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        question_id: questionId,
        answer: answer,
        source_type: sourceType,
        attendant_id: attendantId,
        language: language
      })
    }, 25000);
    if (!res.ok) throw new Error("Failed to submit answer");
    return res.json();
  },

  async completeIntake(sessionId, patientId) {
    const res = await fetchWithTimeout(`${API_BASE}/intake/complete`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: sessionId,
        patient_id: patientId
      })
    }, 25000);
    if (!res.ok) throw new Error("Failed to complete intake");
    return res.json();
  },

  async getDepartmentQueue(deptId, search = null, severity = null, status = null, opdMode = null) {
    let url = `${API_BASE}/physician/queue/${deptId}?`;
    if (search) url += `search=${encodeURIComponent(search)}&`;
    if (severity) url += `severity=${encodeURIComponent(severity)}&`;
    if (status) url += `status=${encodeURIComponent(status)}&`;
    if (opdMode) url += `opd_mode=${encodeURIComponent(opdMode)}&`;

    const res = await fetchWithTimeout(url, {}, 25000);
    if (!res.ok) throw new Error("Failed to fetch department queue");
    return res.json();
  },

  async getPatientCase(sessionId) {
    const res = await fetchWithTimeout(`${API_BASE}/physician/patient/${sessionId}`, {}, 25000);
    if (!res.ok) throw new Error("Failed to fetch patient case details");
    return res.json();
  },

  async recordPhysicianDecision(sessionId, payload) {
    const res = await fetchWithTimeout(`${API_BASE}/physician/sessions/${sessionId}/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }, 15000);
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Physician decision submission failed");
    }
    return res.json();
  },

  async askTargetedQuestion(sessionId, payload) {
    const res = await fetchWithTimeout(`${API_BASE}/physician/sessions/${sessionId}/ask_patient`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }, 15000);
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to dispatch question to patient");
    }
    return res.json();
  },

  async reassignDepartment(sessionId, targetDept, physicianId = "attending_physician", reason = null) {
    let url = `${API_BASE}/physician/sessions/${sessionId}/reassign_department?target_department=${encodeURIComponent(targetDept)}&physician_id=${encodeURIComponent(physicianId)}`;
    if (reason) url += `&reason=${encodeURIComponent(reason)}`;
    const res = await fetchWithTimeout(url, { method: "POST" }, 15000);
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Department reassignment failed");
    }
    return res.json();
  },

  async confirmPatientCase(sessionId, payload) {
    const res = await fetchWithTimeout(`${API_BASE}/physician/confirm/${sessionId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }, 15000);
    if (!res.ok) throw new Error("Failed to confirm patient case");
    return res.json();
  },

  async getHealth() {
    const res = await fetchWithTimeout(`${API_BASE}/health`, {}, 3000);
    if (!res.ok) throw new Error("Health check failed");
    return res.json();
  },

  async getPerformanceDiagnostics() {
    const res = await fetchWithTimeout(`${API_BASE}/diagnostics/performance`, {}, 3000);
    if (!res.ok) throw new Error("Performance diagnostics failed");
    return res.json();
  },

  async queryAyurvedaRag(query, language = "en", topK = 2) {
    const res = await fetchWithTimeout(`${API_BASE}/ayurveda/rag/query`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, language, top_k: topK })
    }, 8000);
    if (!res.ok) throw new Error("Ayurveda RAG query failed");
    return res.json();
  },

  async getAyurvedaDatasetInfo() {
    const res = await fetchWithTimeout(`${API_BASE}/ayurveda/rag/dataset/info`, {}, 4000);
    if (!res.ok) throw new Error("Failed to fetch Ayurveda dataset info");
    return res.json();
  },

  async evaluateAyurvedaRag(chiefComplaint, associatedSymptoms = [], painLevel = null, language = "en") {
    const res = await fetchWithTimeout(`${API_BASE}/ayurveda/rag/evaluate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        chief_complaint: chiefComplaint,
        associated_symptoms: associatedSymptoms,
        pain_level: painLevel,
        language: language
      })
    }, 8000);
    if (!res.ok) throw new Error("Ayurveda RAG evaluation failed");
    return res.json();
  }
};

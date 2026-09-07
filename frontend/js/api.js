const API_BASE = "/api/v1";

// Lightweight in-memory and sessionStorage department cache
let memoryDeptCache = null;

async function fetchWithTimeout(resource, options = {}, timeoutMs = 6500) {
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
  async getDepartments(forceRefresh = false) {
    if (!forceRefresh) {
      if (memoryDeptCache) return memoryDeptCache;
      try {
        const cached = sessionStorage.getItem("medikiosk_departments");
        if (cached) {
          memoryDeptCache = JSON.parse(cached);
          // Background refresh
          this.getDepartments(true).catch(() => {});
          return memoryDeptCache;
        }
      } catch (e) {}
    }

    const res = await fetchWithTimeout(`${API_BASE}/physician/departments`, {}, 4000);
    if (!res.ok) throw new Error("Failed to fetch departments");
    const data = await res.json();
    memoryDeptCache = data;
    try {
      sessionStorage.setItem("medikiosk_departments", JSON.stringify(data));
    } catch (e) {}
    return data;
  },

  async getDepartmentDashboard(deptId) {
    const res = await fetchWithTimeout(`${API_BASE}/physician/departments/${deptId}/dashboard`, {}, 5000);
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
    // Immediate return with status=PROCESSING
    const res = await fetchWithTimeout(`${API_BASE}/documents/upload`, {
      method: "POST",
      body: formData
    }, 8000);
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Document upload failed");
    }
    return res.json();
  },

  async getDocumentStatus(documentId) {
    const res = await fetchWithTimeout(`${API_BASE}/documents/${documentId}/status`, {}, 3500);
    if (!res.ok) throw new Error("Failed to fetch document status");
    return res.json();
  },

  async startIntake(patientId, language = "en", isAttendant = false, attendantId = null, sessionId = null) {
    const res = await fetchWithTimeout(`${API_BASE}/intake/start`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        patient_id: patientId,
        session_id: sessionId || null,
        language: language,
        is_attendant_assisted: isAttendant,
        attendant_id: attendantId
      })
    }, 6000);
    if (!res.ok) throw new Error("Failed to start intake session");
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
    }, 5000);
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
    }, 6000);
    if (!res.ok) throw new Error("Failed to complete intake");
    return res.json();
  },

  async getDepartmentQueue(deptId, search = null, severity = null, status = null) {
    let url = `${API_BASE}/physician/queue/${deptId}?`;
    if (search) url += `search=${encodeURIComponent(search)}&`;
    if (severity) url += `severity=${encodeURIComponent(severity)}&`;
    if (status) url += `status=${encodeURIComponent(status)}&`;

    const res = await fetchWithTimeout(url, {}, 5000);
    if (!res.ok) throw new Error("Failed to fetch department queue");
    return res.json();
  },

  async getPatientCase(sessionId) {
    const res = await fetchWithTimeout(`${API_BASE}/physician/patient/${sessionId}`, {}, 5000);
    if (!res.ok) throw new Error("Failed to fetch patient case details");
    return res.json();
  },

  async recordPhysicianDecision(sessionId, payload) {
    const res = await fetchWithTimeout(`${API_BASE}/physician/sessions/${sessionId}/decision`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    }, 6000);
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
    }, 6000);
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.detail || "Failed to dispatch question to patient");
    }
    return res.json();
  },

  async reassignDepartment(sessionId, targetDept, physicianId = "attending_physician", reason = null) {
    let url = `${API_BASE}/physician/sessions/${sessionId}/reassign_department?target_department=${encodeURIComponent(targetDept)}&physician_id=${encodeURIComponent(physicianId)}`;
    if (reason) url += `&reason=${encodeURIComponent(reason)}`;
    const res = await fetchWithTimeout(url, { method: "POST" }, 6000);
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
    }, 6000);
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
  }
};

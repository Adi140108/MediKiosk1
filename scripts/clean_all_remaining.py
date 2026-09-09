"""
Clean all emojis from remaining files in frontend:
- frontend/js/patient_intake.js
- frontend/js/speech.js
- frontend/diagnostics.html
- frontend/physician.html
- frontend/js/physician_dashboard.js
"""
import re

def clean_patient_intake_js():
    path = "frontend/js/patient_intake.js"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Step milestones
    content = content.replace('1: { icon: "✓", title: "Registration Started"', '1: { icon: "1", title: "Registration Started"')
    content = content.replace('2: { icon: "🌐", title: "Language Selected"', '2: { icon: "2", title: "Language Selected"')
    content = content.replace('3: { icon: "🛡️", title: "Consent Confirmed"', '3: { icon: "3", title: "Consent Confirmed"')
    content = content.replace('4: { icon: "👤", title: "Patient Details Saved"', '4: { icon: "4", title: "Patient Details Saved"')
    content = content.replace('5: { icon: "🩺", title: "Symptoms & Vitals Saved"', '5: { icon: "5", title: "Symptoms & Vitals Saved"')
    content = content.replace('6: { icon: "📄", title: "Documents Attached"', '6: { icon: "6", title: "Documents Attached"')
    content = content.replace('7: { icon: "📋", title: "Clinical Inquiry Finished"', '7: { icon: "7", title: "Clinical Inquiry Finished"')
    content = content.replace('8: { icon: "🎫", title: "Consultation Ticket Issued"', '8: { icon: "8", title: "Consultation Ticket Issued"')

    # Step indicator node.innerHTML
    content = content.replace('node.innerHTML = "✓";', 'node.innerHTML = \'<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>\';')

    # Mobile titles
    content = content.replace('1: { icon: "📍", title: "Welcome & Registration" }', '1: { icon: "", title: "Welcome & Registration" }')
    content = content.replace('2: { icon: "🌐", title: "Select Language" }', '2: { icon: "", title: "Select Language" }')
    content = content.replace('3: { icon: "🛡️", title: "Patient Consent" }', '3: { icon: "", title: "Patient Consent" }')
    content = content.replace('4: { icon: "👤", title: "Patient Details" }', '4: { icon: "", title: "Patient Details" }')
    content = content.replace('5: { icon: "🩺", title: "Symptoms & History" }', '5: { icon: "", title: "Symptoms & History" }')
    content = content.replace('6: { icon: "📄", title: "Previous Records" }', '6: { icon: "", title: "Previous Records" }')
    content = content.replace('7: { icon: "💬", title: "AI Clinical Intake" }', '7: { icon: "", title: "AI Clinical Intake" }')
    content = content.replace('8: { icon: "🎫", title: "Consultation Token" }', '8: { icon: "", title: "Consultation Token" }')

    # Selected badge
    content = content.replace('badge.innerText = "✓ SELECTED";', 'badge.innerHTML = \'<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle; margin-right:3px;"><polyline points="20 6 9 17 4 12"></polyline></svg>SELECTED\';')

    # Alert warning
    content = content.replace('alert("⚠️ Please check the agreement box to confirm your consent.");', 'alert("Please check the agreement box to confirm your consent.");')

    # OCR text & icons
    content = content.replace('color:#1d4ed8;">📄</div>', 'color:#1d4ed8;"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg></div>')
    content = content.replace('text-overflow:ellipsis;">📄 ${file.name}</p>', 'text-overflow:ellipsis;">${file.name}</p>')
    content = content.replace('"📖 Show Full Extracted Text ▼"', '"Show Full Extracted Text ▼"')
    content = content.replace('>📖 Show Full Extracted Text ▼<', '>Show Full Extracted Text ▼<')
    content = content.replace('<span class="spinner" style="display:inline-block;">⏳</span>', '<span class="spinner" style="display:inline-block;"></span>')
    content = content.replace('<span style="font-size:1.3rem;">✅</span>', '<span style="display:inline-flex; align-items:center; justify-content:center; width:22px; height:22px; border-radius:50%; background:#DCFCE7; color:#16A34A;"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg></span>')
    content = content.replace('Document Encrypted & Stored ✓', 'Document Encrypted & Stored')
    content = content.replace('<span class="spinner">⏳</span>', '<span class="spinner"></span>')
    content = content.replace('✓ OCR Digitization Complete', 'OCR Digitization Complete')
    content = content.replace('📄 Extracted Clinical Content:', 'Extracted Clinical Content:')
    content = content.replace('✓ Proceed to AI Clinical Interview →', 'Proceed to AI Clinical Interview →')
    content = content.replace('⚠️ Upload Notice', 'Upload Notice')
    content = content.replace('<span style="margin-right:6px;">⏳</span>', '')

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Cleaned patient_intake.js")


def clean_speech_js():
    path = "frontend/js/speech.js"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace("🎙️ ", "")
    content = content.replace("🎙️", "")
    content = content.replace("🎤 ", "")
    content = content.replace("🎤", "")
    content = content.replace("✓ Voice captured", "Voice captured")
    content = content.replace("⏳ Processing audio", "Processing audio")
    content = content.replace("⚠️ Speech not recognized", "Speech not recognized")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Cleaned speech.js")


def clean_diagnostics_html():
    path = "frontend/diagnostics.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace("🤖 AI & LLM Engine", "AI & LLM Engine")
    content = content.replace("🇮🇳 AI4Bharat Indic Suite", "AI4Bharat Indic Suite")
    content = content.replace("📄 Genuine OCR Engine", "Genuine OCR Engine")
    content = content.replace("☁️ Dual Storage Architecture", "Dual Storage Architecture")
    content = content.replace("⚡ Subsystem Latency Telemetry", "Subsystem Latency Telemetry")
    content = content.replace("🔍 Live Health Telemetry", "Live Health Telemetry")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Cleaned diagnostics.html")


def clean_physician_dashboard_js():
    path = "frontend/js/physician_dashboard.js"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # Department icons map
    content = re.sub(r'"agadatantra":\s*"🧪",', '"agadatantra": "",', content)
    content = re.sub(r'"unspecified":\s*"🏥"', '"unspecified": ""', content)
    content = re.sub(r'return icons\[deptId\] \|\| "🩺";', 'return "";', content)

    # OPD pill labels
    content = content.replace('pill.innerHTML = "🌿 AYUSH OPD ⚙️";', 'pill.innerHTML = "AYUSH OPD";')
    content = content.replace('pill.innerHTML = "🏥 GENERAL OPD ⚙️";', 'pill.innerHTML = "GENERAL OPD";')

    # Severity badges
    content = content.replace('🚨 CRITICAL', 'CRITICAL')
    content = content.replace('⚠️ HIGH', 'HIGH')
    content = content.replace('🚨 Immediate Red-Flag', 'Immediate Red-Flag')

    # Document attachment icon
    content = content.replace("📎", "")

    # Patient case review
    content = content.replace("⚠️ Patient Case Record", "Patient Case Record")
    content = content.replace("🔄 Refresh Record", "Refresh Record")

    # Tags / Gaps
    content = content.replace("⚠️ ", "")
    content = content.replace("✓ No critical information gaps", "No critical information gaps")
    content = content.replace("✓ No prescription medications recorded", "No prescription medications recorded")
    content = content.replace("✓ Active & In Sync", "Active & In Sync")

    # Chief complaint tags
    content = content.replace('tags.push(`<span class="gap-pill" style="background:#eff6ff; color:#1e40af; border:1px solid #bfdbfe;">🫀 Chest</span>`);',
                             'tags.push(`<span class="gap-pill" style="background:#eff6ff; color:#1e40af; border:1px solid #bfdbfe;">Chest</span>`);')
    content = content.replace('tags.push(`<span class="gap-pill" style="background:#eff6ff; color:#1e40af; border:1px solid #bfdbfe;">🦴 Joint</span>`);',
                             'tags.push(`<span class="gap-pill" style="background:#eff6ff; color:#1e40af; border:1px solid #bfdbfe;">Joint</span>`);')
    content = content.replace('tags.push(`<span class="gap-pill" style="background:#eff6ff; color:#1e40af; border:1px solid #bfdbfe;">🧠 Head</span>`);',
                             'tags.push(`<span class="gap-pill" style="background:#eff6ff; color:#1e40af; border:1px solid #bfdbfe;">Head</span>`);')
    content = content.replace('tags.push(`<span class="gap-pill" style="background:#eff6ff; color:#1e40af; border:1px solid #bfdbfe;">🩺 Abdominal</span>`);',
                             'tags.push(`<span class="gap-pill" style="background:#eff6ff; color:#1e40af; border:1px solid #bfdbfe;">Abdominal</span>`);')
    content = content.replace('tags.push(`<span class="gap-pill" style="background:#eff6ff; color:#1e40af; border:1px solid #bfdbfe;">🩺 General</span>`);',
                             'tags.push(`<span class="gap-pill" style="background:#eff6ff; color:#1e40af; border:1px solid #bfdbfe;">General</span>`);')

    # Meds & Speech items
    content = content.replace("💊 ", "")
    content = content.replace("🗣️ ", "")
    content = content.replace("🌿 ", "")
    content = content.replace("🔍 Interactive", "Interactive")
    content = content.replace("✏️ Edit Answer", "Edit Answer")
    content = content.replace("✓ Save Changes", "Save Changes")
    content = content.replace("🧪 Extracted Laboratory Findings:", "Extracted Laboratory Findings:")
    content = content.replace("📄 ", "")
    content = content.replace("✓ Patient successfully reassigned", "Patient successfully reassigned")
    content = content.replace("🚨 IMMEDIATE EMERGENCY ESCALATION", "IMMEDIATE EMERGENCY ESCALATION")
    content = content.replace("🚨 Patient successfully escalated", "Patient successfully escalated")
    content = content.replace("✓ Question dispatched", "Question dispatched")
    content = content.replace("⚠️ Please open or select", "Please open or select")
    content = content.replace("⚠️ Override rationale is required", "Override rationale is required")
    content = content.replace("✓ Confirm & Sign Record", "Confirm & Sign Record")
    content = content.replace("✓ Clinical record successfully finalized", "Clinical record successfully finalized")
    content = content.replace('toggleBtn.innerText = nextState ? "✕ Cancel Editing" : "✏️ Edit Answer"',
                             'toggleBtn.innerText = nextState ? "Cancel Editing" : "Edit Answer"')
    content = content.replace("✓ Pathya", "Pathya")
    content = content.replace("✗ Apathya", "Apathya")
    content = content.replace("📖 Classical Samhita Citation:", "Classical Samhita Citation:")

    # TargetDeptInfo icons
    target_depts = [
        "cardiology", "neurology", "general-medicine", "pediatrics", "orthopedics",
        "emergency", "gastroenterology", "dermatology", "ent", "ophthalmology",
        "psychiatry", "ayush", "kayachikitsa", "panchakarma", "shalya",
        "shalakya", "prasuti-stri", "kaumarabhritya", "swasthavritta", "agadatantra"
    ]
    for d in target_depts:
        content = re.sub(rf'"{d}":\s*\{{\s*name:\s*"([^"]+)",\s*icon:\s*"[^"]*"\s*\}}',
                         rf'"{d}": {{ name: "\1", icon: "" }}', content)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Cleaned physician_dashboard.js")


def clean_physician_html():
    path = "frontend/physician.html"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    content = content.replace("<span>🛡️</span>", '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>')
    content = content.replace("<span>👨‍⚕️</span>", '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>')
    content = content.replace("🏥 GENERAL OPD ⚙️", "GENERAL OPD")
    content = content.replace('<span style="font-size:0.82rem;">🌐</span>', '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>')
    content = content.replace("⚙️ Diagnostics", "Diagnostics")
    content = content.replace("🏥 Patient Kiosk", "Patient Kiosk")
    content = content.replace("🚨 Critical Only", "Critical Only")
    content = content.replace("⚠️ High Only", "High Only")
    content = content.replace("🔄 Refresh Queue", "Refresh Queue")
    content = content.replace("🔍 Search patient", "Search patient")
    content = content.replace("<span>🎯</span>", "")
    content = content.replace("<span>⚡</span>", "")
    content = content.replace("<span>🔎</span>", "")
    content = content.replace('<span style="font-size:1.3rem;">📋</span>', "")
    content = content.replace("<span>📝</span>", "")
    content = content.replace("<span>✓</span>", "")
    content = content.replace("<span>🩺</span>", "")
    content = content.replace("<span>🌿</span>", "")
    content = content.replace("⚠️ Notice:", "Notice:")
    content = content.replace('<span style="font-size:1.25rem;">📄</span>', "")
    content = content.replace("🛡️ Verified Genuine OCR", "Verified Genuine OCR")
    content = content.replace("🚨 Critical", "Critical")
    content = content.replace("⚠️ High Priority", "High Priority")
    content = content.replace("⚠️ Override Rationale Required", "Override Rationale Required")
    content = content.replace("<span>✓ Confirm & Sign Record</span>", "<span>Confirm & Sign Record</span>")
    content = content.replace("<span>🚨 Escalate</span>", "<span>Escalate</span>")
    content = content.replace("<span>🔄 Transfer / Reassign Department Only</span>", "<span>Transfer / Reassign Department</span>")
    content = content.replace("<span>🔄</span> Transfer / Reassign Department", "Transfer / Reassign Department")

    # Options in selects
    dept_emojis = ["🫀", "🧠", "🩺", "👶", "🦴", "🚨", "🍽️", "🍽", "🧴", "👂", "👁", "🧩", "🌿", "🍵", "🪔", "🗡", "🌺", "🧘", "🧪", "⏱", "💊", "🔬", "🔍", "✕"]
    for emo in dept_emojis:
        content = content.replace(emo + " ", "")
        content = content.replace(emo, "")

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("Cleaned physician.html")


if __name__ == "__main__":
    clean_patient_intake_js()
    clean_speech_js()
    clean_diagnostics_html()
    clean_physician_dashboard_js()
    clean_physician_html()

# MediKiosk — Clinical Intelligence, OCR & Physician Triage Platform

![MediKiosk Logo](public/logo.png)

MediKiosk is an AI-assisted, physician-in-the-loop clinical intake, triage, and physician command center platform built for healthcare environments. It streamlines pre-consultation patient intake using adaptive Socratic questioning, multilingual voice/text support (10 Indian languages), genuine document OCR, and deterministic clinical triage rules.

---

## 🌟 Key Architecture & Capabilities

### 1. 🏥 Patient Intake Kiosk
- **8-Step Interactive Wizard**: Guiding patients through registration, Ayushman Bharat Digital Mission (ABDM/ABHA) identification, consent, symptom profiling, document uploading, and intelligent Q&A.
- **Hands-Free Speech-to-Speech**: Real-time microphone audio recording and Text-to-Speech question prompts.
- **Multilingual Intake**: Full support for 10 Indian languages (Hindi, Kannada, Tamil, Telugu, Malayalam, Marathi, Bengali, Gujarati, Punjabi, and English).
- **Attendant-Assisted Mode**: Allows family members to register and assist patients while preserving audit provenance.

### 2. 🤖 Clinical Intelligence & Adaptive Branching
- **Socratic Clinical Inquiry**: Dynamically generates targeted follow-up questions tailored to chief complaints (cardiac, neurological, respiratory, pediatric, etc.).
- **Ayurvedic & Holistic Perspective**: Parallel integrative intake (Agni, Prakriti, Bala, Ahara/Vihara) presented alongside modern clinical history.
- **Zero-Hallucination Safe Fallback**: Safe fallback logic that prevents clinical fabrication when remote LLMs are offline.

### 3. 🚨 Deterministic Red-Flag Triage & Department Routing
- **Age-Based Routing**: Children (ages 0–18) are deterministically routed to **Pediatrics**.
- **Mild / General Symptom Routing**: Uncomplicated symptoms route automatically to **General Medicine**.
- **Emergency Escalation**: Immediate priority elevation to `CRITICAL` with instant queue transfers.

### 4. 👨‍⚕️ Physician Command Center
- **Specialty Queue Management**: Live department queues (Cardiology, Neurology, Pediatrics, Orthopedics, General Medicine, Emergency, AYUSH).
- **Side-by-Side Clinical Views**: Modern History of Present Illness (HPI) vs. Ayurvedic findings.
- **Explainable AI Cards**: Transparent reasoning showing *Why This Department?* and *Triage Urgency Basis*.
- **Department Reassignment & Transfer**: Doctors can transfer patient records across departments with mandatory audit reasoning.
- **Physician Decision Sign-Off**: Attending doctors can override triage, review lab results, order investigations, and sign clinical records.

### 5. 📄 Genuine Document OCR & Dual Storage
- **OCR Engine**: Tesseract OCR multi-strategy image evaluation and PDF text extraction.
- **Dual Cloud Storage**:
  - **Cloudinary**: Medical images and prescription photographs.
  - **Backblaze B2**: Encrypted medical PDFs and lab records.
  - **Firestore / Local Fallback**: Persistent clinical metadata storage.

---

## 🚀 Quick Start (Local Development)

### Prerequisites
- Python 3.10+
- (Optional) Tesseract OCR

### Installation

```bash
# Clone the repository
git clone https://github.com/Adi140108/MediKiosk1.git
cd MediKiosk1

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run Locally
Step 1: Open Terminal in the Project Directory
powershell
cd c:\Users\adity\MediKiosk1
Step 2: Activate the Virtual Environment
powershell
.venv\Scripts\Activate.ps1
(If you are on Command Prompt cmd: .venv\Scripts\activate.bat)

Step 3: Start the FastAPI Server
powershell
python -m uvicorn backend.app.main:app --port 8000 --reload
Step 4: Open in Browser
Open http://localhost:8000/ in your browser.
```bash
# Start FastAPI server
python -m uvicorn backend.app.main:app --reload --port 8000
```

Access the applications at:
- **Patient Kiosk**: [http://localhost:8000/](http://localhost:8000/)
- **Physician Portal**: [http://localhost:8000/physician](http://localhost:8000/physician)
- **Diagnostics Dashboard**: [http://localhost:8000/diagnostics](http://localhost:8000/diagnostics)
- **API Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 Testing

Run the comprehensive pytest test suite (29 tests):

```bash
pytest -v
```

---

## ☁️ Deployment (Vercel)

This project is configured for Vercel deployment:
- **`public/`**: Static frontend files (`index.html`, `physician.html`, `diagnostics.html`, CSS, JS) served directly from Vercel's Edge CDN.
- **`api/index.py`**: Python serverless handler executing the FastAPI clinical backend.
- **`vercel.json`**: Unified clean URL routing and API rewrites.

---

## 📁 Repository Structure

```
MediKiosk1/
├── api/
│   └── index.py             # Vercel Serverless entrypoint
├── backend/
│   ├── app/
│   │   ├── api/v1/          # REST API route controllers
│   │   ├── ai/              # Socratic engine, LLM providers, OCR
│   │   ├── core/            # App settings & configurations
│   │   ├── db/              # Firestore repositories & fallbacks
│   │   └── modules/         # Patients, triage, documents storage
│   └── tests/               # Pytest automated test suites
├── public/                  # Vercel Edge static assets
│   ├── index.html           # Patient intake kiosk
│   ├── physician.html       # Physician command center
│   ├── diagnostics.html     # Live health & telemetry dashboard
│   ├── css/                 # Modern styling & design tokens
│   └── js/                  # Frontend logic & API clients
├── frontend/                # Source UI components
├── requirements.txt         # Production Python dependencies
├── vercel.json              # Vercel deployment configuration
└── README.md                # Project documentation
```

---

## 🔒 Safety & Privacy
- **Physician-in-the-Loop**: MediKiosk does not diagnose conditions or prescribe medications autonomously. All suggestions require attending physician review and sign-off.
- **ABDM Compliant**: Implements Ayushman Bharat Digital Mission privacy and consent standards.

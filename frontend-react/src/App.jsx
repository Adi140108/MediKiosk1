import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

// Background & Layout
import InteractiveHueBackground from './components/background/InteractiveHueBackground';
import SafetyBanner from './components/layout/SafetyBanner';
import Navbar from './components/layout/Navbar';
import HelpModal from './components/layout/HelpModal';

// Landing Page Components (Step 1)
import HeroSection from './components/landing/HeroSection';
import HowMediKioskHelps from './components/landing/HowMediKioskHelps';

// Wizard Steps (Steps 2 to 8)
import WizardProgressBar from './components/wizard/WizardProgressBar';
import Step2Language from './components/wizard/Step2Language';
import Step3PatientInfo from './components/wizard/Step3PatientInfo';
import Step4Consent from './components/wizard/Step4Consent';
import Step5Symptoms from './components/wizard/Step5Symptoms';
import Step6DocUpload from './components/wizard/Step6DocUpload';
import Step7SocraticQA from './components/wizard/Step7SocraticQA';
import Step8TriageResult from './components/wizard/Step8TriageResult';

export default function App() {
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedLang, setSelectedLang] = useState('en');
  const [opdMode, setOpdMode] = useState('GENERAL_OPD');
  const [isMuted, setIsMuted] = useState(false);
  const [isHelpOpen, setIsHelpOpen] = useState(false);

  // Form State
  const [patientData, setPatientData] = useState({});
  const [symptomData, setSymptomData] = useState({});
  const [documentData, setDocumentData] = useState({});
  const [socraticData, setSocraticData] = useState({});

  // Audio Guidance
  const speakText = (text) => {
    if (isMuted || !('speechSynthesis' in window)) return;
    try {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.95;
      utterance.pitch = 1.05;
      window.speechSynthesis.speak(utterance);
    } catch (e) {}
  };

  const handleToggleAudio = () => {
    setIsMuted(prev => {
      const nextState = !prev;
      if (nextState && 'speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      return nextState;
    });
  };

  // Step transitions
  const goToStep = (stepNum) => {
    setCurrentStep(stepNum);
    window.scrollTo({ top: 0, behavior: 'smooth' });

    // Step-specific speech prompt
    if (stepNum === 2) speakText("Please choose your preferred language.");
    if (stepNum === 3) speakText("Please provide your patient identification details.");
    if (stepNum === 4) speakText("Please review the patient consent and privacy notice.");
    if (stepNum === 5) speakText("Please speak or enter what symptoms you are experiencing.");
    if (stepNum === 6) speakText("You can upload prior prescriptions or skip to continue.");
    if (stepNum === 7) speakText("Please answer a few follow-up clinical questions.");
    if (stepNum === 8) speakText("Your intake is complete. Please collect your queue token.");
  };

  const handleReset = () => {
    setCurrentStep(1);
    setPatientData({});
    setSymptomData({});
    setDocumentData({});
    setSocraticData({});
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="relative min-h-screen flex flex-col font-sans selection:bg-emerald-100 selection:text-emerald-900">
      
      {/* 60fps Interactive Greenish Hues Background */}
      <InteractiveHueBackground />

      {/* Top Physician-in-the-Loop Safety Notice */}
      <SafetyBanner />

      {/* Main Navbar */}
      <Navbar
        currentLang={selectedLang}
        opdMode={opdMode}
        onSwitchOpd={() => setOpdMode(prev => prev === 'AYUSH' ? 'GENERAL_OPD' : 'AYUSH')}
        onLanguageClick={() => goToStep(2)}
        onOpenHelp={() => setIsHelpOpen(true)}
      />

      {/* Wizard Progress Bar (Steps 2 to 8) */}
      <WizardProgressBar
        currentStep={currentStep}
        totalSteps={8}
        onStepClick={goToStep}
        onBack={() => goToStep(Math.max(1, currentStep - 1))}
      />

      {/* Main Interactive Screen with Smooth Framer Motion Transitions */}
      <main className="flex-1 z-10">
        <AnimatePresence mode="wait">
          
          {/* Step 1: Landing Page (Hero + How MediKiosk Helps You) */}
          {currentStep === 1 && (
            <motion.div
              key="step-1"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.35 }}
            >
              <HeroSection
                onBeginCheckIn={() => goToStep(2)}
                onToggleAudio={handleToggleAudio}
                isMuted={isMuted}
              />
              <HowMediKioskHelps />
            </motion.div>
          )}

          {/* Step 2: Language Selection */}
          {currentStep === 2 && (
            <motion.div
              key="step-2"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.35 }}
            >
              <Step2Language
                selectedLang={selectedLang}
                onSelectLang={(lang) => setSelectedLang(lang)}
                onNext={() => goToStep(3)}
              />
            </motion.div>
          )}

          {/* Step 3: Patient Info */}
          {currentStep === 3 && (
            <motion.div
              key="step-3"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.35 }}
            >
              <Step3PatientInfo
                initialData={patientData}
                onNext={(data) => {
                  setPatientData(data);
                  goToStep(4);
                }}
              />
            </motion.div>
          )}

          {/* Step 4: Consent & Terms */}
          {currentStep === 4 && (
            <motion.div
              key="step-4"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.35 }}
            >
              <Step4Consent
                onConsent={() => goToStep(5)}
                onToggleAudio={handleToggleAudio}
                isMuted={isMuted}
              />
            </motion.div>
          )}

          {/* Step 5: Symptoms & Voice Intake */}
          {currentStep === 5 && (
            <motion.div
              key="step-5"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.35 }}
            >
              <Step5Symptoms
                currentLang={selectedLang}
                initialData={symptomData}
                onNext={(data) => {
                  setSymptomData(data);
                  goToStep(6);
                }}
              />
            </motion.div>
          )}

          {/* Step 6: Document Upload & OCR */}
          {currentStep === 6 && (
            <motion.div
              key="step-6"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.35 }}
            >
              <Step6DocUpload
                onNext={(data) => {
                  setDocumentData(data);
                  goToStep(7);
                }}
              />
            </motion.div>
          )}

          {/* Step 7: Clinical AI Socratic Questions */}
          {currentStep === 7 && (
            <motion.div
              key="step-7"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              transition={{ duration: 0.35 }}
            >
              <Step7SocraticQA
                symptomData={symptomData}
                onNext={(data) => {
                  setSocraticData(data);
                  goToStep(8);
                }}
              />
            </motion.div>
          )}

          {/* Step 8: Triage Result & Queue Token */}
          {currentStep === 8 && (
            <motion.div
              key="step-8"
              initial={{ opacity: 0, scale: 0.98 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.98 }}
              transition={{ duration: 0.4 }}
            >
              <Step8TriageResult
                sessionSummary={{
                  ...patientData,
                  ...symptomData,
                  documentData,
                  socraticData
                }}
                onReset={handleReset}
              />
            </motion.div>
          )}

        </AnimatePresence>
      </main>

      {/* Footer */}
      <footer className="w-full max-w-7xl mx-auto px-4 py-8 text-center text-xs text-slate-500 z-10 border-t border-slate-200/60 mt-auto">
        <div className="flex flex-wrap items-center justify-center gap-4 mb-2 font-medium">
          <span>Ayushman Bharat Digital Mission (ABDM) Compatible</span>
          <span>•</span>
          <span>NABH Digital Health Compliant</span>
          <span>•</span>
          <span>Physician-in-the-Loop Safeguards</span>
        </div>
        <p className="text-slate-400 text-[11px]">
          © {new Date().getFullYear()} MediKiosk Clinical Intelligence Platform. All rights reserved.
        </p>
      </footer>

      {/* Interactive Help Modal */}
      <HelpModal
        isOpen={isHelpOpen}
        onClose={() => setIsHelpOpen(false)}
      />

    </div>
  );
}

import React, { useState } from 'react';
import { ShieldCheck, Volume2, ArrowRight } from 'lucide-react';

export default function Step4Consent({ onConsent, onToggleAudio, isMuted }) {
  const [hasAccepted, setHasAccepted] = useState(false);

  const consentPoints = [
    {
      title: "Physician-in-the-Loop Care",
      text: "MediKiosk is an intake assistant, not a doctor. Your consultation physician personally evaluates your symptoms, performs examinations, and writes all prescriptions."
    },
    {
      title: "ABDM Privacy & Confidentiality",
      text: "Your health records and Ayushman Bharat Health Account (ABHA) details are strictly confidential and shared only with your treating hospital doctors."
    },
    {
      title: "Voice & Accessibility Assistance",
      text: "Clear spoken voice guidance and speech recognition are provided so all patients, regardless of literacy level, can comfortably complete check-in."
    },
    {
      title: "Urgent Emergency Priority",
      text: "If severe or critical symptoms (such as acute chest pressure or severe breathing difficulty) are detected, you will be flagged for immediate emergency priority attention."
    },
    {
      title: "Attendant & Staff Support",
      text: "A family member or attendant is welcome to assist you with registration, and hospital helpdesk staff are available at any time."
    }
  ];

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-6">
      <div className="bg-white/95 backdrop-blur-md rounded-3xl p-6 sm:p-10 border border-slate-200/80 shadow-lg">
        
        {/* Header matching image */}
        <div className="flex items-center justify-between gap-4 pb-4 border-b border-slate-100 mb-6">
          <div className="flex items-center gap-3.5">
            <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-200 flex items-center justify-center shrink-0">
              <ShieldCheck className="w-5 h-5 text-[#0d382d]" />
            </div>
            <h2 className="text-xl sm:text-2xl font-serif font-bold text-[#0d382d] tracking-tight">
              Patient Consent and Privacy Notice
            </h2>
          </div>

          <button
            type="button"
            onClick={onToggleAudio}
            className="p-2.5 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 shadow-2xs transition-all cursor-pointer"
            title="Listen to Consent Notice"
          >
            <Volume2 className="w-4 h-4" />
          </button>
        </div>

        {/* Descriptive Text */}
        <div className="space-y-2.5 text-xs sm:text-sm text-slate-600 leading-relaxed mb-6">
          <p>
            Before starting your pre-consultation intake, please review and accept how your medical information will be processed.
          </p>
          <p>
            By proceeding, you consent to MediKiosk processing your health symptoms and medical documents using AI to prepare a clinical summary for your attending physician. MediKiosk does not replace medical advice.
          </p>
        </div>

        {/* Tinted Box with Bullet Points */}
        <div className="bg-[#f4fbf7] border border-emerald-100/90 rounded-2xl p-5 sm:p-7 space-y-4 mb-8">
          {consentPoints.map((item, index) => (
            <div key={index} className="flex items-start gap-3 text-xs sm:text-sm text-slate-700 leading-relaxed">
              <span className="w-2 h-2 rounded-full bg-[#059669] shrink-0 mt-1.5" />
              <div>
                <strong className="font-bold text-slate-900">{item.title}: </strong>
                <span>{item.text}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Checkbox acceptance & Proceed Action */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pt-2">
          <label className="flex items-center gap-3 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={hasAccepted}
              onChange={(e) => setHasAccepted(e.target.checked)}
              className="w-5 h-5 rounded-md border-slate-300 text-[#0d382d] focus:ring-emerald-500 cursor-pointer accent-[#0d382d]"
            />
            <span className="text-xs sm:text-sm font-semibold text-slate-800">
              I have read, understood, and accept the clinical consent terms above
            </span>
          </label>

          <button
            type="button"
            onClick={() => {
              if (hasAccepted) onConsent();
            }}
            disabled={!hasAccepted}
            className={`inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-full font-bold text-sm sm:text-base shadow-md transition-all ${
              hasAccepted
                ? 'bg-[#0d382d] hover:bg-[#134e3f] text-white hover:scale-102 cursor-pointer'
                : 'bg-slate-200 text-slate-400 cursor-not-allowed'
            }`}
          >
            <span>I Consent &amp; Proceed</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

      </div>
    </div>
  );
}

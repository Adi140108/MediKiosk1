import React, { useEffect } from 'react';
import { CheckCircle, QrCode, Printer, RotateCcw, AlertTriangle, Clock, MapPin, Building } from 'lucide-react';
import confetti from 'canvas-confetti';

export default function Step8TriageResult({ sessionSummary = {}, onReset }) {
  const isUrgent = sessionSummary.complaint?.toLowerCase().includes('chest') || 
                   sessionSummary.symptomData?.complaint?.toLowerCase().includes('chest') ||
                   sessionSummary.painLevel >= 7;

  const department = isUrgent ? "Cardiology & Emergency OPD" : "General Medicine & AYUSH OPD";
  const room = isUrgent ? "Room 102, Ground Floor (Rapid Evaluation)" : "Room 205, 2nd Floor";
  const priority = isUrgent ? "URGENT / HIGH" : "ROUTINE";
  const tokenNumber = isUrgent ? "EMG-014" : "OPD-058";
  const estWait = isUrgent ? "Immediate (Under 5 mins)" : "~15-20 minutes";

  useEffect(() => {
    try {
      confetti({
        particleCount: 50,
        spread: 60,
        origin: { y: 0.6 }
      });
    } catch (e) {}
  }, []);

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-6">
      <div className="bg-white/95 backdrop-blur-md rounded-3xl p-6 sm:p-10 border border-slate-200/80 shadow-xl">
        
        {/* Success Header */}
        <div className="text-center max-w-xl mx-auto mb-8">
          <div className="w-16 h-16 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center mx-auto mb-3 shadow-sm">
            <CheckCircle className="w-8 h-8" />
          </div>
          <h2 className="text-2xl sm:text-3xl font-serif font-bold text-[#0d382d]">
            Check-In Completed Successfully!
          </h2>
          <p className="text-sm text-slate-600 mt-1">
            Your clinical intake and documents have been synchronized with your attending doctor.
          </p>
        </div>

        {/* Token Card */}
        <div className="max-w-lg mx-auto bg-gradient-to-br from-[#0b382d] to-[#041d17] text-white rounded-3xl p-6 sm:p-8 shadow-2xl border border-emerald-900/50 mb-8 relative overflow-hidden">
          
          {/* Subtle watermark background */}
          <div className="absolute right-[-20px] bottom-[-20px] opacity-10 pointer-events-none">
            <QrCode className="w-56 h-56 text-white" />
          </div>

          <div className="flex items-center justify-between border-b border-white/15 pb-4 mb-5">
            <div>
              <span className="text-[11px] uppercase tracking-widest text-emerald-300 font-bold">
                Hospital OPD Queue Token
              </span>
              <h3 className="text-3xl font-bold font-serif tracking-tight mt-0.5">
                {tokenNumber}
              </h3>
            </div>

            <span className={`px-3 py-1 rounded-full text-xs font-bold tracking-wide uppercase ${
              isUrgent ? 'bg-rose-500/90 text-white animate-pulse' : 'bg-emerald-500/90 text-white'
            }`}>
              {priority} Priority
            </span>
          </div>

          {/* Details list */}
          <div className="space-y-3.5 text-xs sm:text-sm">
            <div className="flex items-start gap-3">
              <Building className="w-4 h-4 text-emerald-300 shrink-0 mt-0.5" />
              <div>
                <span className="text-emerald-200/80 block text-[11px]">Assigned Department</span>
                <span className="font-bold text-white text-base">{department}</span>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <MapPin className="w-4 h-4 text-emerald-300 shrink-0 mt-0.5" />
              <div>
                <span className="text-emerald-200/80 block text-[11px]">Consultation Location</span>
                <span className="font-semibold text-white">{room}</span>
              </div>
            </div>

            <div className="flex items-start gap-3">
              <Clock className="w-4 h-4 text-emerald-300 shrink-0 mt-0.5" />
              <div>
                <span className="text-emerald-200/80 block text-[11px]">Estimated Wait Time</span>
                <span className="font-semibold text-white">{estWait}</span>
              </div>
            </div>
          </div>

          {/* SMS Notice */}
          <div className="mt-6 pt-4 border-t border-white/10 text-[11px] text-emerald-100/70 flex items-center justify-between">
            <span>SMS sent to {sessionSummary.phone || "your mobile"}</span>
            <span className="font-mono text-emerald-300">ABDM #9284</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <button
            type="button"
            onClick={() => window.print()}
            className="inline-flex items-center justify-center gap-2 px-6 py-3 rounded-full border border-slate-300 bg-white hover:bg-slate-50 text-slate-800 font-bold text-xs sm:text-sm shadow-xs transition-all cursor-pointer w-full sm:w-auto"
          >
            <Printer className="w-4 h-4" />
            <span>Print Physical Slip</span>
          </button>

          <button
            type="button"
            onClick={onReset}
            className="inline-flex items-center justify-center gap-2 px-8 py-3 rounded-full bg-[#0d382d] hover:bg-[#134e3f] text-white font-bold text-xs sm:text-sm shadow-md transition-all hover:scale-102 cursor-pointer w-full sm:w-auto"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Finish &amp; Return to Kiosk Home</span>
          </button>
        </div>

      </div>
    </div>
  );
}

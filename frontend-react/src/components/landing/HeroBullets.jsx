import React from 'react';
import { CheckCircle2, Sparkles, Mic, Clock } from 'lucide-react';

export default function HeroBullets() {
  const points = [
    {
      icon: Clock,
      title: "Pre-Consultation Intake",
      desc: "Complete your medical intake seamlessly before seeing your doctor."
    },
    {
      icon: Sparkles,
      title: "AI Clinical Intelligence",
      desc: "Captures and profiles your symptoms accurately with smart clinical AI."
    },
    {
      icon: Mic,
      title: "Hands-Free Voice",
      desc: "Speak naturally in your preferred tongue with 10 Indian languages supported."
    }
  ];

  return (
    <div className="bg-emerald-50/65 border border-emerald-200/70 rounded-2xl p-4 sm:p-5 shadow-2xs flex flex-col gap-3 my-1 sm:my-2">
      {points.map((pt, idx) => {
        return (
          <div key={idx} className="flex items-start gap-3 group">
            <div className="w-5 h-5 rounded-full bg-emerald-200/80 text-emerald-800 flex items-center justify-center shrink-0 mt-0.5 group-hover:bg-emerald-300/80 transition-colors">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-800" />
            </div>
            <div className="text-xs sm:text-sm text-slate-700 leading-snug">
              <span className="font-bold text-[#0d382d]">{pt.title}: </span>
              <span className="text-slate-600">{pt.desc}</span>
            </div>
          </div>
        );
      })}
    </div>
  );
}

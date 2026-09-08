import React from 'react';
import { ShieldCheck } from 'lucide-react';

export default function SafetyBanner() {
  return (
    <div className="w-full bg-[#f4fbf7] border-b border-emerald-100/90 px-4 py-1.5 text-xs text-emerald-950 flex items-center justify-center gap-2 z-20 relative text-center">
      <ShieldCheck className="w-3.5 h-3.5 text-emerald-700 shrink-0" />
      <span className="leading-tight text-slate-700">
        <strong className="font-semibold text-emerald-900">Clinical Notice:</strong> Pre-consultation intake only — all diagnoses &amp; prescriptions are provided by your doctor.
      </span>
    </div>
  );
}


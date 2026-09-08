import React from 'react';
import { HelpCircle, Stethoscope, Globe } from 'lucide-react';

export default function Navbar({ onOpenHelp, onLanguageClick, opdMode, onSwitchOpd, currentLang = 'EN' }) {
  return (
    <header className="w-full bg-white border-b border-slate-200/90 shadow-2xs z-20 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3.5 flex flex-wrap items-center justify-between gap-4">
        {/* Brand Logo & Tagline */}
        <div 
          onClick={() => window.location.reload()} 
          className="flex items-center gap-3 cursor-pointer group select-none"
        >
          <img 
            src="/logo.png" 
            alt="MediKiosk" 
            className="h-10 sm:h-12 w-auto object-contain rounded-xl shadow-xs transition-transform group-hover:scale-105"
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
          <div className="flex flex-col">
            <span className="text-xl sm:text-2xl font-serif font-bold tracking-tight text-[#0d382d]">
              MediKiosk
            </span>
            <span className="text-[10px] sm:text-[11px] font-bold tracking-widest text-[#965b26] uppercase">
              TRADITIONAL WISDOM. MODERN CARE.
            </span>
          </div>
        </div>

        {/* Nav Actions */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Help button */}
          <button
            type="button"
            onClick={onOpenHelp}
            className="inline-flex items-center gap-1.5 h-9 px-3 sm:px-3.5 rounded-xl text-xs font-semibold text-slate-700 bg-slate-100/90 hover:bg-slate-200/80 border border-slate-200/90 transition-all hover:scale-102 cursor-pointer shadow-2xs"
            title="Learn how MediKiosk works"
          >
            <HelpCircle className="w-3.5 h-3.5 text-slate-600" />
            <span className="hidden xs:inline">How does this work?</span>
          </button>

          {/* OPD Mode Pill - Single crisp Stethoscope icon, no emojis, no extra gear */}
          <button
            type="button"
            onClick={onSwitchOpd}
            className="inline-flex items-center gap-2 h-9 px-4 rounded-xl text-xs font-bold text-white bg-[#0d382d] hover:bg-[#134e3f] shadow-xs transition-all hover:scale-102 cursor-pointer"
            title="Staff: Switch OPD Mode"
          >
            <Stethoscope className="w-3.5 h-3.5 text-emerald-300 shrink-0" />
            <span className="tracking-wide">{opdMode === 'AYUSH' ? 'AYUSH OPD' : 'GENERAL OPD'}</span>
          </button>

          {/* Language Pill - In Dark Green */}
          <button
            type="button"
            onClick={onLanguageClick}
            className="inline-flex items-center gap-1.5 h-9 px-3.5 rounded-xl text-xs font-bold text-white bg-[#0d382d] hover:bg-[#134e3f] shadow-xs transition-all hover:scale-102 cursor-pointer"
            title="Tap to change language"
          >
            <Globe className="w-3.5 h-3.5 text-emerald-300 shrink-0" />
            <span className="tracking-wider">{currentLang.toUpperCase()}</span>
          </button>
        </div>
      </div>
    </header>
  );
}


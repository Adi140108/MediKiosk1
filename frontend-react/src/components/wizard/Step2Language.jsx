import React from 'react';
import { Globe, ArrowRight, Check } from 'lucide-react';

export default function Step2Language({ selectedLang, onSelectLang, onNext }) {
  const languages = [
    { code: 'en', name: 'English', native: 'English', region: 'Pan-India / International' },
    { code: 'hi', name: 'Hindi', native: 'हिन्दी', region: 'North & Central India' },
    { code: 'kn', name: 'Kannada', native: 'ಕನ್ನಡ', region: 'Karnataka' },
    { code: 'ta', name: 'Tamil', native: 'தமிழ்', region: 'Tamil Nadu' },
    { code: 'te', name: 'Telugu', native: 'తెలుగు', region: 'Andhra Pradesh & Telangana' },
    { code: 'ml', name: 'Malayalam', native: 'മലയാളം', region: 'Kerala' },
    { code: 'mr', name: 'Marathi', native: 'मराठी', region: 'Maharashtra' },
    { code: 'bn', name: 'Bengali', native: 'বাংলা', region: 'West Bengal' },
    { code: 'gu', name: 'Gujarati', native: 'ગુજરાતી', region: 'Gujarat' },
    { code: 'pa', name: 'Punjabi', native: 'ਪੰਜਾਬੀ', region: 'Punjab' }
  ];

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-6">
      <div className="bg-white/95 backdrop-blur-md rounded-3xl p-6 sm:p-10 border border-slate-200/80 shadow-lg">
        
        {/* Header */}
        <div className="text-center max-w-xl mx-auto mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-100/80 text-emerald-800 text-xs font-bold mb-3">
            <Globe className="w-3.5 h-3.5 text-emerald-600" />
            <span>Multilingual Intake</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-serif font-bold text-[#0d382d]">
            Choose Your Preferred Language
          </h2>
          <p className="text-sm text-slate-600 mt-1">
            MediKiosk will speak, listen, and record your clinical answers in this tongue.
          </p>
        </div>

        {/* Language Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 gap-3.5 sm:gap-4 mb-8">
          {languages.map((lang) => {
            const isSelected = selectedLang === lang.code;
            return (
              <div
                key={lang.code}
                onClick={() => onSelectLang(lang.code)}
                className={`relative flex items-center justify-between p-4 sm:p-5 rounded-2xl border-2 transition-all cursor-pointer ${
                  isSelected
                    ? 'border-emerald-600 bg-emerald-50/70 shadow-sm scale-[1.01]'
                    : 'border-slate-200 hover:border-emerald-300 bg-white hover:bg-emerald-50/20'
                }`}
              >
                <div className="flex flex-col">
                  <span className="text-xl sm:text-2xl font-bold text-slate-900 font-serif">
                    {lang.native}
                  </span>
                  <span className="text-xs font-semibold text-slate-600 mt-0.5">
                    {lang.name} <span className="text-slate-400 font-normal">({lang.region})</span>
                  </span>
                </div>

                <div className={`w-6 h-6 rounded-full flex items-center justify-center border ${
                  isSelected 
                    ? 'bg-emerald-600 border-emerald-600 text-white' 
                    : 'border-slate-300 bg-white'
                }`}>
                  {isSelected && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                </div>
              </div>
            );
          })}
        </div>

        {/* Continue Action */}
        <div className="flex justify-end">
          <button
            onClick={onNext}
            className="inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-full bg-[#0d382d] hover:bg-[#134e3f] text-white font-bold text-sm sm:text-base shadow-md transition-all hover:scale-102 cursor-pointer w-full sm:w-auto"
          >
            <span>Confirm &amp; Proceed</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

      </div>
    </div>
  );
}

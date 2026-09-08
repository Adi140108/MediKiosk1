import React, { useState } from 'react';
import { Brain, Sparkles, ArrowRight, CheckCircle2 } from 'lucide-react';

export default function Step7SocraticQA({ symptomData = {}, onNext }) {
  const [answers, setAnswers] = useState({
    onset: 'Sudden onset (within hours)',
    radiation: 'Radiates to left shoulder or neck',
    aggravating: 'Worse during physical exertion or walking',
    ayushAgni: 'Mandagni (Sluggish appetite & digestion)',
    ayushSleep: 'Disturbed sleep due to discomfort'
  });

  const questions = [
    {
      id: 'onset',
      badge: 'Socratic Inquiry',
      badgeColor: 'bg-emerald-100 text-emerald-800',
      question: 'How did this symptom begin?',
      options: [
        'Sudden onset (within hours)',
        'Gradually worsening over days',
        'Intermittent (comes and goes)'
      ]
    },
    {
      id: 'radiation',
      badge: 'Red-Flag Screening',
      badgeColor: 'bg-rose-100 text-rose-800',
      question: 'Does the pain or sensation spread anywhere else?',
      options: [
        'Radiates to left shoulder or neck',
        'Spreads to upper back / shoulder blades',
        'Stays strictly in one spot'
      ]
    },
    {
      id: 'aggravating',
      badge: 'Clinical Context',
      badgeColor: 'bg-teal-100 text-teal-800',
      question: 'What makes the feeling worse or better?',
      options: [
        'Worse during physical exertion or walking',
        'Worse after heavy meals or lying flat',
        'No specific triggers noticed'
      ]
    },
    {
      id: 'ayushAgni',
      badge: 'AYUSH Integrative Intake',
      badgeColor: 'bg-amber-100 text-amber-800',
      question: 'How has your appetite and digestion (Agni) been lately?',
      options: [
        'Mandagni (Sluggish appetite & heaviness)',
        'Tikshnagni (Intense hunger, acidity, heat)',
        'Samagni (Balanced, normal digestion)'
      ]
    }
  ];

  const handleSelectOption = (qId, option) => {
    setAnswers({ ...answers, [qId]: option });
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-6">
      <div className="bg-white/95 backdrop-blur-md rounded-3xl p-6 sm:p-10 border border-slate-200/80 shadow-lg">
        
        {/* Header */}
        <div className="text-center max-w-xl mx-auto mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-teal-100/80 text-teal-800 text-xs font-bold mb-3">
            <Brain className="w-3.5 h-3.5 text-teal-600" />
            <span>Step 7: Clinical AI Follow-Up</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-serif font-bold text-[#0d382d]">
            Targeted Health Questions
          </h2>
          <p className="text-sm text-slate-600 mt-1">
            Socratic clinical inquiry dynamically adapts questions to your symptoms, reviewing dosha equilibrium, pain severity, and duration in real time.
          </p>
        </div>

        {/* Dynamic Questions List */}
        <div className="space-y-6 mb-8">
          {questions.map((q, idx) => (
            <div key={q.id} className="p-5 rounded-2xl bg-slate-50/80 border border-slate-200/90">
              <div className="flex items-center justify-between mb-2">
                <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider ${q.badgeColor}`}>
                  {q.badge}
                </span>
                <span className="text-xs text-slate-400 font-semibold">Q{idx + 1}</span>
              </div>

              <h3 className="text-sm sm:text-base font-bold text-slate-800 mb-3">
                {q.question}
              </h3>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
                {q.options.map((opt, oIdx) => {
                  const isSelected = answers[q.id] === opt;
                  return (
                    <button
                      key={oIdx}
                      type="button"
                      onClick={() => handleSelectOption(q.id, opt)}
                      className={`p-3 rounded-xl text-xs text-left font-semibold transition-all cursor-pointer flex items-start justify-between gap-2 border ${
                        isSelected
                          ? 'bg-[#0d382d] text-white border-[#0d382d] shadow-xs'
                          : 'bg-white text-slate-700 border-slate-200 hover:bg-slate-100/80'
                      }`}
                    >
                      <span>{opt}</span>
                      {isSelected && <CheckCircle2 className="w-3.5 h-3.5 shrink-0 mt-0.5 text-emerald-300" />}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Submit */}
        <div className="flex justify-end pt-2">
          <button
            type="button"
            onClick={() => onNext(answers)}
            className="inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-full bg-[#0d382d] hover:bg-[#134e3f] text-white font-bold text-sm sm:text-base shadow-md transition-all hover:scale-102 cursor-pointer w-full sm:w-auto"
          >
            <span>Generate Triage &amp; Queue Token</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

      </div>
    </div>
  );
}

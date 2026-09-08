import React from 'react';
import { Check, ArrowLeft } from 'lucide-react';

export default function WizardProgressBar({ currentStep, totalSteps = 8, onStepClick, onBack }) {
  if (currentStep <= 1) return null;

  return (
    <div className="w-full max-w-4xl mx-auto px-4 pt-3 pb-6">
      {/* Top back & step indicator row */}
      <div className="flex items-center justify-between mb-4">
        <button
          type="button"
          onClick={onBack}
          className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold text-slate-700 bg-white/90 hover:bg-white border border-slate-200 shadow-2xs hover:scale-102 transition-all cursor-pointer"
        >
          <ArrowLeft className="w-3.5 h-3.5 text-emerald-800" />
          <span>Back</span>
        </button>

        <div className="text-xs font-bold text-emerald-900 bg-emerald-100/90 px-3.5 py-1 rounded-full border border-emerald-200 shadow-2xs">
          Step {currentStep} of {totalSteps}
        </div>
      </div>

      {/* Progress Track matching reference image */}
      <div className="bg-white/80 backdrop-blur-md rounded-2xl px-3 sm:px-6 py-3.5 border border-slate-200/70 shadow-xs">
        <div className="flex items-center justify-between relative">
          {Array.from({ length: totalSteps }, (_, i) => {
            const stepNum = i + 1;
            const isCompleted = stepNum < currentStep;
            const isActive = stepNum === currentStep;

            return (
              <React.Fragment key={stepNum}>
                {/* Node */}
                <button
                  type="button"
                  onClick={() => {
                    if (isCompleted) onStepClick(stepNum);
                  }}
                  disabled={!isCompleted && !isActive}
                  className={`relative z-10 flex items-center justify-center transition-all duration-300 select-none ${
                    isCompleted
                      ? 'w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-[#059669] text-white shadow-xs cursor-pointer hover:bg-emerald-700'
                      : isActive
                        ? 'w-9 h-9 sm:w-10 sm:h-10 rounded-full bg-[#0d382d] text-white font-bold ring-4 ring-emerald-900/15 shadow-md scale-105'
                        : 'w-8 h-8 sm:w-9 sm:h-9 rounded-full bg-[#f1f5f3] text-slate-400 font-semibold border border-slate-200/90'
                  }`}
                  title={`Step ${stepNum}`}
                >
                  {isCompleted ? (
                    <Check className="w-4 h-4 stroke-[3] text-white" />
                  ) : (
                    <span className="text-xs sm:text-sm">{stepNum}</span>
                  )}
                </button>

                {/* Connecting Line */}
                {stepNum < totalSteps && (
                  <div className="flex-1 h-[3px] mx-1 sm:mx-2 rounded-full overflow-hidden bg-[#e2e8f0]">
                    <div
                      className={`h-full transition-all duration-500 rounded-full ${
                        stepNum < currentStep ? 'bg-[#059669] w-full' : 'w-0'
                      }`}
                    />
                  </div>
                )}
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
}

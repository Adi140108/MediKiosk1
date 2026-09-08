import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Mic, Brain, Camera, FileCheck2 } from 'lucide-react';

export default function HelpModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 15 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 15 }}
          className="relative w-full max-w-xl bg-white rounded-3xl p-6 sm:p-8 shadow-2xl border border-slate-100 overflow-hidden"
        >
          {/* Header */}
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <h3 className="text-xl font-serif font-bold text-[#0d382d]">
                How MediKiosk Works
              </h3>
              <p className="text-xs text-slate-500 mt-0.5">
                4-step automated clinical intake before you see the doctor
              </p>
            </div>
            <button
              onClick={onClose}
              className="w-8 h-8 rounded-full bg-slate-100 hover:bg-slate-200 text-slate-600 flex items-center justify-center cursor-pointer transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Steps list */}
          <div className="mt-5 space-y-4">
            <div className="flex gap-3.5 items-start">
              <div className="w-9 h-9 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shrink-0">
                <Mic className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-slate-800">1. Speak or Type Symptoms</h4>
                <p className="text-xs text-slate-600 leading-relaxed mt-0.5">
                  Choose from 10 Indian languages. Speak naturally into the microphone or use the touchscreen to describe what hurts.
                </p>
              </div>
            </div>

            <div className="flex gap-3.5 items-start">
              <div className="w-9 h-9 rounded-xl bg-teal-100 text-teal-700 flex items-center justify-center shrink-0">
                <Brain className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-slate-800">2. Adaptive Clinical & AYUSH Inquiries</h4>
                <p className="text-xs text-slate-600 leading-relaxed mt-0.5">
                  MediKiosk asks tailored follow-up questions to understand severity, duration, and dosha balance.
                </p>
              </div>
            </div>

            <div className="flex gap-3.5 items-start">
              <div className="w-9 h-9 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center shrink-0">
                <Camera className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-slate-800">3. Scan Past Prescriptions</h4>
                <p className="text-xs text-slate-600 leading-relaxed mt-0.5">
                  Hold prior prescriptions or lab reports up to the camera. Document OCR extracts prior diagnoses and medications.
                </p>
              </div>
            </div>

            <div className="flex gap-3.5 items-start">
              <div className="w-9 h-9 rounded-xl bg-purple-100 text-purple-700 flex items-center justify-center shrink-0">
                <FileCheck2 className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-slate-800">4. Triage & Direct Physician Sync</h4>
                <p className="text-xs text-slate-600 leading-relaxed mt-0.5">
                  Deterministic triage routes you to the correct department with a queue token, transmitting your summary directly to the doctor.
                </p>
              </div>
            </div>
          </div>

          {/* Footer close */}
          <div className="mt-6 pt-4 border-t border-slate-100 flex justify-end">
            <button
              onClick={onClose}
              className="px-5 py-2 rounded-full bg-[#0d382d] text-white font-semibold text-xs shadow-md hover:bg-[#165042] transition-colors cursor-pointer"
            >
              Got it, let's start
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

import React, { useState } from 'react';
import { Mic, MicOff, Activity, ArrowRight, AlertCircle, Sparkles } from 'lucide-react';
import { motion } from 'framer-motion';

export default function Step5Symptoms({ initialData = {}, onNext, currentLang = 'en' }) {
  const [complaint, setComplaint] = useState(initialData.complaint || '');
  const [painLevel, setPainLevel] = useState(initialData.painLevel || 3);
  const [duration, setDuration] = useState(initialData.duration || '2-3 days');
  const [isRecording, setIsRecording] = useState(false);
  const [selectedChips, setSelectedChips] = useState(initialData.selectedChips || []);

  const commonSymptoms = [
    "Chest Pain / Heaviness",
    "Shortness of Breath",
    "Persistent Cough & Cold",
    "High Fever & Chills",
    "Severe Throbbing Headache",
    "Abdominal Cramps / Nausea",
    "Joint Pain & Stiffness",
    "Dizziness & Fatigue",
    "Skin Rash / Itching",
    "Acid Reflux / Indigestion"
  ];

  const handleToggleChip = (sym) => {
    if (selectedChips.includes(sym)) {
      setSelectedChips(selectedChips.filter(s => s !== sym));
    } else {
      setSelectedChips([...selectedChips, sym]);
      if (!complaint.includes(sym)) {
        setComplaint(prev => prev ? `${prev}, ${sym}` : sym);
      }
    }
  };

  const handleToggleRecord = () => {
    if (!isRecording) {
      // Start recording
      setIsRecording(true);
      if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRec();
        recognition.lang = currentLang === 'hi' ? 'hi-IN' : 'en-IN';
        recognition.interimResults = true;
        
        recognition.onresult = (e) => {
          const transcript = Array.from(e.results)
            .map(result => result[0])
            .map(result => result.transcript)
            .join('');
          setComplaint(transcript);
        };

        recognition.onerror = () => setIsRecording(false);
        recognition.onend = () => setIsRecording(false);

        recognition.start();
      } else {
        setTimeout(() => {
          setIsRecording(false);
          setComplaint(prev => prev ? `${prev} (Voice simulated: Feeling pain for 2 days)` : "Feeling pain and heaviness since yesterday");
        }, 3000);
      }
    } else {
      setIsRecording(false);
    }
  };

  const getPainColor = (lvl) => {
    if (lvl <= 3) return 'bg-emerald-500 text-white';
    if (lvl <= 6) return 'bg-amber-500 text-white';
    if (lvl <= 8) return 'bg-orange-500 text-white';
    return 'bg-red-600 text-white';
  };

  const getPainDescription = (lvl) => {
    if (lvl === 0) return "No Pain";
    if (lvl <= 3) return "Mild (Noticeable, manageable)";
    if (lvl <= 6) return "Moderate (Interferes with daily tasks)";
    if (lvl <= 8) return "Severe (Hard to ignore, intense)";
    return "Worst Possible / Critical (Disabling)";
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!complaint.trim() && selectedChips.length === 0) {
      alert("Please enter or speak your primary symptom");
      return;
    }
    onNext({
      complaint: complaint || selectedChips.join(', '),
      painLevel,
      duration,
      selectedChips
    });
  };

  return (
    <div className="w-full max-w-4xl mx-auto px-4 py-6">
      <div className="bg-white/95 backdrop-blur-md rounded-3xl p-6 sm:p-10 border border-slate-200/80 shadow-lg">
        
        {/* Header */}
        <div className="text-center max-w-xl mx-auto mb-8">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-100/80 text-emerald-800 text-xs font-bold mb-3">
            <Activity className="w-3.5 h-3.5 text-emerald-600" />
            <span>Step 5: Chief Complaint</span>
          </div>
          <h2 className="text-2xl sm:text-3xl font-serif font-bold text-[#0d382d]">
            What Brings You In Today?
          </h2>
          <p className="text-sm text-slate-600 mt-1">
            Speak using the microphone or type what symptoms you are experiencing.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          
          {/* Voice Input Section with Live Waveform Simulation */}
          <div className="flex flex-col items-center justify-center p-6 rounded-2xl bg-gradient-to-b from-emerald-50/60 to-teal-50/40 border border-emerald-100/80">
            <motion.button
              type="button"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleToggleRecord}
              className={`w-20 h-20 sm:w-22 sm:h-22 rounded-full flex items-center justify-center shadow-lg transition-all cursor-pointer ${
                isRecording
                  ? 'bg-red-500 text-white ring-8 ring-red-200 animate-pulse'
                  : 'bg-[#0d382d] text-white hover:bg-[#154e3f] ring-6 ring-emerald-100'
              }`}
            >
              {isRecording ? <MicOff className="w-8 h-8" /> : <Mic className="w-8 h-8" />}
            </motion.button>

            <span className="text-xs font-bold tracking-wide mt-3 text-slate-700">
              {isRecording ? "Listening... Speak your symptoms" : "Tap to Speak (Hands-Free Voice)"}
            </span>

            {/* Simulated Live Audio Waveform Bars */}
            {isRecording && (
              <div className="flex items-center gap-1 mt-3 h-7">
                {[40, 70, 95, 30, 80, 100, 60, 90, 45, 85, 55, 95, 35].map((h, i) => (
                  <motion.div
                    key={i}
                    animate={{ height: ['20%', `${h}%`, '30%'] }}
                    transition={{ duration: 0.5 + (i % 3) * 0.2, repeat: Infinity, ease: 'easeInOut' }}
                    className="w-1 bg-emerald-600 rounded-full"
                  />
                ))}
              </div>
            )}
          </div>

          {/* Chief Complaint Textarea */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2 flex items-center justify-between">
              <span>Symptom Description *</span>
              <span className="text-slate-400 font-normal lowercase text-[11px]">voice or text</span>
            </label>
            <textarea
              rows={3}
              placeholder="e.g. Having severe chest tightness radiating to the left arm for 2 hours..."
              value={complaint}
              onChange={(e) => setComplaint(e.target.value)}
              className="w-full px-4 py-3 rounded-xl border border-slate-300 focus:border-emerald-600 focus:ring-2 focus:ring-emerald-100 outline-none text-slate-800 text-sm transition-all resize-none"
            />
          </div>

          {/* Quick Symptom Chips */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              Common Symptoms (Tap to add)
            </label>
            <div className="flex flex-wrap gap-2">
              {commonSymptoms.map((sym, idx) => {
                const isSelected = selectedChips.includes(sym);
                return (
                  <button
                    key={idx}
                    type="button"
                    onClick={() => handleToggleChip(sym)}
                    className={`px-3.5 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer ${
                      isSelected
                        ? 'bg-[#0d382d] text-white shadow-xs scale-102'
                        : 'bg-slate-100 hover:bg-emerald-50 text-slate-700 border border-slate-200'
                    }`}
                  >
                    {sym}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Pain Scale (1 - 10) */}
          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200">
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                Pain Level (0 - 10 Scale)
              </label>
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${getPainColor(painLevel)}`}>
                Score: {painLevel}/10
              </span>
            </div>

            <input
              type="range"
              min="0"
              max="10"
              value={painLevel}
              onChange={(e) => setPainLevel(Number(e.target.value))}
              className="w-full h-2.5 bg-slate-200 rounded-lg appearance-none cursor-pointer accent-[#0d382d]"
            />

            <div className="flex justify-between text-[10px] text-slate-400 font-semibold mt-1">
              <span>0 (None)</span>
              <span>3 (Mild)</span>
              <span>5 (Moderate)</span>
              <span>8 (Severe)</span>
              <span>10 (Unbearable)</span>
            </div>

            <p className="text-xs text-slate-600 font-medium mt-2">
              Evaluation: <span className="font-bold text-slate-900">{getPainDescription(painLevel)}</span>
            </p>
          </div>

          {/* Duration */}
          <div>
            <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-2">
              How long have you had these symptoms?
            </label>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
              {['Just started today', '2-3 days', '1-2 weeks', 'More than a month'].map((dur, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => setDuration(dur)}
                  className={`py-2 px-3 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                    duration === dur
                      ? 'bg-[#0d382d] text-white shadow-xs'
                      : 'bg-white border border-slate-200 text-slate-700 hover:bg-slate-50'
                  }`}
                >
                  {dur}
                </button>
              ))}
            </div>
          </div>

          {/* Submit Action */}
          <div className="flex justify-end pt-2">
            <button
              type="submit"
              className="inline-flex items-center justify-center gap-2 px-8 py-3.5 rounded-full bg-[#0d382d] hover:bg-[#134e3f] text-white font-bold text-sm sm:text-base shadow-md transition-all hover:scale-102 cursor-pointer w-full sm:w-auto"
            >
              <span>Continue to Documents</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </div>

        </form>

      </div>
    </div>
  );
}

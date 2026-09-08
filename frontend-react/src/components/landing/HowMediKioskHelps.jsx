import React from 'react';
import { Mic, Brain, Camera, FileCheck2 } from 'lucide-react';
import { motion } from 'framer-motion';

export default function HowMediKioskHelps() {
  const cards = [
    {
      pill: "EFFORTLESS ENTRANCE",
      icon: Mic,
      iconBg: "bg-emerald-50 text-emerald-600 border-emerald-100",
      featureLabel: "10 Languages Voice & Touch",
      title: "Voice & Touch Intake",
      description: "Arrive at the kiosk and speak comfortably in your native tongue. Our automated microphone countdown listens and transcribes without medical jargon."
    },
    {
      pill: "ADAPTIVE CLINICAL AI",
      icon: Brain,
      iconBg: "bg-teal-50 text-teal-600 border-teal-100",
      featureLabel: "AYUSH & Clinical Triage",
      title: "Intelligent Assessment",
      description: "Socratic clinical inquiry dynamically adapts questions to your symptoms, reviewing dosha equilibrium, pain severity, and duration in real time."
    },
    {
      pill: "DOCUMENT AI",
      icon: Camera,
      iconBg: "bg-sky-50 text-sky-600 border-sky-100",
      featureLabel: "Camera OCR Scanner",
      title: "Instant Paper OCR",
      description: "Hold past prescriptions, test reports, or discharge slips up to the camera. Document AI extracts diagnosis history and lab values instantly."
    },
    {
      pill: "DIRECT DOCTOR SYNC",
      icon: FileCheck2,
      iconBg: "bg-emerald-50 text-emerald-700 border-emerald-100",
      featureLabel: "ABDM FHIR Bundle",
      title: "Physician Fast-Track",
      description: "Your physician receives an organized, prioritized clinical summary before you walk in. Zero waiting, zero repeating your medical history."
    }
  ];

  return (
    <section className="w-full max-w-7xl mx-auto px-4 sm:px-6 pt-4 pb-12 sm:pb-16">
      {/* Decorative Divider Line Before Section */}
      <div className="w-full max-w-5xl mx-auto mb-10 sm:mb-14 flex items-center justify-center gap-4">
        <div className="flex-1 h-[1.5px] bg-gradient-to-r from-transparent via-emerald-600/35 to-emerald-700/50" />
        <div className="w-2.5 h-2.5 rounded-full bg-emerald-600/60 ring-4 ring-emerald-100" />
        <div className="flex-1 h-[1.5px] bg-gradient-to-l from-transparent via-emerald-600/35 to-emerald-700/50" />
      </div>

      {/* Section Header */}
      <div className="text-center max-w-3xl mx-auto mb-10 sm:mb-14">
        <h2 className="text-2xl sm:text-3xl lg:text-4xl font-serif font-bold text-[#0d382d] tracking-tight mb-2 sm:mb-3">
          How MediKiosk Helps You
        </h2>
        <p className="text-sm sm:text-base text-slate-600 font-normal">
          A smarter, faster patient intake experience for everyone.
        </p>
      </div>

      {/* 4 Cards Grid with Responsive Flow */}
      <div className="relative">
        {/* Subtle Horizontal Connecting Track (visible on desktop) */}
        <div 
          className="hidden lg:block absolute top-[52px] left-[5%] right-[5%] h-[2px] bg-gradient-to-r from-emerald-100 via-teal-100 to-emerald-100 z-0 pointer-events-none"
          aria-hidden="true" 
        />

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 sm:gap-6 relative z-10">
          {cards.map((card, idx) => {
            const IconComponent = card.icon;
            return (
              <motion.div
                key={idx}
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.45, delay: idx * 0.1 }}
                whileHover={{ y: -4 }}
                className="flex flex-col bg-white/90 backdrop-blur-xs rounded-2xl p-5 sm:p-6 border border-slate-200/80 shadow-xs hover:shadow-md hover:border-emerald-200 transition-all duration-300"
              >
                {/* Top Pill Tag (NO step numbers) */}
                <div className="flex items-center justify-between mb-4">
                  <span className="text-[11px] font-bold tracking-wider text-slate-700 bg-slate-100/90 px-2.5 py-1 rounded-full uppercase">
                    {card.pill}
                  </span>
                </div>

                {/* Squircle Icon */}
                <div className={`w-12 h-12 rounded-2xl flex items-center justify-center border mb-3.5 ${card.iconBg} shadow-2xs`}>
                  <IconComponent className="w-5 h-5" />
                </div>

                {/* Feature Label (NO glowing dots) */}
                <div className="mb-2">
                  <span className="text-xs font-semibold text-emerald-800/90 tracking-wide">
                    {card.featureLabel}
                  </span>
                </div>

                {/* Card Title in Editorial Serif */}
                <h3 className="text-lg sm:text-xl font-serif font-bold text-[#0d382d] tracking-tight mb-2">
                  {card.title}
                </h3>

                {/* Description */}
                <p className="text-xs sm:text-sm text-slate-600 leading-relaxed font-normal">
                  {card.description}
                </p>
              </motion.div>
            );
          })}
        </div>
      </div>
    </section>
  );
}

import React from 'react';
import { ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';
import TypewriterHeadline from './TypewriterHeadline';
import HeroBullets from './HeroBullets';
import AnimatedHeartbeatCard from './AnimatedHeartbeatCard';

function SoundWaveIcon({ isMuted }) {
  if (isMuted) {
    return (
      <div className="flex items-center gap-[3px] h-5 px-0.5" aria-hidden="true">
        <span className="w-[3px] h-1.5 rounded-full bg-slate-400" />
        <span className="w-[3px] h-2.5 rounded-full bg-slate-400" />
        <span className="w-[3px] h-1.5 rounded-full bg-slate-400" />
        <span className="w-[3px] h-2.5 rounded-full bg-slate-400" />
        <span className="w-[3px] h-1.5 rounded-full bg-slate-400" />
        <span className="w-[3px] h-2 rounded-full bg-slate-400" />
      </div>
    );
  }

  return (
    <div className="flex items-center gap-[3px] h-5 px-0.5" aria-hidden="true">
      <motion.span 
        className="w-[3px] rounded-full bg-emerald-600"
        animate={{ height: ['8px', '16px', '6px', '8px'] }}
        transition={{ duration: 1.1, repeat: Infinity, ease: 'easeInOut' }}
      />
      <motion.span 
        className="w-[3px] rounded-full bg-emerald-600"
        animate={{ height: ['14px', '8px', '20px', '14px'] }}
        transition={{ duration: 1.3, repeat: Infinity, ease: 'easeInOut', delay: 0.15 }}
      />
      <motion.span 
        className="w-[3px] rounded-full bg-emerald-600"
        animate={{ height: ['20px', '12px', '16px', '20px'] }}
        transition={{ duration: 0.95, repeat: Infinity, ease: 'easeInOut', delay: 0.3 }}
      />
      <motion.span 
        className="w-[3px] rounded-full bg-emerald-600"
        animate={{ height: ['12px', '22px', '8px', '12px'] }}
        transition={{ duration: 1.2, repeat: Infinity, ease: 'easeInOut', delay: 0.1 }}
      />
      <motion.span 
        className="w-[3px] rounded-full bg-emerald-600"
        animate={{ height: ['6px', '14px', '18px', '6px'] }}
        transition={{ duration: 1.0, repeat: Infinity, ease: 'easeInOut', delay: 0.25 }}
      />
      <motion.span 
        className="w-[3px] rounded-full bg-emerald-600"
        animate={{ height: ['10px', '6px', '15px', '10px'] }}
        transition={{ duration: 1.15, repeat: Infinity, ease: 'easeInOut', delay: 0.35 }}
      />
    </div>
  );
}

export default function HeroSection({ onBeginCheckIn, onToggleAudio, isMuted }) {
  return (
    <section className="w-full max-w-7xl mx-auto px-4 sm:px-6 pt-2 pb-8 sm:pb-12">
      {/* THE CRISP WHITE FLOATING CARD CONTAINER */}
      <div className="w-full bg-white rounded-3xl sm:rounded-[36px] p-6 sm:p-10 lg:p-12 shadow-sm border border-slate-100/90 relative">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 lg:gap-12 items-center">
          
          {/* Left Column Content */}
          <div className="lg:col-span-7 flex flex-col gap-5 sm:gap-6">
            
            {/* Typewriter Animated Headline */}
            <TypewriterHeadline />

            {/* Clean Subtext Bullet Points */}
            <HeroBullets />

            {/* Action Area - Centered Sound Wave Button below Begin Check In */}
            <div className="flex flex-col items-start pt-2">
              <div className="flex flex-col items-center gap-2.5 w-full sm:w-auto">
                <button
                  id="btn-begin-checkin"
                  onClick={onBeginCheckIn}
                  className="inline-flex items-center justify-center gap-2.5 px-9 py-4 rounded-xl bg-[#0d382d] hover:bg-[#134e3f] text-white font-bold text-base sm:text-lg shadow-md hover:shadow-lg transition-all transform hover:-translate-y-0.5 active:translate-y-0 cursor-pointer w-full sm:w-auto"
                >
                  <span>Begin Check In</span>
                  <ArrowRight className="w-5 h-5" />
                </button>

                {/* Vertical Sound Wave Button - Centered below Begin Check In */}
                <button
                  onClick={onToggleAudio}
                  className={`px-4 py-2 rounded-xl border transition-all cursor-pointer shadow-2xs flex items-center justify-center ${
                    isMuted 
                      ? 'bg-slate-50 text-slate-400 border-slate-200 hover:bg-slate-100' 
                      : 'bg-emerald-50/80 text-emerald-800 border-emerald-200/90 hover:bg-emerald-100/90'
                  }`}
                  title={isMuted ? "Click to turn voice guidance on" : "Click to mute voice guidance"}
                  aria-label="Toggle Voice Guidance"
                >
                  <SoundWaveIcon isMuted={isMuted} />
                </button>
              </div>
            </div>
          </div>

          {/* Right Column: Dark Emerald Card with Animated Heartbeat */}
          <div className="lg:col-span-5 w-full">
            <AnimatedHeartbeatCard />
          </div>

        </div>
      </div>
    </section>
  );
}


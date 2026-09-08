import React from 'react';
import { Heart } from 'lucide-react';
import { motion } from 'framer-motion';

export default function AnimatedHeartbeatCard() {
  // 8 floating luminous bokeh spheres drifting organically inside the card
  const floatingBalls = [
    { id: 1, size: 7, x: '18%', y: '22%', dur: 4.8, del: 0, xOff: 14, yOff: -20 },
    { id: 2, size: 9, x: '82%', y: '16%', dur: 5.5, del: 0.7, xOff: -16, yOff: 18 },
    { id: 3, size: 5, x: '14%', y: '74%', dur: 6.2, del: 1.2, xOff: 18, yOff: -16 },
    { id: 4, size: 8, x: '86%', y: '70%', dur: 5.0, del: 0.4, xOff: -14, yOff: -22 },
    { id: 5, size: 6, x: '32%', y: '14%', dur: 5.8, del: 1.5, xOff: -12, yOff: 22 },
    { id: 6, size: 10, x: '72%', y: '84%', dur: 6.5, del: 2.0, xOff: 16, yOff: -18 },
    { id: 7, size: 5, x: '24%', y: '86%', dur: 4.4, del: 0.6, xOff: 14, yOff: -14 },
    { id: 8, size: 7, x: '80%', y: '36%', dur: 5.9, del: 1.8, xOff: -15, yOff: 16 }
  ];

  return (
    <div className="relative w-full h-[370px] sm:h-[410px] lg:h-[440px] rounded-[32px] bg-gradient-to-br from-[#0a3528] via-[#07281e] to-[#041a13] p-6 sm:p-8 flex items-center justify-center overflow-hidden shadow-2xl border border-emerald-900/60">
      
      {/* 1. BOTANICAL PLANT DESIGN - Handcrafted Leaf Branches & Vines */}
      <svg 
        className="absolute inset-0 w-full h-full pointer-events-none z-0"
        viewBox="0 0 500 500" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
        preserveAspectRatio="xMidYMid meet"
        aria-hidden="true"
      >
        {/* Top-Right Botanical Foliage Branch */}
        <g opacity="0.45">
          <path d="M 490,20 C 440,50 390,90 370,150" stroke="#6ee7b7" strokeWidth="1.8" strokeLinecap="round" />
          {/* Leaves along branch */}
          <path d="M 450,45 C 475,30 485,55 465,65 C 450,60 445,50 450,45 Z" fill="rgba(52, 211, 153, 0.2)" stroke="#a7f3d0" strokeWidth="1.4" />
          <path d="M 420,70 C 400,50 425,35 440,55 C 435,70 425,72 420,70 Z" fill="rgba(52, 211, 153, 0.2)" stroke="#a7f3d0" strokeWidth="1.4" />
          <path d="M 395,100 C 420,90 425,120 405,125 C 395,115 390,105 395,100 Z" fill="rgba(52, 211, 153, 0.2)" stroke="#a7f3d0" strokeWidth="1.4" />
          <path d="M 375,135 C 355,115 375,95 395,115 C 390,130 380,135 375,135 Z" fill="rgba(52, 211, 153, 0.2)" stroke="#a7f3d0" strokeWidth="1.4" />
        </g>

        {/* Bottom-Left Botanical Foliage Branch */}
        <g opacity="0.45">
          <path d="M 15,480 C 65,450 115,410 135,350" stroke="#6ee7b7" strokeWidth="1.8" strokeLinecap="round" />
          {/* Leaves along branch */}
          <path d="M 50,455 C 25,470 15,445 35,435 C 50,440 55,450 50,455 Z" fill="rgba(52, 211, 153, 0.2)" stroke="#a7f3d0" strokeWidth="1.4" />
          <path d="M 80,430 C 100,450 75,465 60,445 C 65,430 75,428 80,430 Z" fill="rgba(52, 211, 153, 0.2)" stroke="#a7f3d0" strokeWidth="1.4" />
          <path d="M 105,400 C 80,410 75,380 95,375 C 105,385 110,395 105,400 Z" fill="rgba(52, 211, 153, 0.2)" stroke="#a7f3d0" strokeWidth="1.4" />
          <path d="M 125,365 C 145,385 125,405 105,385 C 110,370 120,365 125,365 Z" fill="rgba(52, 211, 153, 0.2)" stroke="#a7f3d0" strokeWidth="1.4" />
        </g>

        {/* Central Vertical Leaf Spine */}
        <line 
          x1="250" y1="35" x2="250" y2="465" 
          stroke="rgba(167, 243, 208, 0.45)" 
          strokeWidth="1.6" 
          strokeDasharray="4 3"
        />

        {/* Top Leaf Arch (prominently visible above glass card) */}
        <path 
          d="M 250,35 C 340,95 365,190 250,250 C 135,190 160,95 250,35 Z" 
          stroke="rgba(167, 243, 208, 0.55)" 
          strokeWidth="2" 
          fill="none" 
        />

        {/* Bottom Leaf Arch (prominently visible below glass card) */}
        <path 
          d="M 250,465 C 340,405 365,310 250,250 C 135,310 160,405 250,465 Z" 
          stroke="rgba(167, 243, 208, 0.55)" 
          strokeWidth="2" 
          fill="none" 
        />

        {/* Delicate Diagonal Leaf Veins */}
        <path d="M 250,90 C 295,120 330,150 350,185" stroke="rgba(110, 231, 183, 0.40)" strokeWidth="1.4" fill="none" />
        <path d="M 250,90 C 205,120 170,150 150,185" stroke="rgba(110, 231, 183, 0.40)" strokeWidth="1.4" fill="none" />
        <path d="M 250,165 C 310,195 350,225 375,250" stroke="rgba(110, 231, 183, 0.35)" strokeWidth="1.4" fill="none" />
        <path d="M 250,165 C 190,195 150,225 125,250" stroke="rgba(110, 231, 183, 0.35)" strokeWidth="1.4" fill="none" />

        <path d="M 250,410 C 295,380 330,350 350,315" stroke="rgba(110, 231, 183, 0.40)" strokeWidth="1.4" fill="none" />
        <path d="M 250,410 C 205,380 170,350 150,315" stroke="rgba(110, 231, 183, 0.40)" strokeWidth="1.4" fill="none" />

        {/* Ambient Leaf Node Accents */}
        <circle cx="250" cy="35" r="3.5" fill="#a7f3d0" />
        <circle cx="250" cy="465" r="3.5" fill="#a7f3d0" />
      </svg>

      {/* 2. FLOATING ANIMATED PARTICLES / GLOWING BALLS */}
      {floatingBalls.map((b) => (
        <motion.div
          key={b.id}
          className="absolute rounded-full pointer-events-none z-5"
          style={{
            left: b.x,
            top: b.y,
            width: b.size,
            height: b.size,
            background: 'radial-gradient(circle, #a7f3d0 20%, #34d399 70%, transparent 100%)',
            boxShadow: '0 0 14px rgba(110, 231, 183, 0.85), 0 0 4px #ffffff'
          }}
          animate={{
            x: [0, b.xOff, -b.xOff * 0.7, 0],
            y: [0, b.yOff, -b.yOff * 0.5, 0],
            scale: [1, 1.25, 0.85, 1],
            opacity: [0.35, 0.95, 0.5, 0.35]
          }}
          transition={{
            duration: b.dur,
            delay: b.del,
            repeat: Infinity,
            ease: "easeInOut"
          }}
        />
      ))}

      {/* 3. THE FROSTED GLASS TAB */}
      <motion.div 
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="relative z-10 w-full max-w-[310px] sm:max-w-[340px] rounded-3xl p-6 sm:p-7 flex flex-col items-center text-center shadow-2xl"
        style={{
          background: 'rgba(255, 255, 255, 0.08)',
          backdropFilter: 'blur(28px)',
          WebkitBackdropFilter: 'blur(28px)',
          border: '1px solid rgba(255, 255, 255, 0.20)',
          borderTop: '1.5px solid rgba(255, 255, 255, 0.45)',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5), inset 0 1px 1.5px rgba(255, 255, 255, 0.35)'
        }}
      >
        {/* Heart Icon in Circular Badge */}
        <div className="w-12 h-12 rounded-full bg-white/10 border border-white/25 flex items-center justify-center mb-3.5 text-white shadow-inner">
          <Heart className="w-6 h-6 text-white" strokeWidth={2.2} />
        </div>

        {/* Title in Editorial Serif */}
        <h3 className="text-xl sm:text-2xl font-serif font-bold text-white tracking-tight mb-2">
          Secure &amp; Private
        </h3>

        {/* Subtitle */}
        <p className="text-xs sm:text-sm text-emerald-100/90 leading-relaxed font-normal">
          All information is encrypted and securely transmitted directly to your physician.
        </p>
      </motion.div>

    </div>
  );
}

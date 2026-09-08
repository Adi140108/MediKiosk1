import React, { useEffect, useRef } from 'react';

export default function InteractiveHueBackground() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animId;

    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };
    window.addEventListener('resize', handleResize);

    // Dynamic mouse / touch tracker with smooth spring lerp
    const mouse = {
      x: width * 0.5,
      y: height * 0.35,
      targetX: width * 0.5,
      targetY: height * 0.35,
      active: false,
      speed: 0
    };

    let prevX = width * 0.5;
    let prevY = height * 0.35;

    const onPointerMove = (e) => {
      mouse.targetX = e.clientX;
      mouse.targetY = e.clientY;
      mouse.active = true;
    };

    const onTouchMove = (e) => {
      if (e.touches && e.touches[0]) {
        mouse.targetX = e.touches[0].clientX;
        mouse.targetY = e.touches[0].clientY;
        mouse.active = true;
      }
    };

    window.addEventListener('pointermove', onPointerMove, { passive: true });
    window.addEventListener('touchmove', onTouchMove, { passive: true });

    let t = 0;

    // Harmonic Aurora Ribbons (Pure continuous trigonometric waves - gentle slow drift)
    const waves = [
      {
        yRatio: 0.18,
        amplitude: 70,
        speed: 0.0018, // slowed down significantly for peaceful drift
        freq: 0.0015,
        colorStart: 'rgba(52, 211, 153, 0.45)', // luminous mint
        colorMid: 'rgba(16, 185, 129, 0.20)',
        colorEnd: 'rgba(16, 185, 129, 0.0)',
        height: 460
      },
      {
        yRatio: 0.42,
        amplitude: 88,
        speed: 0.0013, // slowed down
        freq: 0.0012,
        colorStart: 'rgba(6, 182, 212, 0.38)', // vivid turquoise / cyan
        colorMid: 'rgba(13, 148, 136, 0.18)',
        colorEnd: 'rgba(13, 148, 136, 0.0)',
        height: 520
      },
      {
        yRatio: 0.70,
        amplitude: 78,
        speed: 0.0015, // slowed down
        freq: 0.0014,
        colorStart: 'rgba(16, 185, 129, 0.42)', // fresh emerald
        colorMid: 'rgba(5, 150, 105, 0.20)',
        colorEnd: 'rgba(5, 150, 105, 0.0)',
        height: 480
      },
      {
        yRatio: 0.88,
        amplitude: 60,
        speed: 0.0010, // slowed down
        freq: 0.0018,
        colorStart: 'rgba(110, 231, 183, 0.35)', // soft seafoam
        colorMid: 'rgba(52, 211, 153, 0.15)',
        colorEnd: 'rgba(16, 185, 129, 0.0)',
        height: 400
      }
    ];

    const render = () => {
      t += 1;

      // Smooth cursor lerp interpolation
      mouse.x += (mouse.targetX - mouse.x) * 0.08;
      mouse.y += (mouse.targetY - mouse.y) * 0.08;

      const dx = mouse.x - prevX;
      const dy = mouse.y - prevY;
      mouse.speed = Math.sqrt(dx * dx + dy * dy);
      prevX = mouse.x;
      prevY = mouse.y;

      // 1. Clinical Base Gradient
      const bgGrad = ctx.createLinearGradient(0, 0, width, height);
      bgGrad.addColorStop(0, '#eaf8f1');
      bgGrad.addColorStop(0.5, '#f4fbf7');
      bgGrad.addColorStop(1, '#e6f6ed');
      ctx.fillStyle = bgGrad;
      ctx.fillRect(0, 0, width, height);

      // 2. Render undulating Aurora Curtains
      waves.forEach((w, waveIdx) => {
        const baseY = height * w.yRatio;
        const timeOffset = t * w.speed + waveIdx * 2.2;

        ctx.beginPath();
        ctx.moveTo(0, height);
        ctx.lineTo(0, baseY);

        const step = 8; // Dense sampling for perfectly smooth curved contours
        for (let x = 0; x <= width + step; x += step) {
          // Double harmonic sinusoid: mathematically smooth everywhere
          const harmonic1 = Math.sin(x * w.freq + timeOffset) * w.amplitude;
          const harmonic2 = Math.cos(x * (w.freq * 0.6) - timeOffset * 0.75) * (w.amplitude * 0.45);
          
          // Gaussian Interactive Cursor Pull (Bends and ripples aurora gently toward cursor)
          const distToMouse = Math.abs(x - mouse.x);
          const gaussianInfluence = Math.exp(-(distToMouse * distToMouse) / (2 * 190 * 190));
          const yDistToMouse = (mouse.y - baseY);
          const mouseDeflection = gaussianInfluence * (yDistToMouse * 0.38 + Math.sin(t * 0.02) * 12);

          const y = baseY + harmonic1 + harmonic2 + mouseDeflection;
          ctx.lineTo(x, y);
        }

        ctx.lineTo(width, height);
        ctx.closePath();

        // Aurora vertical feathering gradient
        const auroraGrad = ctx.createLinearGradient(0, baseY - w.amplitude, 0, baseY + w.height);
        auroraGrad.addColorStop(0, w.colorStart);
        auroraGrad.addColorStop(0.45, w.colorMid);
        auroraGrad.addColorStop(1, w.colorEnd);

        ctx.fillStyle = auroraGrad;
        ctx.fill();
      });

      // 3. Interactive Floating Aurora Orb directly following cursor
      if (mouse.active) {
        const orbRadius = 340 + Math.min(mouse.speed * 3.5, 90);
        const cursorGrad = ctx.createRadialGradient(
          mouse.x, mouse.y, 0,
          mouse.x, mouse.y, orbRadius
        );
        cursorGrad.addColorStop(0, 'rgba(52, 211, 153, 0.50)');
        cursorGrad.addColorStop(0.35, 'rgba(6, 182, 212, 0.28)');
        cursorGrad.addColorStop(0.68, 'rgba(16, 185, 129, 0.12)');
        cursorGrad.addColorStop(1, 'rgba(16, 185, 129, 0.0)');

        ctx.fillStyle = cursorGrad;
        ctx.beginPath();
        ctx.arc(mouse.x, mouse.y, orbRadius, 0, Math.PI * 2);
        ctx.fill();
      }

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('pointermove', onPointerMove);
      window.removeEventListener('touchmove', onTouchMove);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="fixed inset-0 pointer-events-none z-0 select-none"
      style={{ width: '100%', height: '100%' }}
      aria-hidden="true"
    />
  );
}

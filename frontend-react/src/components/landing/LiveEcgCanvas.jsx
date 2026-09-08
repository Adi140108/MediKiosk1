import React, { useEffect, useRef } from 'react';

export default function LiveEcgCanvas() {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    let animationFrameId;

    let width = (canvas.width = canvas.offsetWidth || 600);
    let height = (canvas.height = canvas.offsetHeight || 260);

    const handleResize = () => {
      if (!canvas) return;
      width = canvas.width = canvas.offsetWidth || 600;
      height = canvas.height = canvas.offsetHeight || 260;
    };
    window.addEventListener('resize', handleResize);

    const cycleLength = 220; // Length of one complete cardiac cycle in pixels
    const speed = 2.4; // Pixels per frame
    let cursorX = 0;

    // Buffer storing y-coordinate and alpha timestamp for each pixel column
    const history = new Array(Math.ceil(width) + 10).fill(null);

    const getEcgY = (x, midY) => {
      const pos = x % cycleLength;
      const u = pos / cycleLength; // normalized 0 to 1

      // P wave (atrial depolarization)
      if (u >= 0.12 && u < 0.22) {
        return midY - 14 * Math.sin(((u - 0.12) / 0.10) * Math.PI);
      }
      // PR segment (baseline)
      if (u >= 0.22 && u < 0.32) {
        return midY;
      }
      // Q wave (small downward dip)
      if (u >= 0.32 && u < 0.36) {
        return midY + 14 * Math.sin(((u - 0.32) / 0.04) * Math.PI);
      }
      // R wave (SHARP TALL CARDIAC SPIKE)
      if (u >= 0.36 && u < 0.42) {
        const peakU = (u - 0.36) / 0.06;
        if (peakU <= 0.5) {
          // Shooting up to -75px
          return midY - (peakU / 0.5) * 78;
        } else {
          // Plunging down to S wave +35px
          return (midY - 78) + ((peakU - 0.5) / 0.5) * 116;
        }
      }
      // S wave return
      if (u >= 0.42 && u < 0.46) {
        return (midY + 38) - ((u - 0.42) / 0.04) * 38;
      }
      // ST segment (baseline)
      if (u >= 0.46 && u < 0.54) {
        return midY;
      }
      // T wave (ventricular repolarization, rounded dome)
      if (u >= 0.54 && u < 0.68) {
        return midY - 22 * Math.sin(((u - 0.54) / 0.14) * Math.PI);
      }

      // Isoelectric baseline
      return midY;
    };

    const render = () => {
      ctx.clearRect(0, 0, width, height);
      const midY = height / 2;

      // Advance sweeping cursor
      const prevX = cursorX;
      cursorX += speed;
      if (cursorX >= width) {
        cursorX = 0;
      }

      // Update history buffer for new swept column
      const currentY = getEcgY(cursorX, midY);
      const idx = Math.floor(cursorX);
      if (idx < history.length) {
        history[idx] = { y: currentY, birth: Date.now() };
      }

      // Clear a 35px leading gap ahead of the cursor (authentic hospital telemetry sweep)
      const eraseAhead = 35;
      for (let i = 0; i < eraseAhead; i++) {
        const eraseIdx = Math.floor((cursorX + i) % width);
        if (eraseIdx < history.length) {
          history[eraseIdx] = null;
        }
      }

      // Draw historical ECG waveform with phosphor glow
      ctx.lineWidth = 2.8;
      ctx.lineCap = 'round';
      ctx.lineJoin = 'round';

      ctx.beginPath();
      let isDrawing = false;

      for (let x = 0; x < width; x++) {
        const pt = history[x];
        if (pt) {
          if (!isDrawing) {
            ctx.moveTo(x, pt.y);
            isDrawing = true;
          } else {
            ctx.lineTo(x, pt.y);
          }
        } else {
          if (isDrawing) {
            ctx.stroke();
            ctx.beginPath();
            isDrawing = false;
          }
        }
      }
      if (isDrawing) {
        ctx.strokeStyle = '#34d399';
        ctx.shadowColor = '#6ee7b7';
        ctx.shadowBlur = 12;
        ctx.stroke();
      }

      // Draw bright, live glowing pulse cursor head
      ctx.save();
      ctx.shadowColor = '#a7f3d0';
      ctx.shadowBlur = 18;

      // Outer glow
      ctx.beginPath();
      ctx.arc(cursorX, currentY, 5, 0, Math.PI * 2);
      ctx.fillStyle = '#6ee7b7';
      ctx.fill();

      // Bright white-hot center core
      ctx.beginPath();
      ctx.arc(cursorX, currentY, 2.5, 0, Math.PI * 2);
      ctx.fillStyle = '#ffffff';
      ctx.fill();

      // Subtle vertical scanline beam
      ctx.beginPath();
      ctx.moveTo(cursorX, currentY - 20);
      ctx.lineTo(cursorX, currentY + 20);
      ctx.strokeStyle = 'rgba(167, 243, 208, 0.4)';
      ctx.lineWidth = 1.5;
      ctx.stroke();

      ctx.restore();

      animationFrameId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener('resize', handleResize);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <canvas 
      ref={canvasRef} 
      className="absolute inset-0 w-full h-full pointer-events-none z-0"
    />
  );
}

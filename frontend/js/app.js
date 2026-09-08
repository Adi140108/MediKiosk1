/**
 * MediKiosk Patient Intake App Entrypoint
 */

// Typewriter animation effect for Step 1 Hero Headline
function initTypewriterHeadline() {
  const el = document.getElementById("typewriter-headline");
  if (!el) return;
  const targetText = "Ready for a smarter check in?";
  el.textContent = "";
  let idx = 0;

  function typeNextChar() {
    if (idx < targetText.length) {
      el.textContent += targetText.charAt(idx);
      idx++;
      setTimeout(typeNextChar, 28 + Math.random() * 12);
    }
  }

  setTimeout(typeNextChar, 350);
}

// Global modal triggers for How It Works
window.openHelpModal = function() {
  const modal = document.getElementById("help-modal");
  if (modal) {
    modal.style.display = "flex";
  }
};

window.closeHelpModal = function() {
  const modal = document.getElementById("help-modal");
  if (modal) {
    modal.style.display = "none";
  }
};

// Smooth Scroll Reveal Observer ("like antigravity webpage")
function initScrollReveal() {
  const elements = document.querySelectorAll('.scroll-reveal');
  if (!elements.length) return;

  if ('IntersectionObserver' in window) {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('is-revealed');
        }
      });
    }, {
      threshold: 0.1,
      rootMargin: '0px 0px -40px 0px'
    });

    elements.forEach(el => observer.observe(el));
  } else {
    // Fallback if IntersectionObserver not available
    elements.forEach(el => el.classList.add('is-revealed'));
  }
}

document.addEventListener("DOMContentLoaded", () => {
  if (typeof PatientIntake !== "undefined") {
    PatientIntake.init();
  }
  initTypewriterHeadline();
  initScrollReveal();
});


"""
Update frontend/css/styles.css with minimalist landing page styling.
"""

def update_styles():
    path = 'frontend/css/styles.css'
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find the start of the Hero Section
    start_str = "/* ── Hero Section (Step 1) ───────────────────────────────────── */"
    end_str = "/* ── Primary Action Button (Clean Healthcare Action) ────────── */"

    if start_str not in content or end_str not in content:
        print("Error: Boundary markers not found!")
        return

    start_idx = content.find(start_str)
    end_idx = content.find(end_str)

    new_hero_css = """/* ── Hero Section (Step 1 — Minimalist Medical Kiosk) ────────── */
.hero-container {
  display: flex;
  flex-direction: column;
  gap: 1.75rem;
  padding: 0.5rem 0 2rem 0;
  position: relative;
}

.hero-main-card {
  background: #FFFFFF;
  border: 1px solid rgba(226, 232, 240, 0.9);
  border-radius: var(--radius-lg);
  padding: 3rem 2.75rem;
  box-shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.04), 0 1px 3px rgba(15, 23, 42, 0.02);
  position: relative;
}

.hero-header-badge-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 0.75rem;
  margin-bottom: 1.75rem;
}

.hero-telemetry-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 0.35rem 1rem;
  background: #F0FDFA;
  color: #0F766E;
  border-radius: var(--radius-pill);
  font-family: 'Outfit', sans-serif;
  font-size: 0.8rem;
  font-weight: 700;
  border: 1px solid #CCFBF1;
  letter-spacing: 0.02em;
}

.hero-hospital-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0.35rem 0.95rem;
  background: #F8FAFC;
  color: #475569;
  border-radius: var(--radius-pill);
  font-size: 0.78rem;
  font-weight: 600;
  border: 1px solid #E2E8F0;
}

.hero-headline-group {
  max-width: 720px;
  margin-bottom: 2.25rem;
}

.hero-brand-title {
  font-family: 'Outfit', sans-serif;
  font-size: 3.1rem;
  font-weight: 800;
  color: #0F172A;
  letter-spacing: -0.03em;
  line-height: 1.15;
  margin-bottom: 0.85rem;
}

.hero-brand-gradient {
  color: #0D9488;
  display: inline-block;
}

.hero-subtitle {
  font-size: 1.08rem;
  color: #475569;
  line-height: 1.65;
  font-weight: 400;
  max-width: 640px;
}

/* Step Kicker Badge (for Step 2 and other steps) */
.step-kicker-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0.3rem 0.85rem;
  background: rgba(13, 148, 136, 0.08);
  color: var(--brand-primary);
  border: 1px solid rgba(13, 148, 136, 0.2);
  border-radius: var(--radius-pill);
  font-family: 'Outfit', sans-serif;
  font-size: 0.75rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  margin-bottom: 0.6rem;
}

/* Call to Action Group */
.hero-cta-group {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.btn-hero-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  min-height: 52px;
  padding: 0 2rem;
  background: #0D9488;
  color: #FFFFFF;
  border: 1px solid #0D9488;
  border-radius: var(--radius-pill);
  font-family: 'Outfit', sans-serif;
  font-size: 1.05rem;
  font-weight: 700;
  letter-spacing: -0.01em;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  box-shadow: 0 4px 14px rgba(13, 148, 136, 0.25);
}

.btn-hero-primary:hover {
  background: #0F766E;
  border-color: #0F766E;
  transform: translateY(-1px);
  box-shadow: 0 8px 20px rgba(13, 148, 136, 0.35);
}

.btn-hero-primary:active {
  transform: translateY(0);
}

.btn-hero-audio {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 52px;
  padding: 0 1.35rem;
  background: #FFFFFF;
  border: 1px solid #CBD5E1;
  color: #334155;
  border-radius: var(--radius-pill);
  font-family: 'Outfit', sans-serif;
  font-size: 0.94rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-hero-audio:hover {
  border-color: #0D9488;
  color: #0D9488;
  background: #F0FDFA;
  transform: translateY(-1px);
}

.btn-hero-audio.is-playing {
  background: #ECFDF5 !important;
  border-color: #10B981 !important;
  color: #047857 !important;
}

.btn-hero-audio.is-muted {
  background: #FEF2F2 !important;
  border-color: #F87171 !important;
  color: #DC2626 !important;
}

/* ── Global Audio Mute Navbar Pill ──────────────────────────── */
.audio-mute-nav-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 0.32rem 0.85rem;
  background: #F0FDFA;
  border: 1.5px solid #99F6E4;
  color: #0F766E;
  border-radius: var(--radius-pill);
  font-family: 'Outfit', sans-serif;
  font-size: 0.78rem;
  font-weight: 700;
  letter-spacing: 0.03em;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  user-select: none;
}

.audio-mute-nav-pill:hover {
  background: #CCFBF1;
  border-color: #0D9488;
}

.audio-mute-nav-pill.is-playing {
  background: #ECFDF5;
  border-color: #10B981;
  color: #047857;
}

.audio-mute-nav-pill.is-muted {
  background: #FEF2F2 !important;
  border-color: #F87171 !important;
  color: #DC2626 !important;
}

.audio-pill-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

/* 3 Minimalist Feature Capability Cards Grid */
.hero-features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.25rem;
}

.hero-feature-card {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: var(--radius-md);
  padding: 1.5rem 1.35rem;
  box-shadow: 0 2px 8px rgba(15, 23, 42, 0.03);
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  display: flex;
  flex-direction: column;
}

.hero-feature-card:hover {
  border-color: #CBD5E1;
  box-shadow: 0 6px 18px rgba(15, 23, 42, 0.06);
  transform: translateY(-2px);
}

.feature-icon-box {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F0FDFA;
  color: #0D9488;
  border: 1px solid #CCFBF1;
  margin-bottom: 1rem;
}

.feature-card-title {
  font-family: 'Outfit', sans-serif;
  font-size: 1.05rem;
  font-weight: 700;
  color: #0F172A;
  margin-bottom: 0.35rem;
  letter-spacing: -0.01em;
}

.feature-card-desc {
  font-size: 0.86rem;
  color: #64748B;
  line-height: 1.55;
  margin: 0;
}

/* Trust & Accreditation Strip */
.hero-trust-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 1rem;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: var(--radius-sm);
  padding: 0.85rem 1.5rem;
}

.trust-item {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 0.82rem;
  font-weight: 600;
  color: #475569;
}

.trust-item svg {
  color: #0D9488;
  flex-shrink: 0;
}

"""

    content = content[:start_idx] + new_hero_css + content[end_idx:]

    # Remove obsolete mobile rules for vitals/floating pluses
    content = content.replace(
        """  .hero-vitals-subtle-bar {
    padding: 0.3rem 0.85rem !important;
    gap: 0.5rem !important;
    margin-bottom: 1.25rem !important;
    max-width: 100% !important;
  }

  .vitals-subtle-text {
    font-size: 0.72rem !important;
  }

  .vitals-subtle-ecg-box {
    min-width: 70px !important;
    height: 16px !important;
  }

  .floating-med-plus {
    opacity: 0.12 !important;
  }""",
        ""
    )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {path}")

if __name__ == '__main__':
    update_styles()

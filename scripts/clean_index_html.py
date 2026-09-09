"""
Clean all emojis and update landing page to a minimalist design without unnecessary stuff.
"""
import os
import re

def update_index_html(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Remove ambient glow orbs
    content = re.sub(
        r'<!-- Ambient Atmospheric Floating Glow Orbs \(Awwwards 60FPS\) -->\s*<div class="ambient-glow-orb orb-1" aria-hidden="true"></div>\s*<div class="ambient-glow-orb orb-2" aria-hidden="true"></div>\s*<div class="ambient-glow-orb orb-3" aria-hidden="true"></div>',
        '<!-- Clean Clinical Canvas -->',
        content
    )

    # 2. Safety Top Notice Banner
    old_safety = '''  <!-- Safety Top Notice Banner -->
  <div class="safety-top-banner">
    <div class="safety-notice-content">
      <span>⚠️</span>
      <span data-i18n="safety_notice">MediKiosk does not diagnose or prescribe. Your healthcare provider reviews all
        information.</span>
    </div>
    <div class="physician-loop-pill">
      <span class="live-dot-beacon" style="background:#A7F3D0;"></span>
      <span>🛡️</span>
      <span data-i18n="physician_in_loop">Physician-in-the-Loop</span>
    </div>
  </div>'''

    new_safety = '''  <!-- Safety Top Notice Banner -->
  <div class="safety-top-banner">
    <div class="safety-notice-content">
      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>
      <span data-i18n="safety_notice">MediKiosk does not diagnose or prescribe. Your healthcare provider reviews all information.</span>
    </div>
    <div class="physician-loop-pill">
      <span class="live-dot-beacon" style="background:#A7F3D0;"></span>
      <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
      <span data-i18n="physician_in_loop">Physician-in-the-Loop</span>
    </div>
  </div>'''

    if old_safety in content:
        content = content.replace(old_safety, new_safety)
    else:
        print("Warning: old_safety exact match not found, using regex fallback")
        content = re.sub(
            r'<span>⚠️</span>',
            '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg>',
            content
        )
        content = re.sub(
            r'<span>🛡️</span>\s*<span data-i18n="physician_in_loop">',
            '<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>\n      <span data-i18n="physician_in_loop">',
            content
        )

    # 3. OPD Mode Pill & Language Indicator in Navbar
    content = re.sub(
        r'<div class="opd-mode-pill"[^>]*>.*?<span>🏥</span>\s*<span id="opd-mode-pill-text">GENERAL OPD</span>\s*<span[^>]*>⚙️</span>\s*</div>',
        '''<div class="opd-mode-pill" id="kiosk-opd-mode-pill" onclick="PatientIntake.openStaffModeModal()" style="cursor:pointer;" title="Staff: Click to change OPD Mode">
        <span class="live-dot-beacon"></span>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 21h18"></path><path d="M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16"></path><line x1="12" y1="7" x2="12" y2="13"></line><line x1="9" y1="10" x2="15" y2="10"></line></svg>
        <span id="opd-mode-pill-text">GENERAL OPD</span>
        <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" style="opacity:0.8; margin-left:2px;" aria-hidden="true"><polyline points="6 9 12 15 18 9"></polyline></svg>
      </div>''',
        content,
        flags=re.DOTALL
    )

    content = re.sub(
        r'<div class="lang-pill-indicator"[^>]*>\s*<span>🌐</span>\s*<span id="current-lang-pill">EN</span>\s*</div>',
        '''<div class="lang-pill-indicator" onclick="PatientIntake.goToStep(2)" title="Tap to Select / Change Language">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
        <span id="current-lang-pill">EN</span>
      </div>''',
        content
    )

    # 4. Mobile step header icon
    content = re.sub(
        r'<span id="mobile-step-icon">📍</span>',
        '<span id="mobile-step-icon" style="display:inline-flex; align-items:center;"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="10" r="3"></circle><path d="M12 2a8 8 0 0 0-8 8c0 5.25 8 12 8 12s8-6.75 8-12a8 8 0 0 0-8-8z"></path></svg></span>',
        content
    )

    # 5. Replace Hero Section Step 1 with Minimalist Design
    hero_pattern = re.compile(
        r'<!-- ─── Step 1: Welcome & Landing .*?<!-- ─── Step 2: Language Selection',
        re.DOTALL
    )

    new_hero = '''<!-- ─── Step 1: Welcome & Landing (Minimalist Medical Kiosk) ─── -->
      <div id="kiosk-step-1" class="hero-container">
        <div class="hero-main-card">
          <!-- Top Telemetry & Hospital Pill Row -->
          <div class="hero-header-badge-row">
            <div class="hero-telemetry-badge">
              <span class="live-dot-beacon"></span>
              <span data-i18n="speech_ready">Intelligent Clinical Intake &amp; Triage</span>
            </div>
            <div class="hero-hospital-pill">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 21h18"></path><path d="M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16"></path><line x1="12" y1="7" x2="12" y2="13"></line><line x1="9" y1="10" x2="15" y2="10"></line></svg>
              <span>OPD Self Check-In • ABHA Integrated</span>
            </div>
          </div>

          <!-- Main Title & Subtitle -->
          <div class="hero-headline-group">
            <h1 class="hero-brand-title">
              Hospital Check-In &amp;<br>
              <span class="hero-brand-gradient">Clinical Intake</span>
            </h1>
            <p class="hero-subtitle" data-i18n="hero_sub">
              Complete your pre-consultation details in minutes. Speak symptoms in your preferred language, scan previous medical reports, and receive your priority consultation token.
            </p>
          </div>

          <!-- Hero Action Buttons -->
          <div class="hero-cta-group">
            <button id="btn-begin-checkin" class="btn-hero-primary" onclick="goToStep(2)">
              <span data-i18n="begin_checkin">Start Patient Check-In</span>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><line x1="5" y1="12" x2="19" y2="12"></line><polyline points="12 5 19 12 12 19"></polyline></svg>
            </button>
            <button class="btn-hero-audio" onclick="SpeechManager.toggleSpeakForStep(1)" title="Voice Assistance Guidance">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>
              <span>Audio Guidance (ध्वनि सहायता)</span>
            </button>
          </div>
        </div>

        <!-- 3 Minimalist Capability Pillars -->
        <div class="hero-features-grid">
          <div class="hero-feature-card">
            <div class="feature-icon-box">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" x2="12" y1="19" y2="22"></line></svg>
            </div>
            <h3 class="feature-card-title">Multilingual Voice</h3>
            <p class="feature-card-desc">Speak naturally in 10 Indian languages. Automatic speech recognition and voice guidance for effortless check-in.</p>
          </div>
          <div class="hero-feature-card">
            <div class="feature-icon-box">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"></path><path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4"></path><circle cx="20" cy="10" r="2"></circle></svg>
            </div>
            <h3 class="feature-card-title">Clinical Triage</h3>
            <p class="feature-card-desc">Adaptive questionnaire with red-flag detection and dual Allopathy &amp; AYUSH intake paths.</p>
          </div>
          <div class="hero-feature-card">
            <div class="feature-icon-box">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"></path><path d="M13 5v2"></path><path d="M13 17v2"></path><path d="M13 11v2"></path></svg>
            </div>
            <h3 class="feature-card-title">Verified Token</h3>
            <p class="feature-card-desc">Structured summary and digitized records sent directly to your physician's dashboard before you walk in.</p>
          </div>
        </div>

        <!-- Hospital Trust & Compliance Bar -->
        <div class="hero-trust-bar">
          <div class="trust-item">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
            <span>ABDM &amp; Ayushman Bharat Aligned</span>
          </div>
          <div class="trust-item">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>
            <span>Physician-in-the-Loop Architecture</span>
          </div>
          <div class="trust-item">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>
            <span>Average Check-In: Under 3 Minutes</span>
          </div>
          <div class="trust-item">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 21h18"></path><path d="M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16"></path><line x1="12" y1="7" x2="12" y2="13"></line><line x1="9" y1="10" x2="15" y2="10"></line></svg>
            <span>Encrypted &amp; Confidential Transit</span>
          </div>
        </div>
      </div>

      <!-- ─── Step 2: Language Selection'''

    content = hero_pattern.sub(new_hero, content)

    # 6. Step 2 Kicker & Selected badge
    content = content.replace(
        '<div class="step-kicker-badge">\n              <span>🌐</span>\n              <span>Step 2 of 8 • Language Preference / भाषा का चयन</span>\n            </div>',
        '''<div class="step-kicker-badge">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>
              <span>Step 2 of 8 • Language Preference / भाषा का चयन</span>
            </div>'''
    )

    content = content.replace(
        '<span class="lang-tile-badge lang-badge-selected">✓ SELECTED</span>',
        '<span class="lang-tile-badge lang-badge-selected"><svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle; margin-right:3px;" aria-hidden="true"><polyline points="20 6 9 17 4 12"></polyline></svg>SELECTED</span>'
    )

    # 7. Step 3 Consent terms icons
    content = content.replace(
        '<span style="font-size:1.15rem; line-height:1.2; flex-shrink:0;">🛡️</span>',
        '<span style="flex-shrink:0; color:var(--brand-primary); display:inline-flex; align-items:center; margin-top:2px;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg></span>'
    )
    content = content.replace(
        '<span style="font-size:1.15rem; line-height:1.2; flex-shrink:0;">🔒</span>',
        '<span style="flex-shrink:0; color:var(--brand-primary); display:inline-flex; align-items:center; margin-top:2px;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg></span>'
    )
    content = content.replace(
        '<span style="font-size:1.15rem; line-height:1.2; flex-shrink:0;">🎙️</span>',
        '<span style="flex-shrink:0; color:var(--brand-primary); display:inline-flex; align-items:center; margin-top:2px;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg></span>'
    )
    content = content.replace(
        '<span style="font-size:1.15rem; line-height:1.2; flex-shrink:0;">🚨</span>',
        '<span style="flex-shrink:0; color:#DC2626; display:inline-flex; align-items:center; margin-top:2px;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg></span>'
    )
    content = content.replace(
        '<span style="font-size:1.15rem; line-height:1.2; flex-shrink:0;">🏥</span>',
        '<span style="flex-shrink:0; color:var(--brand-primary); display:inline-flex; align-items:center; margin-top:2px;"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 21h18"></path><path d="M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16"></path><line x1="12" y1="7" x2="12" y2="13"></line><line x1="9" y1="10" x2="15" y2="10"></line></svg></span>'
    )

    # 8. Step 5 Speak buttons and Symptom tags
    mic_svg = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" y1="19" x2="12" y2="23"></line><line x1="8" y1="23" x2="16" y2="23"></line></svg>'
    content = content.replace('<span>🎙️</span>', mic_svg)

    # Remove symptom tags emojis
    content = content.replace('🫀 Chest Discomfort', 'Chest Discomfort')
    content = content.replace('🧠 Severe\n                Headache', 'Severe Headache')
    content = content.replace('🧠 Severe Headache', 'Severe Headache')
    content = content.replace('🌡️ Fever & Chills', 'Fever & Chills')
    content = content.replace('🫁 Shortness of\n                Breath', 'Shortness of Breath')
    content = content.replace('🫁 Shortness of Breath', 'Shortness of Breath')
    content = content.replace('🦴 Joint Pain', 'Joint Pain')
    content = content.replace('🩺 Stomach\n                Pain', 'Stomach Pain')
    content = content.replace('🩺 Stomach Pain', 'Stomach Pain')
    content = content.replace('🩹 Skin Itching/Rash', 'Skin Rash / Itching')

    # Remove condition pills emojis
    content = content.replace('🩸 Diabetes / Sugar', 'Diabetes')
    content = content.replace('💓 High BP / Hypertension', 'High BP / Hypertension')
    content = content.replace('🫀 Heart Disease', 'Heart Disease')
    content = content.replace('🫁 Asthma / Breathing', 'Asthma / Breathing')
    content = content.replace('🦋 Thyroid', 'Thyroid Disorder')
    content = content.replace('🦴 Arthritis / Joint Pain', 'Arthritis / Joint Pain')
    content = content.replace('🩺 Kidney Condition', 'Kidney Condition')
    content = content.replace('🚫 No Chronic Conditions', 'No Chronic Conditions')

    # 9. Step 6 Document Upload Options
    content = content.replace(
        '📄 Option A: Upload Paper or Snap Camera Photo',
        'Option A: Upload Document or Snap Photo'
    )
    content = content.replace(
        '<span>📁</span> <span>Browse Files</span>',
        '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg> <span>Browse Files</span>'
    )
    content = content.replace(
        '<span>📷</span> <span>Live Camera</span>',
        '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg> <span>Live Camera</span>'
    )
    content = content.replace(
        '🗣️ Option B: Forgot Your Prescription?',
        'Option B: Forgot Your Prescription?'
    )

    # 10. Step 8 Ticket Verified Seal
    content = content.replace(
        '<span class="official-verified-seal-star">★ ★ ★</span>',
        '<span class="official-verified-seal-star" style="font-size:0.6rem; letter-spacing:0.05em; font-weight:800;">OFFICIAL</span>'
    )
    content = content.replace(
        '<span style="font-size:2rem;">🏥</span>',
        '<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#2DD4BF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M3 21h18"></path><path d="M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16"></path><line x1="12" y1="7" x2="12" y2="13"></line><line x1="9" y1="10" x2="15" y2="10"></line></svg>'
    )
    content = content.replace(
        '<span class="status-check">✓</span>',
        '<span class="status-check"><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="20 6 9 17 4 12"></polyline></svg></span>'
    )

    # 11. Staff Mode Modal
    content = content.replace(
        'style="position:absolute; top:20px; right:20px; border:none; background:var(--bg-subtle); border-radius:50%; width:36px; height:36px; cursor:pointer; font-size:1.1rem; color:var(--text-muted); transition:var(--transition);">✕</button>',
        'style="position:absolute; top:20px; right:20px; border:none; background:var(--bg-subtle); border-radius:50%; width:36px; height:36px; cursor:pointer; color:var(--text-muted); display:flex; align-items:center; justify-content:center; transition:var(--transition);"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg></button>'
    )
    content = content.replace(
        '<div style="font-size:2.5rem; margin-bottom:0.5rem;">🏥</div>',
        '<div style="display:flex; justify-content:center; margin-bottom:0.75rem;"><div style="width:48px; height:48px; border-radius:12px; background:var(--brand-primary-soft); display:flex; align-items:center; justify-content:center; color:var(--brand-primary);"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21h18"></path><path d="M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16"></path><line x1="12" y1="7" x2="12" y2="13"></line><line x1="9" y1="10" x2="15" y2="10"></line></svg></div></div>'
    )
    content = content.replace(
        '<div style="font-size:1.8rem; margin-bottom:0.4rem;">🩺</div>',
        '<div style="display:flex; justify-content:center; margin-bottom:0.4rem; color:var(--brand-primary);"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M4.8 2.3A.3.3 0 1 0 5 2H4a2 2 0 0 0-2 2v5a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6V4a2 2 0 0 0-2-2h-1a.2.2 0 1 0 .3.3"></path><path d="M8 15v1a6 6 0 0 0 6 6v0a6 6 0 0 0 6-6v-4"></path><circle cx="20" cy="10" r="2"></circle></svg></div>'
    )
    content = content.replace(
        '<div style="font-size:1.8rem; margin-bottom:0.4rem;">🌿</div>',
        '<div style="display:flex; justify-content:center; margin-bottom:0.4rem; color:#15803D;"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M11 20A7 7 0 0 1 4 13C4 7 11 2 20 2c0 9-5 16-12 16h3"></path><path d="M2 21c0-4 3-7 7-7"></path></svg></div>'
    )

    # 12. Camera Modal
    content = content.replace(
        '<span style="font-size:1.3rem;">📷</span>',
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--brand-primary)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>'
    )
    content = content.replace(
        '<button type="button" onclick="PatientIntake.closeCameraModal()" style="background:#F1F5F9; border:none; border-radius:50%; width:36px; height:36px; font-size:1.2rem; cursor:pointer; color:#64748B; display:flex; align-items:center; justify-content:center;">✕</button>',
        '<button type="button" onclick="PatientIntake.closeCameraModal()" style="background:#F1F5F9; border:none; border-radius:50%; width:36px; height:36px; cursor:pointer; color:#64748B; display:flex; align-items:center; justify-content:center;"><svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg></button>'
    )
    content = content.replace(
        '✓ Photo Captured',
        '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round" style="vertical-align:middle; margin-right:4px;"><polyline points="20 6 9 17 4 12"></polyline></svg>Photo Captured'
    )
    content = content.replace(
        '<button type="button" class="camera-flip-btn" onclick="PatientIntake.switchCamera()" title="Switch Front / Rear Camera">\n          🔄\n        </button>',
        '<button type="button" class="camera-flip-btn" onclick="PatientIntake.switchCamera()" title="Switch Front / Rear Camera" style="display:flex; align-items:center; justify-content:center;"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg></button>'
    )
    content = content.replace(
        '<span>🔄</span> <span>Retake Photo</span>',
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg> <span>Retake Photo</span>'
    )
    content = content.replace(
        '<span>✓</span> <span>Use Document</span>',
        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.8" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg> <span>Use Document</span>'
    )
    content = content.replace(
        '<p style="margin:0 0 0.5rem 0;">⚠️ Camera access was not granted or is unavailable on this device.</p>',
        '<p style="margin:0 0 0.5rem 0; display:flex; align-items:center; justify-content:center; gap:6px;"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="12"></line><line x1="12" y1="16" x2="12.01" y2="16"></line></svg> Camera access was not granted or is unavailable on this device.</p>'
    )
    content = content.replace(
        '📁 Use System File / Photo Picker',
        'Use System File / Photo Picker'
    )

    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {path}")

if __name__ == '__main__':
    update_index_html('frontend/index.html')

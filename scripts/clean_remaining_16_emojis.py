import os

def clean_file(path, replacements):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Cleaned {path}")

# 1. index.html
svg_lock = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>'
svg_shield = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>'
svg_hospital = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 21h18"></path><path d="M5 21V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16"></path><line x1="12" y1="7" x2="12" y2="13"></line><line x1="9" y1="10" x2="15" y2="10"></line></svg>'
svg_globe = '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>'

svg_voice = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"></path><path d="M19 10v2a7 7 0 0 1-14 0v-2"></path><line x1="12" x2="12" y1="19" y2="22"></line></svg>'
svg_pulse = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>'
svg_camera = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"></path><circle cx="12" cy="13" r="4"></circle></svg>'
svg_doc = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>'

svg_speaker = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"></polygon><path d="M19.07 4.93a10 10 0 0 1 0 14.14M15.54 8.46a5 5 0 0 1 0 7.07"></path></svg>'
svg_close = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>'
svg_flip = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>'

replacements_index = [
    ('<span class="floating-med-plus plus-pos-2">✚</span>', '<span class="floating-med-plus plus-pos-2">+</span>'),
    ('<span class="floating-med-plus plus-pos-4">✛</span>', '<span class="floating-med-plus plus-pos-4">+</span>'),
    ('<span class="floating-med-plus plus-pos-6">✚</span>', '<span class="floating-med-plus plus-pos-6">+</span>'),
    ('<div class="feature-icon-box icon-box-teal">🗣️</div>', f'<div class="feature-icon-box icon-box-teal">{svg_voice}</div>'),
    ('<div class="feature-icon-box icon-box-blue">⚡</div>', f'<div class="feature-icon-box icon-box-blue">{svg_pulse}</div>'),
    ('<div class="feature-icon-box icon-box-amber">📷</div>', f'<div class="feature-icon-box icon-box-amber">{svg_camera}</div>'),
    ('<div class="feature-icon-box icon-box-emerald">👨‍⚕️</div>', f'<div class="feature-icon-box icon-box-emerald">{svg_doc}</div>'),
    ('<span class="trust-item-icon">🔒</span>', f'<span class="trust-item-icon">{svg_lock}</span>'),
    ('<span class="trust-item-icon">🛡️</span>', f'<span class="trust-item-icon">{svg_shield}</span>'),
    ('<span class="trust-item-icon">🏥</span>', f'<span class="trust-item-icon">{svg_hospital}</span>'),
    ('<span>🌐</span>', f'<span>{svg_globe}</span>'),
    ('>🔊</button>', f'>{svg_speaker}</button>'),
    ('\n              🔊\n            </button>', f'\n              {svg_speaker}\n            </button>'),
    ('<span style="font-size:1.3rem;">📷</span>', f'<span style="display:inline-flex; align-items:center;">{svg_camera}</span>'),
    ('>✕</button>', f'>{svg_close}</button>'),
    ('title="Switch Front / Rear Camera">\n          🔄\n        </button>', f'title="Switch Front / Rear Camera">\n          {svg_flip}\n        </button>'),
    ('title="Switch Front / Rear Camera">\n          🔄</button>', f'title="Switch Front / Rear Camera">\n          {svg_flip}</button>'),
    ('🔄', svg_flip)
]

clean_file('frontend/index.html', replacements_index)

# 2. patient_intake.js
clean_file('frontend/js/patient_intake.js', [
    ('alert("⚠️ Please tap Submit Answer once more to proceed.");', 'alert("Please tap Submit Answer once more to proceed.");')
])

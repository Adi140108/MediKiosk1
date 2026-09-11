/**
 * MediKiosk Universal On-Screen Virtual Keyboard
 * Designed for Medical Kiosks & Touchscreen Displays
 * Features:
 *  - High contrast, minimalist glassmorphism interface
 *  - Bulletproof forward cursor tracking (guaranteed LTR order, eliminates inverted character entry)
 *  - Safe across all input types including type="number"
 *  - Manual FAB toggle controlled (no auto-open on tap/focus)
 *  - QWERTY, Uppercase/Shift, Numbers, Punctuation, and Medical Symbols
 *  - Smart step-aware auto-targeting when opened via floating FAB
 *  - Strictly zero emojis (pure SVGs & typography)
 */

(function(window, document) {
  'use strict';

  const VirtualKeyboard = {
    isOpen: false,
    activeInput: null,
    cursorPos: 0,
    isShift: false,
    mode: 'alpha', // 'alpha' | 'sym' | 'num'

    // Key layouts
    layouts: {
      alpha: [
        ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
        ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
        ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
        ['shift', 'z', 'x', 'c', 'v', 'b', 'n', 'm', 'backspace'],
        ['sym', ',', 'space', '.', 'done']
      ],
      sym: [
        ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
        ['@', '#', '₹', '$', '%', '&', '*', '-', '+', '='],
        ['(', ')', '/', '\\', ':', ';', '"', "'", '!', '?'],
        ['alpha', '_', '~', '<', '>', '[', ']', '{', '}', 'backspace'],
        ['alpha', ',', 'space', '.', 'done']
      ],
      num: [
        ['1', '2', '3', '4', '5'],
        ['6', '7', '8', '9', '0'],
        ['alpha', '+', '-', 'backspace'],
        ['space', 'done']
      ]
    },

    init() {
      this.ensureDrawerDOM();
      this.ensureFabButton();
      this.bindGlobalInputListeners();
      this.bindFabButton();
      this.renderKeys();
    },

    ensureFabButton() {
      let fab = document.getElementById('keyboard-fab');
      if (!fab) {
        fab = document.createElement('button');
        fab.id = 'keyboard-fab';
        fab.className = 'keyboard-fab';
        fab.type = 'button';
        fab.title = 'Open On-Screen Keyboard';
        fab.setAttribute('aria-label', 'Open On-Screen Keyboard');
        fab.innerHTML = `
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"
            stroke-linecap="round" stroke-linejoin="round">
            <rect x="2" y="4" width="20" height="16" rx="2" ry="2"></rect>
            <line x1="6" y1="8" x2="6" y2="8"></line>
            <line x1="10" y1="8" x2="10" y2="8"></line>
            <line x1="14" y1="8" x2="14" y2="8"></line>
            <line x1="18" y1="8" x2="18" y2="8"></line>
            <line x1="6" y1="12" x2="6" y2="12"></line>
            <line x1="10" y1="12" x2="10" y2="12"></line>
            <line x1="14" y1="12" x2="14" y2="12"></line>
            <line x1="18" y1="12" x2="18" y2="12"></line>
            <line x1="7" y1="16" x2="17" y2="16"></line>
          </svg>
        `;
        const step1 = document.getElementById('kiosk-step-1');
        if (step1 && (step1.style.display !== 'none' && window.getComputedStyle(step1).display !== 'none')) {
          fab.style.display = 'none';
        }
        document.body.appendChild(fab);
      }
    },

    ensureDrawerDOM() {
      if (document.getElementById('virtual-keyboard-drawer')) return;

      const drawer = document.createElement('div');
      drawer.id = 'virtual-keyboard-drawer';
      drawer.className = 'vk-drawer';
      drawer.setAttribute('aria-label', 'On-Screen Virtual Keyboard');

      drawer.innerHTML = `
        <div class="vk-header">
          <div class="vk-target-indicator">
            <span class="vk-beacon"></span>
            <svg class="vk-target-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <polyline points="4 7 4 4 20 4 20 7"></polyline>
              <line x1="9" y1="20" x2="15" y2="20"></line>
              <line x1="12" y1="4" x2="12" y2="20"></line>
            </svg>
            <span id="vk-target-label" class="vk-target-name">Ready — Tap an input field</span>
          </div>

          <div class="vk-header-actions">
            <button type="button" class="vk-action-btn" id="vk-btn-clear" title="Clear Field Value">
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="3 6 5 6 21 6"></polyline>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
              </svg>
              <span>Clear</span>
            </button>
            <button type="button" class="vk-action-btn vk-btn-hide" id="vk-btn-close" title="Hide Keyboard">
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="6 9 12 15 18 9"></polyline>
              </svg>
              <span>Hide</span>
            </button>
          </div>
        </div>

        <div id="vk-keyboard-body" class="vk-keyboard-body"></div>
      `;

      // Prevent touches or clicks on the drawer chrome from blurring the active input
      const preventDrawerBlur = (e) => {
        if (e.target && !e.target.matches('input, textarea, select')) {
          e.preventDefault();
        }
      };
      if (window.PointerEvent) {
        drawer.addEventListener('pointerdown', preventDrawerBlur);
      } else {
        drawer.addEventListener('mousedown', preventDrawerBlur);
      }

      document.body.appendChild(drawer);

      // Bind header action buttons
      const clearBtn = document.getElementById('vk-btn-clear');
      if (clearBtn) {
        const onClear = (e) => {
          e.preventDefault();
          e.stopPropagation();
          this.clearCurrentInput();
        };
        if (window.PointerEvent) {
          clearBtn.addEventListener('pointerdown', onClear);
        } else {
          clearBtn.addEventListener('mousedown', onClear);
        }
        clearBtn.addEventListener('click', (e) => e.preventDefault());
      }

      const closeBtn = document.getElementById('vk-btn-close');
      if (closeBtn) {
        closeBtn.addEventListener('click', (e) => {
          e.preventDefault();
          this.close();
        });
      }
    },

    isEligibleInput(target) {
      if (!target) return false;
      const tagName = target.tagName ? target.tagName.toLowerCase() : '';
      const isEditable = (tagName === 'input' && !['checkbox', 'radio', 'file', 'submit', 'button', 'range', 'color', 'hidden', 'image', 'reset'].includes(target.type)) ||
                         tagName === 'textarea';
      return isEditable && !target.readOnly && !target.disabled && target.offsetParent !== null;
    },

    bindGlobalInputListeners() {
      // Track currently focused input and synchronize cursor position
      const syncInputState = (e) => {
        const target = e.target;
        if (this.isEligibleInput(target)) {
          this.setActiveInput(target);
          if (target.type !== 'number' && typeof target.selectionStart === 'number') {
            this.cursorPos = target.selectionStart;
          }
        }
      };

      document.addEventListener('focusin', syncInputState, true);
      document.addEventListener('click', syncInputState, true);
      document.addEventListener('keyup', syncInputState, true);
      document.addEventListener('select', syncInputState, true);
      document.addEventListener('touchend', syncInputState, true);
    },

    bindFabButton() {
      const fab = document.getElementById('keyboard-fab');
      if (fab) {
        fab.onclick = (e) => {
          e.preventDefault();
          this.toggle();
        };
      }
    },

    findDefaultInputForCurrentStep() {
      // Step-aware auto detection of the primary interactive input in currently visible step
      for (let s = 1; s <= 8; s++) {
        const stepEl = document.getElementById('kiosk-step-' + s);
        if (stepEl && stepEl.style.display !== 'none' && window.getComputedStyle(stepEl).display !== 'none') {
          const inputs = Array.from(
            stepEl.querySelectorAll('input:not([type="hidden"]):not([type="range"]):not([type="checkbox"]):not([type="file"]):not([disabled]), textarea:not([disabled])')
          ).filter(el => el.offsetParent !== null && window.getComputedStyle(el).display !== 'none');
          if (inputs.length > 0) return inputs[0];
        }
      }

      // Fallback: any visible editable element in patient intake section
      const sec = document.getElementById('section-patient') || document.body;
      const visibleInputs = Array.from(
        sec.querySelectorAll('input:not([type="hidden"]):not([type="range"]):not([type="checkbox"]):not([type="file"]):not([disabled]), textarea:not([disabled])')
      ).filter(el => el.offsetParent !== null && window.getComputedStyle(el).display !== 'none');

      return visibleInputs.length > 0 ? visibleInputs[0] : null;
    },

    setActiveInput(el) {
      if (!el) return;
      const isDifferent = this.activeInput !== el;
      this.activeInput = el;

      // When switching to a new element or if cursor position uninitialized, position cursor at text end
      if (isDifferent || typeof this.cursorPos !== 'number') {
        const valLen = (el.value || '').length;
        if (document.activeElement === el && el.type !== 'number' && typeof el.selectionStart === 'number') {
          this.cursorPos = el.selectionStart;
        } else {
          this.cursorPos = valLen;
        }
      }

      const isNumeric = el.type === 'number' || el.type === 'tel' || el.id === 'reg-age' || el.id === 'reg-phone';
      if (isNumeric && this.mode === 'alpha') {
        this.mode = 'num';
        this.renderKeys();
      } else if (!isNumeric && this.mode === 'num') {
        this.mode = 'alpha';
        this.renderKeys();
      }

      this.updateTargetLabel();
    },

    updateTargetLabel() {
      const labelEl = document.getElementById('vk-target-label');
      if (!labelEl) return;

      if (!this.activeInput) {
        labelEl.textContent = "Ready — Tap an input field";
        return;
      }

      let name = this.activeInput.getAttribute('aria-label') ||
                 this.activeInput.getAttribute('placeholder') ||
                 this.activeInput.getAttribute('id') ||
                 'Active Field';

      name = name.replace(/^patient-/, '').replace(/^reg-/, '').replace(/-/g, ' ');
      name = name.charAt(0).toUpperCase() + name.slice(1);

      labelEl.textContent = `Typing: ${name}`;
    },

    toggle() {
      if (this.isOpen) {
        this.close();
      } else {
        this.open();
      }
    },

    open() {
      // Prioritize currently focused editable field if available
      const activeEl = document.activeElement;
      if (this.isEligibleInput(activeEl)) {
        this.setActiveInput(activeEl);
      }

      if (!this.activeInput || this.activeInput.offsetParent === null || this.activeInput.disabled || this.activeInput.readOnly) {
        const candidate = this.findDefaultInputForCurrentStep();
        if (candidate) {
          this.setActiveInput(candidate);
        }
      }

      if (this.activeInput) {
        try {
          this.activeInput.focus({ preventScroll: true });
          if (this.activeInput.type !== 'number') {
            const pos = typeof this.cursorPos === 'number' ? this.cursorPos : (this.activeInput.value || '').length;
            this.activeInput.setSelectionRange(pos, pos);
          }
        } catch(e) {}
      }

      const drawer = document.getElementById('virtual-keyboard-drawer');
      if (drawer) {
        drawer.classList.add('vk-open');
      }

      const fab = document.getElementById('keyboard-fab');
      if (fab) {
        fab.classList.add('is-active');
        fab.title = "Close On-Screen Keyboard";
      }

      this.isOpen = true;
      this.updateTargetLabel();
    },

    close() {
      const drawer = document.getElementById('virtual-keyboard-drawer');
      if (drawer) {
        drawer.classList.remove('vk-open');
      }

      const fab = document.getElementById('keyboard-fab');
      if (fab) {
        fab.classList.remove('is-active');
        fab.title = "Open On-Screen Keyboard";
      }

      this.isOpen = false;
    },

    renderKeys() {
      const container = document.getElementById('vk-keyboard-body');
      if (!container) return;

      container.innerHTML = '';
      const rows = this.layouts[this.mode] || this.layouts.alpha;

      rows.forEach(rowKeys => {
        const rowEl = document.createElement('div');
        rowEl.className = 'vk-row';

        rowKeys.forEach(key => {
          const btn = document.createElement('button');
          btn.type = 'button';
          btn.className = 'vk-key';
          btn.setAttribute('tabindex', '-1');

          // Prevent blur on pointer down and trigger key press
          const onKeyTrigger = (e) => {
            e.preventDefault();
            e.stopPropagation();
            this.handleKeyPress(key);
          };

          if (window.PointerEvent) {
            btn.addEventListener('pointerdown', onKeyTrigger);
          } else {
            btn.addEventListener('touchstart', onKeyTrigger, { passive: false });
            btn.addEventListener('mousedown', onKeyTrigger);
          }

          btn.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
          });

          if (key === 'shift') {
            btn.classList.add('vk-key-special', 'vk-key-shift');
            if (this.isShift) btn.classList.add('vk-key-active');
            btn.innerHTML = `
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="18 15 12 9 6 15"></polyline>
              </svg>
            `;
          } else if (key === 'backspace') {
            btn.classList.add('vk-key-special', 'vk-key-backspace');
            btn.innerHTML = `
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M21 4H8l-7 8 7 8h13a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2z"></path>
                <line x1="18" y1="9" x2="12" y2="15"></line>
                <line x1="12" y1="9" x2="18" y2="15"></line>
              </svg>
            `;
          } else if (key === 'space') {
            btn.classList.add('vk-key-space');
            btn.innerHTML = `<span>Space</span>`;
          } else if (key === 'sym') {
            btn.classList.add('vk-key-special', 'vk-key-toggle');
            btn.textContent = '?123';
          } else if (key === 'alpha') {
            btn.classList.add('vk-key-special', 'vk-key-toggle');
            btn.textContent = 'ABC';
          } else if (key === 'done') {
            btn.classList.add('vk-key-special', 'vk-key-done');
            btn.innerHTML = `
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                <polyline points="20 6 9 17 4 12"></polyline>
              </svg>
              <span>Done</span>
            `;
          } else {
            // Normal character key
            let char = key;
            if (this.mode === 'alpha' && this.isShift) {
              char = key.toUpperCase();
            }
            btn.textContent = char;
          }

          rowEl.appendChild(btn);
        });

        container.appendChild(rowEl);
      });
    },

    handleKeyPress(key) {
      if (key === 'shift') {
        this.isShift = !this.isShift;
        this.renderKeys();
        return;
      }

      if (key === 'sym') {
        this.mode = 'sym';
        this.renderKeys();
        return;
      }

      if (key === 'alpha') {
        this.mode = 'alpha';
        this.renderKeys();
        return;
      }

      if (key === 'done') {
        this.close();
        if (this.activeInput) {
          try { this.activeInput.blur(); } catch(e) {}
        }
        return;
      }

      // Check if target input is available
      if (!this.activeInput || this.activeInput.offsetParent === null) {
        const candidate = this.findDefaultInputForCurrentStep();
        if (candidate) {
          this.setActiveInput(candidate);
        } else {
          return;
        }
      }

      const input = this.activeInput;

      if (key === 'backspace') {
        this.deleteBackwards(input);
      } else if (key === 'space') {
        this.insertText(input, ' ');
      } else {
        let char = key;
        if (this.mode === 'alpha' && this.isShift) {
          char = key.toUpperCase();
        }
        this.insertText(input, char);
      }

      // Revert shift after single character entry
      if (this.isShift && this.mode === 'alpha' && key.length === 1 && key.toLowerCase() !== key.toUpperCase()) {
        this.isShift = false;
        this.renderKeys();
      }
    },

    insertText(input, text) {
      if (!input) return;
      const isNumberType = input.type === 'number';
      const val = input.value || '';

      // If number field, only allow numeric characters
      if (isNumberType && !/^[0-9]$/.test(text)) {
        return;
      }

      // Check if user currently has an active text selection range inside this input
      let start = null;
      let end = null;
      if (document.activeElement === input && !isNumberType) {
        try {
          if (typeof input.selectionStart === 'number' && typeof input.selectionEnd === 'number') {
            start = input.selectionStart;
            end = input.selectionEnd;
          }
        } catch (e) {}
      }

      // If there is an active highlighted selection range (start !== end), replace it
      if (start !== null && end !== null && start !== end) {
        const before = val.substring(0, start);
        const after = val.substring(end);
        input.value = before + text + after;
        this.cursorPos = start + text.length;
      } else {
        // Forward cursor insertion: use tracked cursorPos if valid, else input.selectionStart if focused, else end of string
        let pos;
        if (typeof this.cursorPos === 'number' && !isNaN(this.cursorPos) && this.cursorPos >= 0 && this.cursorPos <= val.length) {
          pos = this.cursorPos;
        } else if (start !== null && start >= 0 && start <= val.length) {
          pos = start;
        } else {
          pos = val.length;
        }

        const before = val.substring(0, pos);
        const after = val.substring(pos);
        input.value = before + text + after;
        this.cursorPos = pos + text.length;
      }

      // Keep focus and caret sync
      if (!isNumberType) {
        try {
          input.focus({ preventScroll: true });
          input.setSelectionRange(this.cursorPos, this.cursorPos);
        } catch (e) {}
      }

      this.dispatchInputEvents(input);
    },

    deleteBackwards(input) {
      if (!input) return;
      const isNumberType = input.type === 'number';
      const val = input.value || '';
      if (!val.length) {
        this.cursorPos = 0;
        return;
      }

      // Check if there is an active selection range to delete
      if (document.activeElement === input && !isNumberType) {
        try {
          const start = input.selectionStart;
          const end = input.selectionEnd;
          if (typeof start === 'number' && typeof end === 'number' && start !== end) {
            const before = val.substring(0, start);
            const after = val.substring(end);
            input.value = before + after;
            this.cursorPos = start;
            input.focus({ preventScroll: true });
            input.setSelectionRange(this.cursorPos, this.cursorPos);
            this.dispatchInputEvents(input);
            return;
          }
        } catch (e) {}
      }

      let pos;
      if (typeof this.cursorPos === 'number' && !isNaN(this.cursorPos) && this.cursorPos >= 0 && this.cursorPos <= val.length) {
        pos = this.cursorPos;
      } else {
        pos = val.length;
      }

      if (pos > 0) {
        const before = val.substring(0, pos - 1);
        const after = val.substring(pos);
        input.value = before + after;
        this.cursorPos = pos - 1;

        if (!isNumberType) {
          try {
            input.focus({ preventScroll: true });
            input.setSelectionRange(this.cursorPos, this.cursorPos);
          } catch (e) {}
        }
      }

      this.dispatchInputEvents(input);
    },

    clearCurrentInput() {
      if (!this.activeInput) return;
      this.activeInput.value = '';
      this.cursorPos = 0;
      if (this.activeInput.type !== 'number') {
        try {
          this.activeInput.focus({ preventScroll: true });
          this.activeInput.setSelectionRange(0, 0);
        } catch (e) {}
      }
      this.dispatchInputEvents(this.activeInput);
    },

    dispatchInputEvents(input) {
      try {
        input.dispatchEvent(new Event('input', { bubbles: true }));
        input.dispatchEvent(new Event('change', { bubbles: true }));
        input.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true }));
      } catch(e) {}
    }
  };

  // Expose globally and auto-initialize on DOMContentLoaded
  window.VirtualKeyboard = VirtualKeyboard;

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => VirtualKeyboard.init());
  } else {
    VirtualKeyboard.init();
  }

})(window, document);

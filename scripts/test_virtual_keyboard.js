const assert = require('assert');
const fs = require('fs');
const path = require('path');

// Read virtual_keyboard.js
const vkPath = path.join(__dirname, '..', 'frontend', 'js', 'virtual_keyboard.js');
const vkCode = fs.readFileSync(vkPath, 'utf-8');

// Mock a lightweight DOM environment
class MockEvent {
  constructor(type, opts = {}) {
    this.type = type;
    this.bubbles = !!opts.bubbles;
  }
}

class MockElement {
  constructor(tagName = 'div', id = '') {
    this.tagName = tagName.toUpperCase();
    this.id = id;
    this.value = '';
    this.type = 'text';
    this.attributes = {};
    this.style = {};
    this.children = [];
    this.classList = {
      classes: new Set(),
      add: (c) => this.classList.classes.add(c),
      remove: (c) => this.classList.classes.delete(c),
      contains: (c) => this.classList.classes.has(c)
    };
    this.eventListeners = {};
    this.offsetParent = {}; // truthy by default (visible)
    this._selectionStart = 0;
    this._selectionEnd = 0;
  }

  getAttribute(name) {
    return this.attributes[name] || null;
  }

  setAttribute(name, val) {
    this.attributes[name] = val;
  }

  addEventListener(type, listener) {
    if (!this.eventListeners[type]) this.eventListeners[type] = [];
    this.eventListeners[type].push(listener);
  }

  dispatchEvent(evt) {
    const list = this.eventListeners[evt.type] || [];
    list.forEach(fn => fn(evt));
    return true;
  }

  focus() {}
  blur() {}

  setSelectionRange(start, end) {
    this._selectionStart = start;
    this._selectionEnd = end;
  }

  // Simulate an unfocused element where selectionStart can return 0
  get selectionStart() {
    return this._selectionStart;
  }

  set selectionStart(val) {
    this._selectionStart = val;
  }

  get selectionEnd() {
    return this._selectionEnd;
  }

  set selectionEnd(val) {
    this._selectionEnd = val;
  }

  appendChild(child) {
    this.children.push(child);
  }

  querySelector() { return null; }
  querySelectorAll() { return []; }
}

const mockDocument = {
  readyState: 'complete',
  elements: {},
  body: new MockElement('body'),
  createElement(tag) {
    return new MockElement(tag);
  },
  getElementById(id) {
    return this.elements[id] || null;
  },
  addEventListener(type, fn) {},
  activeElement: null
};

const mockWindow = {
  document: mockDocument,
  getComputedStyle: () => ({ display: 'block' }),
  PointerEvent: function() {}
};

// Evaluate the script in this environment
const vm = require('vm');
const context = {
  window: mockWindow,
  document: mockDocument,
  Event: MockEvent,
  KeyboardEvent: MockEvent,
  console: console
};

vm.createContext(context);
vm.runInContext(vkCode, context);

const VK = context.window.VirtualKeyboard;

console.log("--> Testing VirtualKeyboard...");

// 1. Test basic initialization
assert(VK, "VirtualKeyboard object should exist");

// 2. Test typing 'O' then 'K' on a text input
const testInput = new MockElement('input', 'patient-name');
testInput.type = 'text';
testInput.value = '';

VK.setActiveInput(testInput);
assert.strictEqual(VK.cursorPos, 0, "Initial cursor pos should be 0");

// Simulate typing 'o'
VK.handleKeyPress('o');
console.log(`After typing 'o': value="${testInput.value}", cursorPos=${VK.cursorPos}`);
assert.strictEqual(testInput.value, 'o', "Value should be 'o'");
assert.strictEqual(VK.cursorPos, 1, "Cursor should advance to 1");

// Simulate typing 'k'
VK.handleKeyPress('k');
console.log(`After typing 'k': value="${testInput.value}", cursorPos=${VK.cursorPos}`);
assert.strictEqual(testInput.value, 'ok', "Value should be 'ok' NOT 'ko'");
assert.strictEqual(VK.cursorPos, 2, "Cursor should advance to 2");

// 3. Test simulating unfocused element where selectionStart resets to 0
testInput._selectionStart = 0;
testInput._selectionEnd = 0;
mockDocument.activeElement = null; // Unfocused!

VK.handleKeyPress('a');
console.log(`After typing 'a' while unfocused: value="${testInput.value}", cursorPos=${VK.cursorPos}`);
assert.strictEqual(testInput.value, 'oka', "Value should be 'oka' even when input is unfocused");
assert.strictEqual(VK.cursorPos, 3, "Cursor should advance to 3");

// 4. Test backspace
VK.handleKeyPress('backspace');
console.log(`After backspace: value="${testInput.value}", cursorPos=${VK.cursorPos}`);
assert.strictEqual(testInput.value, 'ok', "Value should be back to 'ok'");
assert.strictEqual(VK.cursorPos, 2, "Cursor should decrement to 2");

// 5. Test space
VK.handleKeyPress('space');
console.log(`After space: value="${testInput.value}", cursorPos=${VK.cursorPos}`);
assert.strictEqual(testInput.value, 'ok ', "Value should be 'ok '");
assert.strictEqual(VK.cursorPos, 3, "Cursor should advance to 3");

// 6. Test uppercase / shift
VK.handleKeyPress('shift');
assert.strictEqual(VK.isShift, true, "Shift should be active");
VK.handleKeyPress('y');
console.log(`After shifted 'y': value="${testInput.value}", cursorPos=${VK.cursorPos}`);
assert.strictEqual(testInput.value, 'ok Y', "Value should be 'ok Y'");
assert.strictEqual(VK.isShift, false, "Shift should revert to false after typing a letter");

// 7. Test clearCurrentInput
VK.clearCurrentInput();
console.log(`After clear: value="${testInput.value}", cursorPos=${VK.cursorPos}`);
assert.strictEqual(testInput.value, '', "Value should be empty");
assert.strictEqual(VK.cursorPos, 0, "Cursor should reset to 0");

// 8. Test typing immediately after clear
VK.handleKeyPress('o');
VK.handleKeyPress('k');
console.log(`After re-typing 'o', 'k': value="${testInput.value}", cursorPos=${VK.cursorPos}`);
assert.strictEqual(testInput.value, 'ok', "Value must be 'ok'");

// 9. Test number input
const numInput = new MockElement('input', 'reg-age');
numInput.type = 'number';
numInput.value = '';
VK.setActiveInput(numInput);

VK.handleKeyPress('2');
VK.handleKeyPress('5');
console.log(`After typing '2', '5' on number field: value="${numInput.value}", cursorPos=${VK.cursorPos}`);
assert.strictEqual(numInput.value, '25', "Number input should be '25'");

// Reject non-numeric on number input
VK.handleKeyPress('a');
assert.strictEqual(numInput.value, '25', "Number input should reject 'a'");

console.log("\n===========================================");
console.log(">>> ALL VIRTUAL KEYBOARD UNIT TESTS PASSED! <<<");
console.log("===========================================");

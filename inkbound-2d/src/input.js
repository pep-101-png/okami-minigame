export class Input {
  constructor(canvas) {
    this.keys = new Set();
    this.pressed = new Set();
    this.released = new Set();
    this.pointer = { x: 0, y: 0, down: false };
    this.padCursor = { x: 640, y: 360 };
    this.padPrevious = [];
    this.padKeys = new Set();
    this.canvas = canvas;
    window.addEventListener("keydown", (e) => {
      if (
        [
          "Space",
          "Tab",
          "ArrowUp",
          "ArrowDown",
          "ArrowLeft",
          "ArrowRight",
        ].includes(e.code)
      )
        e.preventDefault();
      if (!this.keys.has(e.code)) this.pressed.add(e.code);
      this.keys.add(e.code);
    });
    window.addEventListener("keyup", (e) => {
      this.keys.delete(e.code);
      this.released.add(e.code);
    });
    window.addEventListener("blur", () => {
      this.keys.clear();
      this.pointer.down = false;
      this.onBlur?.();
    });
    canvas.addEventListener("contextmenu", (e) => e.preventDefault());
    canvas.addEventListener("pointerdown", (e) => {
      this.position(e);
      canvas.setPointerCapture(e.pointerId);
      this.pointer.down = true;
      this.pressed.add(e.button === 2 ? "Heavy" : "Light");
      this.onDown?.(this.pointer, e.button);
    });
    canvas.addEventListener("pointermove", (e) => {
      this.position(e);
      this.onMove?.(this.pointer);
    });
    canvas.addEventListener("pointerup", (e) => {
      this.position(e);
      this.pointer.down = false;
      this.released.add(e.button === 2 ? "Heavy" : "Light");
      this.onUp?.(this.pointer);
    });
  }
  position(e) {
    const r = this.canvas.getBoundingClientRect();
    this.pointer.x = ((e.clientX - r.left) * 1280) / r.width;
    this.pointer.y = ((e.clientY - r.top) * 720) / r.height;
  }
  held(...codes) {
    return codes.some((c) => this.keys.has(c) || this.padKeys.has(c));
  }
  tap(...codes) {
    return codes.some((c) => this.pressed.has(c));
  }
  gamepad(dt, brush) {
    const p = Array.from(navigator.getGamepads?.() || []).find(Boolean);
    if (!p) {
      this.padKeys.clear();
      this.axis = 0;
      return;
    }
    this.axis = Math.abs(p.axes[0]) > 0.18 ? p.axes[0] : 0;
    const map = [
      "Space",
      "KeyK",
      "KeyJ",
      "KeyL",
      "ShiftLeft",
      "KeyB",
      "KeyQ",
      "KeyE",
      "KeyM",
      "Escape",
    ];
    p.buttons.forEach((b, i) => {
      const code = map[i];
      if (!code) return;
      if (b.pressed && !this.padPrevious[i]) this.pressed.add(code);
      if (b.pressed) this.padKeys.add(code);
      else this.padKeys.delete(code);
      this.padPrevious[i] = b.pressed;
    });
    if (brush) {
      const x = p.axes[2] || p.axes[0],
        y = p.axes[3] || p.axes[1];
      this.padCursor.x = Math.max(
        0,
        Math.min(1280, this.padCursor.x + x * 620 * dt),
      );
      this.padCursor.y = Math.max(
        0,
        Math.min(720, this.padCursor.y + y * 620 * dt),
      );
      this.pointer.x = this.padCursor.x;
      this.pointer.y = this.padCursor.y;
      const down = p.buttons[7]?.pressed;
      if (down && !this.padDraw) {
        this.pointer.down = true;
        this.onDown?.(this.pointer, 0);
      }
      if (down) this.onMove?.(this.pointer);
      if (!down && this.padDraw) {
        this.pointer.down = false;
        this.onUp?.(this.pointer);
      }
      this.padDraw = down;
    }
  }
  end() {
    this.pressed.clear();
    this.released.clear();
  }
}

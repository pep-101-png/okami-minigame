export class Input {
  constructor(canvas) {
    this.keys = new Set();
    for (const action of [
      "attack",
      "heavy",
      "lightDown",
      "lightUp",
      "heavyDown",
      "heavyUp",
      "jump",
      "dash",
      "interact",
      "pause",
      "mute",
      "bark",
      "voice",
    ])
      this[action] = false;
    this.lightHeld = false;
    this.heavyHeld = false;
    this.yaw = Math.atan2(9, 12);
    this.pitch = 0.18;
    this.zoom = 1;
    this.mouseButtons = new Set();
    const setHold = (kind, held) => {
      const property = kind === "light" ? "lightHeld" : "heavyHeld";
      if (this[property] === held) return;
      this[property] = held;
      this[kind + (held ? "Down" : "Up")] = true;
    };
    window.addEventListener("keydown", (event) => {
      if (
        [
          "Space",
          "KeyW",
          "KeyA",
          "KeyS",
          "KeyD",
          "ArrowUp",
          "ArrowDown",
        ].includes(event.code)
      )
        event.preventDefault();
      this.keys.add(event.code);
      if (event.repeat) return;
      if (event.code === "KeyJ") setHold("light", true);
      else if (event.code === "KeyL") setHold("heavy", true);
      else {
        const action = {
          Space: "jump",
          KeyK: "dash",
          KeyE: "interact",
          Escape: "pause",
          KeyM: "mute",
          KeyB: "bark",
          KeyV: "voice",
        }[event.code];
        if (action) this[action] = true;
      }
    });
    window.addEventListener("keyup", (event) => {
      this.keys.delete(event.code);
      if (event.code === "KeyJ" && !this.mouseButtons.has(0))
        setHold("light", false);
      if (event.code === "KeyL" && !this.mouseButtons.has(2))
        setHold("heavy", false);
    });
    canvas.addEventListener("pointerdown", (event) => {
      if (event.button !== 0 && event.button !== 2) return;
      event.preventDefault();
      this.mouseButtons.add(event.button);
      setHold(event.button === 0 ? "light" : "heavy", true);
    });
    window.addEventListener("pointerup", (event) => {
      this.mouseButtons.delete(event.button);
      if (event.button === 0 && !this.keys.has("KeyJ")) setHold("light", false);
      if (event.button === 2 && !this.keys.has("KeyL")) setHold("heavy", false);
    });
    canvas.addEventListener("contextmenu", (event) => event.preventDefault());
    canvas.addEventListener("pointercancel", () => this.clear());
    window.addEventListener("blur", () => this.clear());
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) this.clear();
    });
    canvas.addEventListener(
      "wheel",
      (event) => {
        event.preventDefault();
        this.zoom = Math.max(
          0.78,
          Math.min(1.25, this.zoom + event.deltaY * 0.00045),
        );
      },
      { passive: false },
    );
  }
  clear() {
    this.keys.clear();
    this.mouseButtons.clear();
    this.lightHeld = this.heavyHeld = false;
    for (const action of [
      "attack",
      "heavy",
      "lightDown",
      "lightUp",
      "heavyDown",
      "heavyUp",
      "jump",
      "dash",
      "interact",
      "pause",
      "bark",
      "voice",
    ])
      this[action] = false;
  }
  consume(name) {
    const value = this[name];
    this[name] = false;
    return value;
  }
}

export class Input {
  constructor(canvas) {
    this.keys = new Set();
    this.attack = false;
    this.jump = false;
    this.dash = false;
    this.interact = false;
    this.pause = false;
    this.mute = false;
    this.yaw = Math.atan2(9, 12);
    this.pitch = 0.18;
    this.zoom = 1;
    window.addEventListener("keydown", (event) => {
      if (["Space", "KeyW", "KeyA", "KeyS", "KeyD", "ArrowUp", "ArrowDown"].includes(event.code))
        event.preventDefault();
      this.keys.add(event.code);
      if (event.repeat) return;
      const action = {
        Space: "jump", KeyJ: "attack", KeyK: "dash", KeyE: "interact",
        Escape: "pause", KeyM: "mute",
      }[event.code];
      if (action) this[action] = true;
    });
    window.addEventListener("keyup", (event) => this.keys.delete(event.code));
    window.addEventListener("blur", () => this.clear());
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) this.clear();
    });
    canvas.addEventListener("mousedown", (event) => {
      if (event.button === 0) this.attack = true;
    });
    canvas.addEventListener("wheel", (event) => {
      event.preventDefault();
      this.zoom = Math.max(0.78, Math.min(1.25, this.zoom + event.deltaY * 0.00045));
    }, { passive: false });
    canvas.addEventListener("contextmenu", (event) => event.preventDefault());
  }
  clear() {
    this.keys.clear();
    for (const key of ["attack", "jump", "dash", "interact", "pause"]) this[key] = false;
  }
  consume(name) {
    const value = this[name];
    this[name] = false;
    return value;
  }
}

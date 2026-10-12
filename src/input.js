import { requestPointer } from "./pointer.js";
export class Input {
  constructor(canvas) {
    this.keys = new Set();
    this.attack = false;
    this.jump = false;
    this.dash = false;
    this.interact = false;
    this.yaw = 0.65;
    this.pitch = 0.18;
    window.addEventListener("keydown", (e) => {
      if (["Space", "KeyW", "KeyA", "KeyS", "KeyD"].includes(e.code))
        e.preventDefault();
      this.keys.add(e.code);
      if (e.code === "Space" && !e.repeat) this.jump = true;
      if (e.code === "KeyJ" && !e.repeat) this.attack = true;
      if (e.code === "KeyK" && !e.repeat) this.dash = true;
      if (e.code === "KeyE" && !e.repeat) this.interact = true;
    });
    window.addEventListener("keyup", (e) => this.keys.delete(e.code));
    window.addEventListener("blur", () => this.keys.clear());
    canvas.addEventListener("mousedown", () => (this.attack = true));
  }
  consume(name) {
    const value = this[name];
    this[name] = false;
    return value;
  }
}

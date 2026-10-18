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
    this.weapon = false;
    this.yaw = Math.atan2(9, 12);
    this.pitch = .448;
    this.cameraDrag = false;
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
          KeyQ: "weapon",
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
      if (event.altKey || event.button !== 0 && event.button !== 2) return;
      event.preventDefault();
      this.mouseButtons.add(event.button);
      setHold(event.button === 0 ? "light" : "heavy", true);
    });
    window.addEventListener("pointerup", (event) => {
      this.mouseButtons.delete(event.button);
      if (event.button === 0 && !this.keys.has("KeyJ")) setHold("light", false);
      if (event.button === 2 && !this.keys.has("KeyL")) setHold("heavy", false);
    });
    canvas.addEventListener('pointerdown',event=>{if(event.button===1||event.altKey){this.cameraDrag=true;this.lastMouse=[event.clientX,event.clientY];event.preventDefault();}});
    window.addEventListener('pointermove',event=>{if(!this.cameraDrag)return;this.yaw-=(event.clientX-this.lastMouse[0])*.005;this.pitch=Math.max(.22,Math.min(.95,this.pitch+(event.clientY-this.lastMouse[1])*.004));this.lastMouse=[event.clientX,event.clientY];});
    window.addEventListener('pointerup',()=>this.cameraDrag=false);
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
    this.weapon = false;this.cameraDrag=false;
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

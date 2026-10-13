// Original synthesized score and effects. No third-party audio downloads.
export class AudioSystem {
  constructor() {
    this.ctx = null;
    this.muted = false;
    this.clock = 0;
    this.beat = 0;
    this.restored = false;
  }
  start() {
    if (!this.ctx) {
      this.ctx = new AudioContext();
      this.master = this.ctx.createGain();
      this.master.gain.value = 0.3;
      this.master.connect(this.ctx.destination);
    }
    this.ctx.resume();
  }
  tone(f, d = 0.2, type = "sine", v = 0.2, slide = 1, delay = 0) {
    if (!this.ctx || this.muted) return;
    const t = this.ctx.currentTime + delay,
      o = this.ctx.createOscillator(),
      g = this.ctx.createGain();
    o.type = type;
    o.frequency.setValueAtTime(f, t);
    o.frequency.exponentialRampToValueAtTime(Math.max(30, f * slide), t + d);
    g.gain.setValueAtTime(0.001, t);
    g.gain.exponentialRampToValueAtTime(v, t + 0.012);
    g.gain.exponentialRampToValueAtTime(0.001, t + d);
    o.connect(g);
    g.connect(this.master);
    o.start(t);
    o.stop(t + d + 0.02);
  }
  noise(d = 0.15, v = 0.15, f = 1200) {
    if (!this.ctx || this.muted) return;
    const n = this.ctx.createBuffer(
        1,
        this.ctx.sampleRate * d,
        this.ctx.sampleRate,
      ),
      a = n.getChannelData(0);
    for (let i = 0; i < a.length; i++)
      a[i] = (Math.random() * 2 - 1) * (1 - i / a.length);
    const s = this.ctx.createBufferSource(),
      filter = this.ctx.createBiquadFilter(),
      g = this.ctx.createGain();
    filter.type = "lowpass";
    filter.frequency.value = f;
    g.gain.value = v;
    s.buffer = n;
    s.connect(filter);
    filter.connect(g);
    g.connect(this.master);
    s.start();
  }
  play(name) {
    const table = {
      step: [110, 0.055, 0.04, 0.65],
      jump: [300, 0.2, 0.13, 1.6],
      land: [75, 0.16, 0.2, 0.5],
      light: [440, 0.13, 0.16, 0.3],
      heavy: [100, 0.3, 0.3, 0.4],
      hit: [170, 0.12, 0.25, 0.3],
      hurt: [240, 0.25, 0.18, 0.35],
      brush: [800, 0.4, 0.1, 0.6],
      ink: [1100, 0.04, 0.035, 0.7],
      collect: [880, 0.2, 0.12, 1.5],
      ui: [500, 0.1, 0.1, 1.2],
      dodge: [420, 0.12, 0.1, 0.45],
      enemy: [140, 0.2, 0.12, 0.5],
      bomb: [60, 0.6, 0.3, 0.5],
      bloom: [440, 0.6, 0.17, 2],
      win: [523, 0.8, 0.2, 1.5],
    };
    const a = table[name] || table.light;
    this.tone(a[0], a[1], "sine", a[2], a[3]);
    if (
      [
        "heavy",
        "hit",
        "land",
        "dodge",
        "brush",
        "bomb",
        "step",
        "light",
      ].includes(name)
    )
      this.noise(a[1], a[2] * 0.7, name === "brush" ? 2500 : 900);
    if (["bloom", "win", "collect"].includes(name)) {
      this.tone(a[0] * 1.25, 0.7, "sine", 0.08, 1, 0.14);
      this.tone(a[0] * 1.5, 0.9, "sine", 0.06, 1, 0.3);
    }
  }
  update(dt, restored) {
    this.restored = restored;
    if (!this.ctx || this.muted) return;
    this.clock -= dt;
    if (this.clock <= 0) {
      this.clock = 0.62;
      const scale = restored
        ? [220, 277.18, 329.63, 440, 493.88, 554.37, 659.25]
        : [196, 220, 261.63, 293.66, 392, 440, 523.25];
      const seq = [0, 4, 2, 5, 3, 2, 4, 1, 0, 2, 6, 4, 3, 5, 2, 1],
        f = scale[seq[this.beat++ % seq.length]];
      this.tone(f, 1.25, "sine", 0.048);
      if (this.beat % 4 === 0) {
        this.tone(scale[0] / 2, 2.7, "sine", 0.035);
        this.noise(0.55, 0.012, 650);
      }
      if (this.beat % 8 === 0) this.tone(1400, 1.2, "sine", 0.015, 0.7);
    }
  }
  toggle() {
    this.muted = !this.muted;
    if (this.master) this.master.gain.value = this.muted ? 0 : 0.3;
  }
}

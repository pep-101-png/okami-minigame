/** Original Web Audio synthesis: all sounds are generated locally. */
export class AudioController {
  constructor() {
    this.context = this.ctx = null;
    this.master = null;
    this.volume = 0.45;
    this.muted = false;
    this.unlocked = false;
    this.voices = 0;
    this.maxVoices = 28;
    this.lastSound = new Map();
    this.ambientTime = 0;
    this.chimeTime = 16;
    this.unlockGesture = () => {
      void this.unlock();
    };
    if (typeof document !== "undefined") {
      document.addEventListener("pointerdown", this.unlockGesture);
      document.addEventListener("keydown", this.unlockGesture);
    }
  }

  async unlock() {
    const AudioContext =
      globalThis.AudioContext || globalThis.webkitAudioContext;
    if (!AudioContext) return false;
    try {
      if (!this.context) {
        this.context = this.ctx = new AudioContext();
        this.master = this.context.createGain();
        this.master.gain.value = this.muted ? 0 : this.volume;
        const compressor = this.context.createDynamicsCompressor();
        compressor.threshold.value = -15;
        compressor.knee.value = 12;
        compressor.ratio.value = 3;
        compressor.attack.value = 0.004;
        compressor.release.value = 0.16;
        this.master.connect(compressor);
        compressor.connect(this.context.destination);
        this.compressor = compressor;
        this.noiseBuffer = this.context.createBuffer(
          1,
          this.context.sampleRate * 2,
          this.context.sampleRate,
        );
        const data = this.noiseBuffer.getChannelData(0);
        let brown = 0;
        for (let i = 0; i < data.length; i++) {
          brown = (brown + (Math.random() * 2 - 1) * 0.02) / 1.02;
          data[i] = brown * 3.5 + (Math.random() * 2 - 1) * 0.21;
        }
      }
      if (this.context.state === "suspended") await this.context.resume();
      this.unlocked = this.context.state === "running";
      if (this.unlocked) {
        document.removeEventListener("pointerdown", this.unlockGesture);
        document.removeEventListener("keydown", this.unlockGesture);
        this.startAmbience();
      }
      return this.unlocked;
    } catch {
      return false;
    }
  }

  setMuted(muted) {
    this.muted = Boolean(muted);
    if (this.master)
      this.master.gain.setTargetAtTime(
        this.muted ? 0 : this.volume,
        this.context.currentTime,
        0.035,
      );
    return this.muted;
  }
  toggleMute() {
    return this.setMuted(!this.muted);
  }
  setVolume(volume) {
    this.volume = Math.min(1, Math.max(0, Number(volume) || 0));
    if (this.master && !this.muted)
      this.master.gain.setTargetAtTime(
        this.volume,
        this.context.currentTime,
        0.035,
      );
    return this.volume;
  }

  startAmbience() {
    if (this.wind) return;
    const source = this.context.createBufferSource();
    source.buffer = this.noiseBuffer;
    source.loop = true;
    const filter = this.context.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.value = 520;
    filter.Q.value = 0.35;
    const gain = this.context.createGain();
    gain.gain.value = 0.055;
    source.connect(filter);
    filter.connect(gain);
    gain.connect(this.master);
    source.start();
    this.wind = { source, filter, gain };
  }

  envelope(gain, start, duration, volume, attack = 0.005) {
    gain.gain.setValueAtTime(0.0001, start);
    gain.gain.exponentialRampToValueAtTime(
      Math.max(0.0002, volume),
      start + Math.min(duration * 0.35, attack),
    );
    gain.gain.exponentialRampToValueAtTime(0.0001, start + duration);
  }
  connectVoice(
    source,
    filter,
    duration,
    volume,
    { delay = 0, pan = 0, attack = 0.005 } = {},
  ) {
    if (this.voices >= this.maxVoices) return;
    const start = this.context.currentTime + delay;
    const gain = this.context.createGain();
    this.envelope(gain, start, duration, volume, attack);
    const panner = this.context.createStereoPanner?.();
    if (filter) {
      source.connect(filter);
      filter.connect(gain);
    } else source.connect(gain);
    if (panner) {
      panner.pan.value = Math.max(-1, Math.min(1, pan));
      gain.connect(panner);
      panner.connect(this.master);
    } else gain.connect(this.master);
    this.voices++;
    source.onended = () => {
      source.disconnect();
      filter?.disconnect();
      gain.disconnect();
      panner?.disconnect();
      this.voices = Math.max(0, this.voices - 1);
    };
    source.start(start);
    source.stop(start + duration + 0.01);
  }
  noise(
    duration,
    volume,
    frequency = 1800,
    {
      endFrequency = frequency,
      type = "bandpass",
      q = 0.6,
      delay = 0,
      pan = 0,
      attack = 0.005,
    } = {},
  ) {
    if (this.voices >= this.maxVoices) return;
    const source = this.context.createBufferSource();
    source.buffer = this.noiseBuffer;
    source.loop = true;
    const filter = this.context.createBiquadFilter();
    filter.type = type;
    filter.Q.value = q;
    const start = this.context.currentTime + delay;
    filter.frequency.setValueAtTime(Math.max(30, frequency), start);
    filter.frequency.exponentialRampToValueAtTime(
      Math.max(30, endFrequency),
      start + duration,
    );
    this.connectVoice(source, filter, duration, volume, { delay, pan, attack });
  }
  tone(
    frequency,
    endFrequency,
    duration,
    volume,
    {
      type = "sine",
      delay = 0,
      pan = 0,
      attack = 0.004,
      filterFrequency = 2200,
    } = {},
  ) {
    if (this.voices >= this.maxVoices) return;
    const source = this.context.createOscillator();
    source.type = type;
    const start = this.context.currentTime + delay;
    source.frequency.setValueAtTime(Math.max(20, frequency), start);
    source.frequency.exponentialRampToValueAtTime(
      Math.max(20, endFrequency),
      start + duration,
    );
    const filter = this.context.createBiquadFilter();
    filter.type = "lowpass";
    filter.frequency.value = filterFrequency;
    this.connectVoice(source, filter, duration, volume, { delay, pan, attack });
  }

  vocal(kind, { strong = false, pan = 0 } = {}) {
    const duration =
      { bark: 0.26, growl: 0.85, whimper: 0.55, howl: 1.65 }[kind] || 0.26;
    const buffer = this.context.createBuffer(
        1,
        Math.ceil(duration * this.context.sampleRate),
        this.context.sampleRate,
      ),
      data = buffer.getChannelData(0);
    let phase = 0,
      seed = 217,
      brown = 0;
    for (let i = 0; i < data.length; i++) {
      const t = i / this.context.sampleRate,
        u = t / duration;
      seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
      const noise = (seed / 4294967296) * 2 - 1;
      brown = (brown + noise * 0.05) / 1.05;
      const f =
        kind === "growl"
          ? 78 + 13 * Math.sin(t * 35)
          : kind === "whimper"
            ? 460 - 180 * u + 30 * Math.sin(t * 48)
            : kind === "howl"
              ? 190 + 160 * Math.sin(u * Math.PI * 0.85) + 6 * Math.sin(t * 38)
              : 150 - 65 * u;
      phase += (f / this.context.sampleRate) * Math.PI * 2;
      const voiced =
        Math.sin(phase) +
        0.35 * Math.sin(phase * 2) +
        0.15 * Math.sin(phase * 3);
      const gate =
        kind === "growl"
          ? 0.65 + 0.35 * Math.sin(t * 45)
          : kind === "bark"
            ? Math.pow(1 - u, 0.6)
            : Math.sin(Math.PI * u);
      data[i] =
        (voiced * 0.24 +
          noise * (kind === "bark" ? 0.2 : 0.04) +
          brown * (kind === "growl" ? 0.45 : 0.13)) *
        gate;
    }
    const source = this.context.createBufferSource();
    source.buffer = buffer;
    const filter = this.context.createBiquadFilter();
    filter.type = "bandpass";
    filter.Q.value = 0.65;
    filter.frequency.setValueAtTime(
      kind === "whimper"
        ? 1100
        : kind === "howl"
          ? 760
          : kind === "growl"
            ? 330
            : 850,
      this.context.currentTime,
    );
    filter.frequency.exponentialRampToValueAtTime(
      kind === "whimper" ? 700 : kind === "growl" ? 230 : 520,
      this.context.currentTime + duration,
    );
    this.connectVoice(
      source,
      filter,
      duration,
      strong ? 0.9 : kind === "whimper" ? 0.6 : 0.65,
      { pan, attack: kind === "bark" ? 0.006 : 0.04 },
    );
  }

  play(name, { combo = 1, heavy = false, speed = 0, pan = 0 } = {}) {
    if (!this.unlocked || this.muted || this.context?.state !== "running")
      return false;
    const now = this.context.currentTime;
    const interval =
      {
        footstep: 0.07,
        hit: 0.035,
        heavyHit: 0.06,
        enemyDeath: 0.09,
        enemyWindup: 0.1,
      }[name] ?? 0.025;
    if (now - (this.lastSound.get(name) ?? -100) < interval) return false;
    this.lastSound.set(name, now);
    const location = { pan };
    if (["barkStun", "barkSoft", "growl", "whimper", "howl"].includes(name)) {
      this.vocal(name.startsWith("bark") ? "bark" : name, {
        strong: name === "barkStun",
        pan,
      });
      if (name === "barkStun") {
        this.noise(0.18, 0.18, 420, { endFrequency: 180, type: "lowpass" });
      }
    } else if (name === "chargeReady") {
      this.tone(heavy ? 220 : 660, heavy ? 300 : 990, 0.26, 0.08, {
        type: "triangle",
      });
      this.noise(0.18, 0.06, 1200, { endFrequency: 1900, attack: 0.03 });
    } else if (name === "swing") {
      const duration = [0, 0.15, 0.24, 0.3][combo] ?? 0.15;
      this.noise(
        duration,
        combo === 3 ? 0.28 : 0.17,
        combo === 2 ? 850 : 1450,
        {
          ...location,
          endFrequency: combo === 3 ? 320 : 2400,
          q: 0.45,
          attack: 0.045,
        },
      );
      if (combo === 3) this.tone(105, 58, 0.16, 0.07, location);
      else this.noise(0.035, 0.055, 400, { ...location, type: "lowpass" });
    } else if (name === "hit" || name === "heavyHit") {
      const strong = heavy || name === "heavyHit";
      this.tone(
        strong ? 165 : 200,
        strong ? 58 : 86,
        strong ? 0.17 : 0.1,
        strong ? 0.27 : 0.18,
        location,
      );
      this.noise(strong ? 0.15 : 0.08, strong ? 0.36 : 0.24, 1600, {
        ...location,
        endFrequency: 450,
      });
      this.tone(
        strong ? 580 : 940,
        strong ? 390 : 750,
        strong ? 0.16 : 0.1,
        0.055,
        { ...location, type: "triangle" },
      );
    } else if (name === "footstep") {
      this.noise(
        0.045,
        0.12 + (speed > 6 ? 0.035 : 0),
        1000 + Math.random() * 500,
        { ...location, type: "lowpass", endFrequency: 350 },
      );
      this.tone(105 + Math.random() * 20, 65, 0.035, 0.045, location);
    } else if (name === "jump") {
      this.noise(0.12, 0.16, 900, {
        ...location,
        endFrequency: 2300,
        attack: 0.012,
      });
      this.tone(140, 105, 0.09, 0.045, location);
    } else if (name === "land") {
      this.noise(0.07, 0.17, 1100, {
        ...location,
        type: "lowpass",
        endFrequency: 360,
      });
      this.tone(130, 65, 0.065, 0.1, location);
    } else if (name === "dodge") {
      this.noise(0.18, 0.17, 1800, {
        ...location,
        endFrequency: 650,
        attack: 0.025,
      });
    } else if (name === "enemyWindup") {
      this.noise(0.21, 0.1, 360, {
        ...location,
        endFrequency: 720,
        q: 1,
        attack: 0.03,
      });
      this.tone(135, 95, 0.18, 0.025, {
        ...location,
        type: "triangle",
        filterFrequency: 500,
      });
    } else if (name === "enemyAttack") {
      this.noise(0.22, 0.18, 650, {
        ...location,
        endFrequency: 1700,
        attack: 0.01,
      });
    } else if (name === "playerHit") {
      this.vocal("whimper", location);
      this.tone(120, 46, 0.2, 0.21, location);
      this.noise(0.14, 0.24, 1500, { ...location, endFrequency: 260 });
    } else if (name === "enemyDeath") {
      this.noise(0.65, 0.19, 1200, {
        ...location,
        endFrequency: 210,
        type: "highpass",
        attack: 0.055,
      });
      this.tone(440, 445, 0.6, 0.035, {
        ...location,
        type: "triangle",
        delay: 0.14,
      });
      this.tone(660, 656, 0.65, 0.025, { ...location, delay: 0.25 });
    } else if (name === "interact" || name === "collect") {
      this.tone(660, 659, 0.2, 0.07, { ...location, type: "triangle" });
      this.tone(880, 875, 0.27, 0.045, { ...location, delay: 0.065 });
    } else if (name === "heal") {
      for (let i = 0; i < 3; i++)
        this.tone([330, 440, 660][i], [330, 440, 660][i], 0.6, 0.045, {
          ...location,
          delay: i * 0.14,
        });
    } else if (name === "victory") {
      for (let i = 0; i < 4; i++)
        this.tone(
          [330, 440, 550, 660][i],
          [330, 440, 550, 660][i],
          0.9,
          0.065,
          { ...location, type: "triangle", delay: i * 0.19, attack: 0.02 },
        );
    } else return false;
    return true;
  }

  update(dt, { combat = false } = {}) {
    if (!this.unlocked) return;
    this.ambientTime += dt;
    if (this.wind) {
      const now = this.context.currentTime;
      this.wind.filter.frequency.setTargetAtTime(
        470 + Math.sin(this.ambientTime * 0.19) * 130,
        now,
        0.4,
      );
      this.wind.gain.gain.setTargetAtTime(
        (combat ? 0.035 : 0.055) *
          (0.8 + Math.sin(this.ambientTime * 0.31) * 0.2),
        now,
        0.5,
      );
    }
    this.chimeTime -= dt;
    if (this.chimeTime <= 0) {
      this.chimeTime = 18 + Math.random() * 18;
      if (!combat && !this.muted) {
        const frequency = [440, 550, 660][Math.floor(Math.random() * 3)];
        this.tone(frequency, frequency * 0.998, 2.4, 0.022, {
          type: "sine",
          pan: Math.random() * 0.8 - 0.4,
          attack: 0.02,
        });
        this.tone(frequency * 2.01, frequency * 2, 1.25, 0.011, {
          type: "triangle",
          pan: -0.25,
          attack: 0.01,
        });
      }
    }
  }
  dispose() {
    document.removeEventListener("pointerdown", this.unlockGesture);
    document.removeEventListener("keydown", this.unlockGesture);
    this.wind?.source.stop();
    this.wind?.source.disconnect();
    if (this.context && this.context.state !== "closed")
      void this.context.close();
  }
}

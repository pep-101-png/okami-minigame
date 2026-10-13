import { clamp, damp } from "./math.js";
import { collide, WIDTH } from "./world.js";
export const WEAPONS = [
  { id: "mirror", name: "Dawn Mirror", range: 145, speed: 1, damage: 1 },
  { id: "beads", name: "River Beads", range: 255, speed: 0.85, damage: 1 },
  { id: "blade", name: "Mountain Fang", range: 180, speed: 1.35, damage: 2 },
];
export class Player {
  constructor() {
    Object.assign(this, {
      x: 260,
      y: 575,
      vx: 0,
      vy: 0,
      facing: 1,
      grounded: true,
      hp: 8,
      maxHp: 8,
      ink: 100,
      stride: 0,
      attack: null,
      combo: 0,
      comboWindow: 0,
      buffer: null,
      dodge: 0,
      dodgeCooldown: 0,
      hurt: 0,
      land: 0,
      coyote: 0.1,
      jumpBuffer: 0,
      jumps: 0,
      doubleJump: false,
      weapon: 0,
      unlocked: 1,
      pearls: 0,
      dead: false,
      deathTime: 0,
      brush: false,
      turn: 0,
      footClock: 0,
    });
    this.attackId = 0;
  }
  startAttack(kind, g) {
    if (this.dead || this.dodge > 0) return;
    if (this.attack) {
      this.buffer = kind;
      return;
    }
    if (!this.grounded) kind = "air";
    else if (kind === "light" && Math.abs(this.vx) > 310) kind = "running";
    this.combo =
      kind === "light" && this.comboWindow > 0 ? (this.combo % 3) + 1 : 1;
    const w = WEAPONS[this.weapon],
      dur =
        {
          light: [0.34, 0.43, 0.57][this.combo - 1],
          heavy: 0.76,
          air: 0.6,
          running: 0.48,
        }[kind] * w.speed;
    this.attack = {
      id: ++this.attackId,
      kind,
      combo: this.combo,
      t: 0,
      duration: dur,
      hit: false,
      hits: new Set(),
      weapon: this.weapon,
    };
    if (kind === "air") this.vy = -100;
    g.audio.play(kind === "heavy" ? "heavy" : "light");
  }
  damage(n, dir, g) {
    if (this.hurt > 0 || this.dodge > 0 || this.dead) return;
    this.hp = Math.max(0, this.hp - n);
    this.hurt = 1.1;
    this.vx = dir * 290;
    this.vy = -210;
    this.attack = null;
    g.audio.play("hurt");
    g.effect(this.x, this.y - 45, "hurt", 12);
    if (!this.hp) {
      this.dead = true;
      this.deathTime = 0;
    }
  }
  update(dt, input, g) {
    if (this.dead) {
      this.deathTime += dt;
      this.vx = damp(this.vx, 0, 8, dt);
      return;
    }
    let oldY = this.y;
    const wasGround = this.grounded;
    this.hurt = Math.max(0, this.hurt - dt);
    this.land = Math.max(0, this.land - dt);
    this.turn = Math.max(0, this.turn - dt);
    this.comboWindow = Math.max(0, this.comboWindow - dt);
    this.dodge = Math.max(0, this.dodge - dt);
    this.dodgeCooldown = Math.max(0, this.dodgeCooldown - dt);
    this.ink = clamp(this.ink + dt * 5, 0, 100);
    let axis =
      (input.held("KeyD", "ArrowRight") ? 1 : 0) -
      (input.held("KeyA", "ArrowLeft") ? 1 : 0);
    if (input.axis) axis = input.axis;
    if (axis && Math.sign(axis) !== this.facing && !this.attack) {
      this.facing = Math.sign(axis);
      this.turn = 0.16;
    }
    const target =
      axis *
      (input.held("ControlLeft", "ControlRight")
        ? 135
        : input.held("ShiftLeft", "ShiftRight")
          ? 440
          : 285);
    this.vx = damp(this.vx, target, this.grounded ? (axis ? 9 : 11) : 4, dt);
    if (input.tap("Space", "KeyW", "ArrowUp")) this.jumpBuffer = 0.15;
    else this.jumpBuffer = Math.max(0, this.jumpBuffer - dt);
    this.coyote = wasGround ? 0.11 : Math.max(0, this.coyote - dt);
    if (
      this.jumpBuffer > 0 &&
      (this.coyote > 0 || (this.doubleJump && this.jumps < 2))
    ) {
      this.vy = -630;
      this.grounded = false;
      this.coyote = 0;
      this.jumpBuffer = 0;
      this.jumps++;
      g.audio.play("jump");
      g.effect(this.x, this.y, "dust", 7);
    }
    if (input.released.has("Space") && this.vy < -280) this.vy = -280;
    if (input.tap("KeyK") && this.dodgeCooldown <= 0 && this.hurt < 0.4) {
      this.dodge = 0.3;
      this.dodgeCooldown = 0.64;
      this.attack = null;
      this.vx = this.facing * 640;
      g.audio.play("dodge");
      g.effect(this.x, this.y - 25, "petal", 9);
    }
    if (this.dodge > 0) this.vx = this.facing * 620;
    if (input.tap("KeyJ", "Light")) this.startAttack("light", g);
    if (input.tap("KeyL", "Heavy")) this.startAttack("heavy", g);
    if (input.tap("Digit1")) this.weapon = 0;
    if (input.tap("Digit2") && this.unlocked >= 2) this.weapon = 1;
    if (input.tap("Digit3") && this.unlocked >= 3) this.weapon = 2;
    if (input.tap("KeyQ")) this.weapon = (this.weapon + 1) % this.unlocked;
    if (this.attack) {
      const a = this.attack;
      a.t += dt;
      const active = a.t / a.duration;
      if (active > 0.27 && active < 0.72) g.resolveAttack(a);
      if (a.kind === "running") this.vx = this.facing * 460;
      if (a.kind === "heavy") this.vx *= Math.exp(-6 * dt);
      if (a.kind === "air" && active > 0.35) this.vy = 750;
      if (a.t >= a.duration) {
        this.attack = null;
        this.comboWindow = 0.34;
        if (this.buffer) {
          const b = this.buffer;
          this.buffer = null;
          this.startAttack(b, g);
        }
      }
    }
    this.vy += 1650 * dt;
    this.x = clamp(this.x + this.vx * dt, 90, WIDTH - 120);
    const gate = g.world.gate;
    if (!gate.open && this.x > gate.x - 60 && this.x < gate.x + 80)
      this.x = this.facing > 0 ? gate.x - 61 : gate.x + 81;
    const wall = g.world.wall;
    if (!wall.broken && this.x > wall.x - 48 && this.x < wall.x + 55)
      this.x = this.facing > 0 ? wall.x - 49 : wall.x + 56;
    if (g.world.bossAwake && !g.world.bossDefeated)
      this.x = clamp(this.x, 5030, 6060);
    this.y += this.vy * dt;
    const bank = g.world.platforms.find(
      (s) => s.h > 100 && this.x >= s.x && this.x < s.x + s.w,
    );
    if (
      wasGround &&
      this.vy >= 0 &&
      bank &&
      oldY >= bank.y &&
      oldY - bank.y <= 64
    ) {
      this.y = bank.y;
      oldY = bank.y;
      this.vy = 0;
    }
    collide(g.world, this, oldY, dt);
    if (this.grounded) {
      this.jumps = 0;
      if (!wasGround) {
        this.land = 0.2;
        g.audio.play("land");
        g.effect(this.x, this.y, "dust", 8);
        if (this.attack?.kind === "air") {
          g.slam(this.x, this.y);
          this.attack = null;
        }
      }
    } else {
      if (
        axis &&
        ((!gate.open && Math.abs(this.x - gate.x) < 70) ||
          (!wall.broken && Math.abs(this.x - wall.x) < 60)) &&
        this.vy > 80
      )
        this.vy = 80;
    }
    this.stride +=
      Math.abs(this.vx) * dt * (Math.abs(this.vx) > 340 ? 0.028 : 0.038);
    if (this.grounded && Math.abs(this.vx) > 75) {
      this.footClock -= dt;
      if (this.footClock < 0) {
        this.footClock = Math.abs(this.vx) > 340 ? 0.14 : 0.22;
        g.audio.play("step");
        g.effect(
          this.x - 35 * this.facing,
          this.y - 5,
          g.world.restored ? "petal" : "leaf",
          3,
        );
      }
    }
  }
}

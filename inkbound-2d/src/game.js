import { Player, WEAPONS } from "./player.js";
import { createWorld } from "./world.js";
import { updateEnemies, hitEnemy } from "./enemies.js";
import { Brush } from "./brush.js";
import { AudioSystem } from "./audio.js";
import { distance } from "./math.js";
export class Game {
  constructor(input, renderer) {
    this.input = input;
    this.renderer = renderer;
    this.audio = new AudioSystem();
    this.state = "title";
    this.player = new Player();
    this.world = createWorld();
    this.brush = new Brush(this);
    this.particles = [];
    this.time = 0;
    this.hitstop = 0;
    this.pendingInputs = new Set();
    this.message = "";
    this.messageTime = 0;
    this.camera = { x: 0, y: 0, zoom: 1 };
    input.onBlur = () => {
      if (this.state === "playing") {
        this.state = "paused";
        this.brush.active = false;
        this.player.brush = false;
        this.ui();
      }
    };
    this.ui();
  }
  begin() {
    this.audio.start();
    this.state = "playing";
    this.say(
      "A river has forgotten its name. Carry spring back to its source.",
      5,
    );
    this.ui();
  }
  reset() {
    this.player = new Player();
    this.world = createWorld();
    this.particles = [];
    this.pendingInputs.clear();
    this.brush.active = false;
    this.brush.history = [];
    this.camera = { x: 0, y: 0, zoom: 1 };
    this.begin();
  }
  say(text, seconds = 3) {
    this.message = text;
    this.messageTime = seconds;
    this.ui();
  }
  effect(x, y, kind, count = 10) {
    for (let i = 0; i < count; i++) {
      if (this.particles.length > 700) this.particles.shift();
      this.particles.push({
        x,
        y,
        vx: (Math.random() - 0.5) * (kind === "bloom" ? 350 : 180),
        vy: -Math.random() * (kind === "bloom" ? 240 : 130),
        life: kind === "bloom" ? 2.8 : 1.0 + Math.random(),
        max: 2,
        kind,
        size: 2 + Math.random() * 6,
        angle: Math.random() * 6.28,
      });
    }
  }
  resolveAttack(a) {
    const p = this.player,
      w = WEAPONS[a.weapon],
      range = w.range + (a.kind === "heavy" ? 30 : 0),
      damage =
        w.damage +
        (a.kind === "heavy"
          ? 2
          : a.kind === "air"
            ? 2
            : a.kind === "running"
              ? 1
              : a.combo === 3
                ? 1
                : 0);
    for (const e of this.world.enemies) {
      if (
        e.dead ||
        a.hits.has(e) ||
        (e.type === "boss" && !this.world.bossAwake)
      )
        continue;
      const dx = e.x - p.x,
        dy = e.y - p.y;
      if (
        dx * p.facing > -45 &&
        dx * p.facing < range &&
        Math.abs(dy) < (a.kind === "air" ? 180 : 120)
      ) {
        a.hits.add(e);
        hitEnemy(e, damage, p.facing, this);
        if (a.weapon === 1 && !e.dead) {
          e.vx = -p.facing * 170;
          e.timer = 0.5;
        } else if (a.weapon === 0) p.ink = Math.min(100, p.ink + 2);
      }
    }
    if (
      a.kind === "heavy" &&
      Math.abs(p.x - this.world.wall.x) < range &&
      !this.world.wall.broken
    ) {
      this.world.wall.broken = true;
      this.effect(this.world.wall.x, 520, "dust", 35);
      this.audio.play("bomb");
      this.say("A hidden shrine path is revealed.", 3);
    }
  }
  slam(x, y) {
    this.audio.play("heavy");
    this.effect(x, y, "shock", 25);
    for (const e of this.world.enemies)
      if (!e.dead && distance({ x, y }, e) < 210)
        hitEnemy(e, 3, this.player.facing, this);
  }
  update(dt) {
    this.input.gamepad(dt, this.brush.active);
    if (this.input.tap("KeyM")) {
      this.audio.toggle();
      this.ui();
    }
    if (this.input.tap("Escape")) {
      if (this.state === "playing") {
        this.brush.active = false;
        this.player.brush = false;
        this.state = "paused";
      } else if (this.state === "paused") this.state = "playing";
      this.ui();
    }
    if (this.input.tap("KeyB", "Tab") && this.state === "playing")
      this.brush.toggle();
    this.brush.update(dt);
    this.messageTime = Math.max(0, this.messageTime - dt);
    if (this.state === "playing" && !this.brush.active) {
      for (const code of this.input.pressed)
        if (
          [
            "Space",
            "KeyW",
            "ArrowUp",
            "KeyJ",
            "Light",
            "KeyL",
            "Heavy",
            "KeyK",
          ].includes(code)
        )
          this.pendingInputs.add(code);
      this.audio.update(dt, this.world.restored);
      this.hitstop = Math.max(0, this.hitstop - dt);
      if (this.hitstop === 0) {
        for (const code of this.pendingInputs) this.input.pressed.add(code);
        this.pendingInputs.clear();
        this.time += dt;
        this.player.update(dt, this.input, this);
        updateEnemies(this, dt);
        for (const b of this.world.bombs) {
          b.fuse -= dt;
          if (b.fuse <= 0 && !b.done) {
            b.done = true;
            this.audio.play("bomb");
            this.effect(b.x, b.y, "shock", 40);
            for (const e of this.world.enemies)
              if (!e.dead && distance(b, e) < 240) {
                e.exposed = 4;
                hitEnemy(e, 4, this.player.facing, this, true);
              }
            if (distance(b, { x: this.world.wall.x, y: 520 }) < 230)
              this.world.wall.broken = true;
          }
        }
        this.world.bombs = this.world.bombs.filter((b) => !b.done);
        for (const item of this.world.pickups) {
          if (
            !item.got &&
            distance({ x: this.player.x, y: this.player.y - 32 }, item) < 65
          ) {
            item.got = true;
            this.player.pearls += item.kind === "treasure" ? 5 : 1;
            this.player.ink = Math.min(100, this.player.ink + 10);
            this.audio.play("collect");
            this.effect(item.x, item.y, "gold", 12);
            if (item.kind === "treasure")
              this.say("A forgotten offering · +5 sun pearls", 2);
          }
        }
        this.world.restoration = Math.min(
          1,
          this.world.restoration + dt * 0.18,
        );
        if (this.player.dead && this.player.deathTime > 1.4) {
          this.state = "defeat";
          this.ui();
        }
        if (this.world.bossDefeated && this.player.x > 6350) {
          this.state = "won";
          this.audio.play("win");
          this.ui();
        }
      }
      for (const p of this.particles) {
        p.life -= dt;
        p.x += p.vx * dt;
        p.y += p.vy * dt;
        p.vy += p.kind === "petal" || p.kind === "bloom" ? 20 : 110;
        p.angle += dt;
      }
      this.particles = this.particles.filter((p) => p.life > 0);
    }
    this.renderer.updateCamera(this, dt);
    this.renderHUD();
    this.input.end();
  }
  objective() {
    const w = this.world,
      p = this.player;
    if (!w.trees[0].restored)
      return "Reach the river willow →\nB: freeze time. Draw a circle around its crown.";
    if (!w.basin.filled)
      return "Restore the river wheel →\nDraw from the blue river seal to the stone basin.";
    if (!w.restored)
      return "Release the cursed grove →\nDefeat its spirits, then circle the great tree.";
    if (!w.bossDefeated)
      return "Cross the ancient wall →\nHeavy strike / bomb spiral. Face Kurobane at the shrine.";
    return "Follow the petals east →\nReach the dawn shrine.";
  }
  ui() {
    this.hudCache = {};
    const root = document.querySelector("#ui");
    let overlay = "";
    if (this.state !== "playing") {
      const title = {
        title: "The River<br>Remembers",
        paused: "A moment<br>of stillness",
        defeat: "Embers endure.",
        won: "Spring returns.",
      }[this.state];
      const detail = {
        title:
          "A divine wolf. A broken river. One stroke of ink can wake the world.<br>Explore a painted riverbank, restore the grove, and unbind its guardian.",
        paused: "The river will wait. Your journey resumes where you left it.",
        defeat:
          "Read the spirits’ golden tells, dodge their attacks, and use ink to break guarded seals.",
        won: "The grove blooms, the river runs clear, and the guardian is free. You have completed this first chapter.",
      }[this.state];
      overlay = `<div class="overlay"><div class="card"><div class="eyebrow">INKBOUND · CHAPTER ONE</div><h1>${title}</h1><p>${detail}</p><div class="keys">A / D · Move &nbsp; SHIFT · Sprint &nbsp; CTRL · Walk &nbsp; SPACE · Jump<br>J / Left click · Combo &nbsp; L / Right click · Heavy &nbsp; K · Dodge<br>B / TAB · Draw with the brush &nbsp; Q / 1–3 · Weapon &nbsp; ESC · Pause<br>Brush: line = cut · circle = bloom · zigzag = wind · spiral = bomb<br>Controller: left stick move · A jump · X/Y attack · B dodge<br>RB brush · right stick draws · RT holds the brush</div><button id="play">${this.state === "title" ? "FOLLOW THE RIVER →" : this.state === "paused" ? "RESUME →" : "PLAY AGAIN →"}</button><button id="mute">${this.audio.muted ? "SOUND OFF" : "SOUND ON"}</button></div></div>`;
    }
    root.innerHTML = `<div class="hud"><div class="brand">INKBOUND <span style="color:#b3483a">❀</span></div><div class="meter" id="health"></div><div class="ink"><i id="ink-fill"></i></div><div class="small" id="weapon"></div></div><div class="objective" id="objective"></div><div class="toast" id="toast"></div><div class="help">A D · move &nbsp; SHIFT · sprint &nbsp; SPACE · jump &nbsp; J / L · attacks &nbsp; K · dodge &nbsp; B · brush &nbsp; Q · weapon &nbsp; ESC · pause</div><div class="boss hidden" id="boss">KUROBANE · BROKEN RIVER GUARDIAN<div class="track"><i id="boss-fill"></i></div></div><div class="brush-note ${this.brush.active ? "" : "hidden"}">Time rests on the paper. Draw → release to cast. B to return.<br><small>Line: slash · Circle: bloom · Zigzag: wind · Spiral: bomb · River → basin: water</small></div>${overlay}`;
    document.querySelector("#play")?.addEventListener("click", () => {
      if (this.state === "title") this.begin();
      else if (this.state === "paused") {
        this.state = "playing";
        this.ui();
      } else this.reset();
    });
    document.querySelector("#mute")?.addEventListener("click", () => {
      this.audio.toggle();
      this.ui();
    });
    this.renderHUD();
  }
  renderHUD() {
    if (!document.querySelector("#health")) return;
    const p = this.player,
      w = this.world;
    if (this.hudCache.hp !== p.hp) {
      document.querySelector("#health").innerHTML = Array.from(
        { length: p.maxHp },
        (_, i) => `<i class="heart ${i >= p.hp ? "empty" : ""}"></i>`,
      ).join("");
      this.hudCache.hp = p.hp;
    }
    document.querySelector("#ink-fill").style.width = `${p.ink}%`;
    document.querySelector("#weapon").textContent =
      `${WEAPONS[p.weapon].name} · ${p.pearls} sun pearls${p.doubleJump ? " · Double jump" : ""}`;
    document.querySelector("#objective").innerHTML = this.objective().replace(
      "\n",
      "<br>",
    );
    const t = document.querySelector("#toast");
    t.textContent = this.message;
    t.style.opacity = this.messageTime > 0 ? "1" : "0";
    const boss = w.enemies.find((e) => e.type === "boss");
    document
      .querySelector("#boss")
      .classList.toggle("hidden", !w.bossAwake || boss.dead);
    document.querySelector("#boss-fill").style.width =
      `${Math.max(0, (boss.hp / boss.maxHp) * 100)}%`;
  }
}

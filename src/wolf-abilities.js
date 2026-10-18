import * as THREE from "three";
import { CHARGE_MIN, CHARGE_FULL, WOLF_ATTACKS } from "./combat.js";
/** Wolf-specific input/state, independent from enemy AI and village activities. */
export class WolfAbilities {
  constructor(game) {
    this.game = game;
    this.charge = null;
    this.pending = null;
    this.barkCooldown = 0;
    this.voiceTime = 0;
    this.voiceDuration = 1;
    this.voiceKind = null;
    this.voiceOption = "growl";
    this.foliageDistance = 0;
    this.chargeEffect = 0;
    this.readyPlayed = false;
    this.lastMove = null;
  }
  get chargeRatio() {
    return this.charge ? Math.min(1, this.charge.time / CHARGE_FULL) : 0;
  }
  get charging() {
    return this.charge && this.charge.time >= CHARGE_MIN;
  }
  get movementMultiplier() {
    return this.charging
      ? 0.32
      : this.voiceKind === "Bark" && this.voiceTime > 0
        ? 0.18
        : 1;
  }
  cancel() {
    this.charge = null;
    this.pending = null;
    this.readyPlayed = false;
    this.chargeEffect = 0;
  }
  reset() {
    this.cancel();
    this.barkCooldown = 0;
    this.voiceTime = 0;
    this.voiceKind = null;
    this.foliageDistance = 0;
  }
  update(dt) {
    const g = this.game,
      input = g.input;
    this.barkCooldown = Math.max(0, this.barkCooldown - dt);
    this.voiceTime = Math.max(0, this.voiceTime - dt);
    if (input.consume("bark")) this.bark();
    if (input.consume("voice")) this.vocalize(this.voiceOption);
    if (input.dash || input.jump) {
      this.cancel();
      input.consume("lightDown");
      input.consume("heavyDown");
      input.consume("lightUp");
      input.consume("heavyUp");
    }
    for (const kind of ["light", "heavy"]) {
      if (input.consume(kind + "Down") && !this.charge && g.dashTime === 0) {
        this.charge = { kind, time: 0 };
        this.readyPlayed = false;
      }
    }
    if (this.charge) {
      const kind = this.charge.kind;
      this.charge.time += dt;
      if (this.charging) {
        this.chargeEffect -= dt;
        if (this.chargeEffect <= 0) {
          this.chargeEffect = 0.14;
          const weapon = g.player.weaponEndpoints?.();
          if (weapon) g.effects.spectralWeapon(weapon.tip);
          g.effects.chargeAura(
            g.player.root.position,
            this.chargeRatio,
            kind === "heavy",
          );
        }
        if (!this.readyPlayed && this.chargeRatio === 1) {
          this.readyPlayed = true;
          g.audio.play("chargeReady", { heavy: kind === "heavy" });
        }
      }
      const released = input.consume(kind + "Up");
      if (released) {
        const time = this.charge.time;
        this.charge = null;
        if (g.player.root.position.y > 0.16) {
          if (!g.aerialUsed)
            this.request(
              "aerial",
              time >= CHARGE_MIN ? this.chargeLevel(time) : 0,
            );
        } else if (time >= CHARGE_MIN)
          this.request(
            kind === "heavy" ? "chargedHeavy" : "chargedLight",
            this.chargeLevel(time),
          );
        else if (kind === "heavy") this.request("heavy");
        else input.attack = true;
      }
    }
    input.consume("lightUp");
    input.consume("heavyUp");
    if (input.consume("heavy"))
      this.request(g.player.root.position.y > 0.16 ? "aerial" : "heavy");
    if (this.pending) {
      const current = g.attackData();
      if (g.attackTime <= 0 || g.attackPhase >= current.cancel) {
        const request = this.pending;
        this.pending = null;
        g.startSpecialAttack(request.kind, request.level);
      }
    }
  }
  chargeLevel(time) {
    return THREE.MathUtils.clamp(
      (time - CHARGE_MIN) / (CHARGE_FULL - CHARGE_MIN),
      0,
      1,
    );
  }
  request(kind, level = 0) {
    const g = this.game;
    if (kind === "aerial" && g.aerialUsed) return;
    if (g.dashTime > 0) return;
    if (kind === "heavy" && g.attackTime > 0 && g.specialAttack === "heavy") {
      g.queuedHeavy = true;
      return;
    }
    // A two-hit heavy string ends after its return strike, without an accidental third hit.
    if (
      kind === "heavy" &&
      g.attackTime > 0 &&
      g.specialAttack === "heavyFinish"
    )
      return;
    this.pending = { kind, level };
  }
  bark() {
    const g = this.game;
    if (this.barkCooldown > 0) {
      g.notify(`Bark recovers in ${this.barkCooldown.toFixed(1)}s`, 1.2);
      return false;
    }
    if (g.player.root.position.y > 0.15 || g.dashTime > 0) return false;
    if (g.expansion && !g.expansion.spendEnergy(16)) return false;
    g.cancelAttack();
    this.cancel();
    this.barkCooldown = g.expansion?.profile.stats.barkCooldown ?? 6;
    this.voiceKind = "Bark";
    this.voiceTime = this.voiceDuration = 0.55;
    g.audio.play("barkStun");
    g.effects.barkWave(g.player.root.position, g.player.root.rotation.y);
    g.velocity.multiplyScalar(0.2);
    const forward = g.forward();
    let count = 0;
    for (const e of g.enemies) {
      if (e.hp <= 0) continue;
      const delta = e.mesh.position.clone().sub(g.player.root.position);
      delta.y = 0;
      const distance = delta.length();
      if (
        distance > (g.expansion?.profile.stats.barkRadius ?? 5.5) ||
        g.player.root.position.x < 15 ||
        !g.clearShot(g.player.root.position, e.mesh.position)
      )
        continue;
      if (distance > 0.01 && delta.normalize().dot(forward) < 0.05) continue;
      e.stun = Math.max(e.stun, 1.65);
      e.state = "stagger";
      e.stateDuration = e.timer = e.stun;
      e.hitPlayer = true;
      e.cooldown = Math.max(e.cooldown, 1);
      e.visual.hit(forward, 0.6);
      g.effects.stunStars(e.mesh.position);
      count++;
    }
    g.notify(
      count
        ? `Guardian bark · ${count} spirit${count === 1 ? "" : "s"} stunned`
        : "Guardian bark · 6s recovery",
      2,
    );
    return true;
  }
  vocalize(option = "growl") {
    if (this.voiceTime > 0) return false;
    const name =
      { growl: "Growl", howl: "Howl", bark: "Bark" }[option] || "Growl";
    this.voiceKind = name;
    this.voiceTime = this.voiceDuration =
      name === "Howl" ? 1.7 : name === "Growl" ? 0.9 : 0.55;
    this.game.audio.play(
      option === "bark" ? "barkSoft" : option === "howl" ? "howl" : "growl",
    );
    return true;
  }
  afterMove(dt, moved) {
    const g = this.game;
    if (
      g.speed < 4.5 ||
      g.player.root.position.y > 0.05 ||
      g.attackTime > 0 ||
      this.charge
    )
      return;
    this.foliageDistance += moved;
    while (this.foliageDistance > 0.3) {
      this.foliageDistance -= 0.3;
      const p = g.player.root.position
        .clone()
        .addScaledVector(g.forward(), -0.5);
      g.effects.foliage(p, g.forward());
    }
  }
  pose() {
    return {
      charge: this.charging
        ? { kind: this.charge.kind, ratio: this.chargeRatio }
        : null,
      voice:
        this.voiceTime > 0
          ? {
              clip: this.voiceKind,
              phase: 1 - this.voiceTime / this.voiceDuration,
            }
          : null,
    };
  }
}

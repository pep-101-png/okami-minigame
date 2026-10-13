import * as THREE from "three";
import { wolf } from "./models.js";
import { animateWolf } from "./animation.js";
import { Effects } from "./effects.js";
import { EnemyController } from "./enemy.js";
import { AudioController } from "./audio.js";
import { VillageActivities } from "./quests.js";
import { WolfAbilities } from "./wolf-abilities.js";
import {
  WOLF_ATTACKS,
  ATTACKS,
  ATTACK_BUFFER,
  COMBO_GRACE,
  attackEnvelope,
  sweepAngle,
} from "./combat.js";

const UP = new THREE.Vector3(0, 1, 0);
const angleDelta = (a, b) => Math.atan2(Math.sin(a - b), Math.cos(a - b));
const clamp = THREE.MathUtils.clamp;

export class Game {
  constructor(scene, input, world, onEnd) {
    Object.assign(this, { scene, input, world, onEnd });
    this.attacks = ATTACKS;
    this.player = wolf();
    scene.add(this.player.root);
    world.player = this.player.root;
    this.player.root.position.set(0, 0, 12);
    this.effects = new Effects(scene);
    this.audio = new AudioController();
    this.abilities = new WolfAbilities(this);
    this.specialAttack = null;
    this.currentAttack = null;
    this.aerialUsed = false;
    this.aerialLanded = false;
    this.activities = new VillageActivities(scene, (text) => this.notify(text));
    this.maxHp = 100;
    this.hp = this.maxHp;
    this.active = false;
    this.paused = false;
    this.victory = false;
    this.time = 0;
    this.hitStop = 0;
    this.velocity = new THREE.Vector3();
    this.velocityY = 0;
    this.speed = 0;
    this.turnDelta = 0;
    this.attackTime = 0;
    this.attackDuration = 1;
    this.attackPhase = 0;
    this.combo = 0;
    this.comboWindow = 0;
    this.queuedCombo = false;
    this.hitTargets = new Set();
    this.attackBuffer = 0;
    this.dodgeBuffer = 0;
    this.jumpBuffer = 0;
    this.coyote = 0.1;
    this.dashTime = 0;
    this.dashCooldown = 0;
    this.dashDirection = new THREE.Vector3(0, 0, -1);
    this.invulnerable = 0;
    this.footstepDistance = 0;
    this.landing = 0;
    this.dialogue = null;
    this.nearNpc = null;
    this.nearActivity = null;
    this.toast = { text: "Find Hana in the garden · E to talk", timer: 7 };
    this.kills = 0;
    this.combatStarted = false;
    this.enemies = [
      [-5, -5],
      [5, -5],
      [0, -9],
      [-7, 1],
      [7, 1],
    ].map(([x, z], i) => {
      const home = new THREE.Vector3(x + 26, 0, z);
      const visual = new EnemyController(scene, { index: i, home });
      const mesh = visual.root;
      mesh.position.copy(home);
      const canvas = document.createElement("canvas");
      canvas.width = 128;
      canvas.height = 16;
      const texture = new THREE.CanvasTexture(canvas);
      const bar = new THREE.Sprite(
        new THREE.SpriteMaterial({
          map: texture,
          depthTest: false,
          transparent: true,
        }),
      );
      bar.scale.set(1.15, 0.12, 1);
      bar.position.y = 2.25;
      bar.visible = false;
      mesh.add(bar);
      const e = {
        visual,
        mesh,
        home,
        hp: 5,
        maxHp: 5,
        cooldown: 0.6 + i * 0.2,
        texture,
        canvas,
        bar,
        state: "idle",
        timer: 0,
        stateDuration: 1,
        stun: 0,
        deathTime: 0,
        deathEffect: false,
        attackDirection: new THREE.Vector3(),
        knockback: new THREE.Vector3(),
        previous: home.clone(),
        hitPlayer: false,
      };
      this.drawBar(e);
      return e;
    });
  }
  notify(text, duration = 4.5) {
    this.toast = { text, timer: duration };
  }
  drawBar(e) {
    const context = e.canvas.getContext("2d");
    context.clearRect(0, 0, 128, 16);
    context.fillStyle = "#3e332a";
    context.fillRect(0, 0, 128, 16);
    context.fillStyle = e.state === "windup" ? "#edb950" : "#b74e3d";
    context.fillRect(3, 3, (122 * Math.max(0, e.hp)) / e.maxHp, 10);
    e.texture.needsUpdate = true;
  }
  collide(pos, radius = 0.43) {
    const b = this.world.bounds;
    pos.x = clamp(pos.x, b.minX + radius, b.maxX - radius);
    pos.z = clamp(pos.z, b.minZ + radius, b.maxZ - radius);
    // Two passes resolve adjacent props and building corners without tunneling.
    for (let pass = 0; pass < 2; pass++) {
      for (const box of this.world.boxes) {
        const dx = pos.x - box.x,
          dz = pos.z - box.z;
        const hx = box.halfX + radius,
          hz = box.halfZ + radius;
        if (Math.abs(dx) < hx && Math.abs(dz) < hz) {
          if (hx - Math.abs(dx) < hz - Math.abs(dz))
            pos.x = box.x + (dx >= 0 ? hx : -hx);
          else pos.z = box.z + (dz >= 0 ? hz : -hz);
        }
      }
      for (const o of this.world.obstacles) {
        const dx = pos.x - o.x,
          dz = pos.z - o.z;
        const distance = Math.hypot(dx, dz),
          min = radius + o.r;
        if (distance < min) {
          pos.x = o.x + (distance ? dx / distance : 1) * min;
          pos.z = o.z + (distance ? dz / distance : 0) * min;
        }
      }
      for (const npc of this.world.npcs) {
        const dx = pos.x - npc.root.position.x,
          dz = pos.z - npc.root.position.z;
        const distance = Math.hypot(dx, dz),
          min = radius + 0.59;
        if (distance < min) {
          pos.x = npc.root.position.x + (distance ? dx / distance : 1) * min;
          pos.z = npc.root.position.z + (distance ? dz / distance : 0) * min;
        }
      }
    }
  }
  move(pos, delta, radius = 0.43) {
    const steps = Math.max(1, Math.ceil(Math.hypot(delta.x, delta.z) / 0.22));
    for (let i = 0; i < steps; i++) {
      pos.addScaledVector(delta, 1 / steps);
      this.collide(pos, radius);
      if (pos === this.player.root.position) this.collidePlayer();
    }
  }
  collidePlayer() {
    const position = this.player.root.position;
    const forward = this.forward();
    // A lean wolf is long, so its chest and hips need contact points too.
    // Keep the spear non-solid: weapon tips should not snag on every post.
    for (let pass = 0; pass < 2; pass++) {
      for (const [offset, radius] of [
        [0.62, 0.3],
        [-0.45, 0.3],
      ]) {
        const probe = position.clone().addScaledVector(forward, offset);
        const original = probe.clone();
        this.collide(probe, radius);
        position.x += probe.x - original.x;
        position.z += probe.z - original.z;
      }
      this.collide(position);
    }
  }
  clearShot(from, to) {
    const length = Math.hypot(to.x - from.x, to.z - from.z);
    const steps = Math.max(1, Math.ceil(length / 0.22));
    for (let i = 1; i < steps; i++) {
      const x = THREE.MathUtils.lerp(from.x, to.x, i / steps);
      const z = THREE.MathUtils.lerp(from.z, to.z, i / steps);
      if (
        this.world.boxes.some(
          (box) =>
            Math.abs(x - box.x) < box.halfX && Math.abs(z - box.z) < box.halfZ,
        )
      )
        return false;
      if (
        this.world.obstacles.some(
          (o) => Math.hypot(x - o.x, z - o.z) < o.r * 0.88,
        )
      )
        return false;
    }
    return true;
  }
  forward(angle = this.player.root.rotation.y) {
    return new THREE.Vector3(0, 0, -1).applyAxisAngle(UP, angle);
  }
  attackData() {
    return this.currentAttack || ATTACKS[this.combo] || ATTACKS[1];
  }
  startSpecialAttack(kind, level = 0) {
    if (kind === "aerial" && this.aerialUsed) return false;
    this.startAttack(1);
    this.specialAttack = kind;
    this.currentAttack = { ...WOLF_ATTACKS[kind] };
    if (kind === "chargedLight")
      this.currentAttack.damage = 2 + Math.floor(level * 2);
    if (kind === "chargedHeavy")
      this.currentAttack.damage = 3 + Math.floor(level * 3);
    this.chargeLevel = level;
    this.attackDuration = this.currentAttack.duration;
    this.attackTime = this.attackDuration;
    this.attackPhase = 0.001;
    if (kind === "aerial") {
      this.aerialUsed = true;
      this.aerialLanded = false;
      this.velocityY = 0;
      this.audio.play("growl");
    }
    return true;
  }
  startAttack(nextCombo) {
    this.specialAttack = null;
    this.currentAttack = null;
    const root = this.player.root;
    this.combo =
      nextCombo ??
      (this.comboWindow > 0 && this.combo < 3 ? this.combo + 1 : 1);
    const data = ATTACKS[this.combo];
    const front = this.forward();
    const candidates = this.enemies
      .filter((e) => {
        const delta = e.mesh.position.clone().sub(root.position);
        delta.y = 0;
        return (
          e.hp > 0 &&
          delta.length() < 4.5 &&
          delta.normalize().dot(front) > 0.15 &&
          this.clearShot(root.position, e.mesh.position)
        );
      })
      .sort(
        (a, b) =>
          a.mesh.position.distanceTo(root.position) -
          b.mesh.position.distanceTo(root.position),
      );
    if (candidates[0]) {
      const d = candidates[0].mesh.position.clone().sub(root.position);
      const aim = Math.atan2(-d.x, -d.z);
      // A small assist preserves the chosen direction rather than snapping 180°.
      root.rotation.y += clamp(angleDelta(aim, root.rotation.y), -0.32, 0.32);
    }
    this.attackDuration = data.duration;
    this.attackTime = data.duration;
    this.attackPhase = 0.001;
    this.comboWindow = 0;
    this.queuedCombo = false;
    this.hitTargets.clear();
    this.didHit = false;
    this.attackBuffer = 0;
    this.swingPlayed = false;
    this.attackBurstPlayed = false;
  }
  strike(phase = this.attackData().hit) {
    if (!this.combo) return;
    const root = this.player.root,
      data = this.attackData();
    const arcAngle =
      data.sweep || (!this.specialAttack && this.combo === 2)
        ? sweepAngle(phase)
        : 0;
    const forward = this.forward(root.rotation.y + arcAngle);
    for (const e of this.enemies) {
      if (e.hp <= 0 || this.hitTargets.has(e)) continue;
      const diff = e.mesh.position.clone().sub(root.position);
      diff.y = 0;
      const distance = diff.length();
      if (distance > data.range || root.position.y > (data.height ?? 1.2))
        continue;
      if (distance > 0.01 && diff.normalize().dot(forward) < data.arc) continue;
      if (!this.clearShot(root.position, e.mesh.position)) continue;
      this.hitTargets.add(e);
      this.didHit = true;
      e.hp = Math.max(0, e.hp - data.damage);
      const knock = e.mesh.position.clone().sub(root.position);
      knock.y = 0;
      if (knock.lengthSq() < 0.001) knock.copy(forward);
      knock.normalize();
      e.knockback.copy(knock).multiplyScalar(data.knockback * 9);
      e.stun = data.stagger;
      e.state = "stagger";
      e.stateDuration = e.timer = data.stagger;
      e.cooldown = Math.max(e.cooldown, 0.6);
      e.visual.hit(
        knock,
        data.heavy || this.combo === 3 ? 1.7 : this.combo === 2 ? 1.2 : 0.8,
      );
      this.hitStop = Math.max(this.hitStop, data.hitStop);
      const impact = e.mesh.position.clone();
      this.effects.impact(impact, forward, {
        heavy: data.heavy || this.combo === 3,
      });
      this.audio.play(data.heavy || this.combo === 3 ? "heavyHit" : "hit", {
        combo: this.combo,
        heavy: data.heavy || this.combo === 3,
      });
      this.cameraImpact?.(data.heavy || this.combo === 3 ? 0.12 : 0.045);
      this.drawBar(e);
      if (e.hp === 0) {
        e.state = "dead";
        e.deathTime = 0;
        e.bar.visible = false;
        e.visual.kill();
        this.kills++;
        if (this.kills === this.enemies.length) this.victoryPending = 1.25;
      }
    }
  }
  cancelAttack() {
    this.specialAttack = null;
    this.currentAttack = null;
    this.abilities?.cancel();
    this.attackTime = 0;
    this.attackPhase = 0;
    this.attackBuffer = 0;
    this.comboWindow = 0;
    this.queuedCombo = false;
  }
  startDodge(direction) {
    const root = this.player.root;
    this.cancelAttack();
    this.dashDirection
      .copy(direction.lengthSq() ? direction : this.forward())
      .normalize();
    root.rotation.y = Math.atan2(-this.dashDirection.x, -this.dashDirection.z);
    this.dashTime = 0.28;
    this.dashCooldown = this.activities.offered ? 0.65 : 0.78;
    this.invulnerable = Math.max(this.invulnerable, 0.32);
    this.dodgeBuffer = 0;
    this.effects.dust(root.position, { count: 9 });
    this.audio.play("dodge");
  }
  interact() {
    if (this.dialogue) {
      this.dialogue.line++;
      if (this.dialogue.line >= this.dialogue.lines.length)
        this.dialogue = null;
      this.audio.play("interact");
      return;
    }
    if (
      this.nearActivity &&
      (!this.nearNpc ||
        this.nearActivity.root.position.distanceTo(this.player.root.position) <
          this.nearNpc.root.position.distanceTo(this.player.root.position))
    ) {
      this.activities.interact(this.nearActivity, this);
      return;
    }
    if (this.nearNpc) {
      this.cancelAttack();
      this.dialogue = {
        npc: this.nearNpc,
        line: 0,
        lines: this.activities.dialogueLines(this.nearNpc, this),
      };
      this.audio.play("interact");
    }
  }
  update(dt) {
    if (this.input.consume("mute")) this.audio.toggleMute();
    if (this.input.consume("pause") && this.active && !this.dialogue)
      this.paused = !this.paused;
    if (this.paused) {
      this.abilities.cancel();
      for (const action of [
        "attack",
        "heavy",
        "lightDown",
        "lightUp",
        "heavyDown",
        "heavyUp",
        "bark",
        "voice",
        "jump",
        "dash",
        "interact",
      ])
        this.input.consume(action);
      return;
    }
    this.time += dt;
    this.world.update(dt, this.time);
    this.effects.update(dt);
    this.activities.update(dt, this.time);
    this.toast.timer = Math.max(0, this.toast.timer - dt);
    for (const petal of this.world.petals?.children || []) {
      petal.position.y -= dt * 0.35;
      petal.position.x += Math.sin(this.time + petal.position.z) * dt * 0.15;
      petal.rotation.z += dt;
      if (petal.position.y < 0) petal.position.y = 7;
    }
    const root = this.player.root;
    this.nearNpc =
      this.world.npcs
        .filter((n) => n.root.position.distanceTo(root.position) < 2.4)
        .sort(
          (a, b) =>
            a.root.position.distanceTo(root.position) -
            b.root.position.distanceTo(root.position),
        )[0] || null;
    this.nearActivity = this.activities.nearby(root.position);
    if (
      this.input.consume("interact") &&
      this.active &&
      root.position.x < 15 &&
      root.position.y < 0.1 &&
      this.dashTime === 0 &&
      this.attackTime === 0
    )
      this.interact();
    // Defeated spirits complete their release even when a dialogue/overlay opens.
    for (const e of this.enemies) {
      if (e.hp > 0) continue;
      e.deathTime += dt;
      e.visual.animate(dt, { state: "dead", time: this.time, dead: true });
      if (!e.deathEffect && e.deathTime > 0.4) {
        e.deathEffect = true;
        this.effects.death(e.mesh.position);
        this.audio.play("enemyDeath");
      }
    }
    if (this.dialogue || !this.active) {
      this.abilities.cancel();
      for (const action of [
        "attack",
        "heavy",
        "lightDown",
        "lightUp",
        "heavyDown",
        "heavyUp",
        "bark",
        "voice",
        "jump",
        "dash",
      ])
        this.input.consume(action);
      this.velocity.set(0, 0, 0);
      this.speed = 0;
      animateWolf(this.player, {
        dt,
        time: this.time,
        speed: 0,
        air: false,
        attack: 0,
        grounded: true,
      });
      for (const e of this.enemies)
        if (e.hp > 0) e.visual.animate(dt, { state: "idle", time: this.time });
      this.audio.update(dt, { speed: 0, combat: false });
      return;
    }
    this.abilities.update(dt);
    if (this.hitStop > 0) {
      // Inputs survive the impact pause; a fast second click still chains.
      if (this.input.consume("attack")) this.queuedCombo = true;
      if (this.input.consume("dash")) this.dodgeBuffer = 0.18;
      this.hitStop = Math.max(0, this.hitStop - dt);
      return;
    }
    for (const name of [
      "invulnerable",
      "comboWindow",
      "dashCooldown",
      "attackBuffer",
      "dodgeBuffer",
      "jumpBuffer",
      "landing",
    ])
      this[name] = Math.max(0, this[name] - dt);
    if (this.input.consume("attack")) {
      if (root.position.y > 0.16) {
        if (!this.aerialUsed) this.startSpecialAttack("aerial");
      } else if (this.attackTime > 0) this.queuedCombo = true;
      else this.attackBuffer = ATTACK_BUFFER;
    }
    if (this.input.consume("dash")) this.dodgeBuffer = 0.18;
    if (this.input.consume("jump")) this.jumpBuffer = 0.16;
    const direction = new THREE.Vector3(
      Number(this.input.keys.has("KeyD")) - Number(this.input.keys.has("KeyA")),
      0,
      Number(this.input.keys.has("KeyS")) - Number(this.input.keys.has("KeyW")),
    );
    if (direction.lengthSq())
      direction.normalize().applyAxisAngle(UP, this.input.yaw);
    const grounded = root.position.y < 0.002 && this.velocityY <= 0;
    const data = this.attackTime > 0 ? this.attackData() : null;
    const canCancel =
      !data ||
      this.attackPhase < data.active[0] - 0.06 ||
      this.attackPhase >= data.cancel;
    if (
      this.dodgeBuffer > 0 &&
      this.dashCooldown === 0 &&
      canCancel &&
      grounded
    )
      this.startDodge(direction);
    const dashing = this.dashTime > 0;
    const previousHeading = root.rotation.y;
    if (direction.lengthSq() && !dashing && this.attackTime <= 0) {
      const aim = Math.atan2(-direction.x, -direction.z);
      root.rotation.y +=
        angleDelta(aim, root.rotation.y) *
        (1 - Math.exp(-dt * (grounded ? 12 : 6)));
    }
    this.turnDelta =
      angleDelta(root.rotation.y, previousHeading) / Math.max(dt, 0.001);
    const sprint =
      this.input.keys.has("ShiftLeft") || this.input.keys.has("ShiftRight");
    const maxSpeed = sprint ? 6.8 : 3.65;
    const desired = direction
      .clone()
      .multiplyScalar(
        maxSpeed * (data ? data.movement : this.abilities.movementMultiplier),
      );
    const response = grounded ? (desired.lengthSq() ? 10 : 15) : 3.5;
    this.velocity.lerp(desired, 1 - Math.exp(-dt * response));
    const beforeMove = root.position.clone();
    if (dashing) {
      const phase = 1 - this.dashTime / 0.28;
      const dashSpeed = 7 + Math.sin(Math.PI * phase) * 7.5;
      this.move(
        root.position,
        this.dashDirection.clone().multiplyScalar(dt * dashSpeed),
      );
      this.dashTime = Math.max(0, this.dashTime - dt);
    } else this.move(root.position, this.velocity.clone().multiplyScalar(dt));
    const moved = Math.hypot(
      root.position.x - beforeMove.x,
      root.position.z - beforeMove.z,
    );
    this.speed = dashing ? 0 : moved / Math.max(dt, 0.001);
    if (grounded) this.coyote = 0.1;
    else this.coyote = Math.max(0, this.coyote - dt);
    if (this.jumpBuffer > 0 && this.coyote > 0 && canCancel && !dashing) {
      this.cancelAttack();
      this.aerialUsed = false;
      this.aerialLanded = false;
      this.velocityY = 7.7;
      this.jumpBuffer = 0;
      this.coyote = 0;
      this.effects.dust(root.position, { count: 5 });
      this.audio.play("jump");
    }
    const wasAirborne = root.position.y > 0;
    if (
      this.specialAttack === "aerial" &&
      this.attackTime > 0 &&
      !this.aerialLanded
    ) {
      this.velocityY =
        this.attackPhase < 0.18 ? 0 : Math.min(this.velocityY, -12);
    } else this.velocityY -= 21 * dt;
    root.position.y = Math.max(0, root.position.y + this.velocityY * dt);
    if (root.position.y === 0) {
      this.velocityY = 0;
      if (wasAirborne) {
        if (this.specialAttack === "aerial" && !this.aerialLanded) {
          this.aerialLanded = true;
          this.effects.slam(root.position);
          this.audio.play("slam");
          this.strike(Math.max(0.22, Math.min(0.82, this.attackPhase)));
        }
        this.aerialUsed = false;
        this.landing = 0.16;
        this.effects.dust(root.position, { count: 6 });
        this.audio.play("land");
      }
    }
    if (
      this.attackBuffer > 0 &&
      this.attackTime <= 0 &&
      !dashing &&
      root.position.y < 0.15
    )
      this.startAttack();
    this.updateAttack(dt);
    this.collidePlayer();
    this.updateEnemies(dt);
    animateWolf(this.player, {
      dt,
      time: this.time,
      speed: this.attackTime > 0 ? 0 : this.speed,
      air: root.position.y > 0.05,
      grounded: root.position.y === 0,
      verticalVelocity: this.velocityY,
      turnDelta: this.turnDelta,
      landing: this.landing / 0.16,
      attack: this.attackTime > 0 ? Math.max(0.001, this.attackPhase) : 0,
      dash: dashing,
      combo: this.combo,
      attackClip: this.attackTime > 0 ? this.attackData().clip : null,
      ...this.abilities.pose(),
      velocity: this.velocity.clone().applyAxisAngle(UP, -root.rotation.y),
    });
    if (this.attackTime === 0 && !dashing && root.position.y === 0) {
      if (this.player.footfalls) {
        for (const position of this.player.footfalls) {
          this.audio.play("footstep", { speed: this.speed });
          if (sprint) this.effects.dust(position, { count: 2 });
        }
      } else {
        // Older character controllers can use traveled distance as a fallback.
        this.footstepDistance += moved;
        const stepLength = sprint ? 1.8 : 0.78;
        if (this.footstepDistance > stepLength) {
          this.footstepDistance %= stepLength;
          this.audio.play("footstep", { speed: this.speed });
          if (sprint) this.effects.dust(root.position, { count: 2 });
        }
      }
    }
    this.abilities.afterMove(dt, moved);
    this.audio.update(dt, {
      speed: this.speed,
      combat: root.position.x > 15 && !this.victory,
    });
    if (this.victoryPending > 0) {
      this.victoryPending = Math.max(0, this.victoryPending - dt);
      if (this.victoryPending === 0) {
        this.victory = true;
        this.audio.play("victory");
        this.end(true);
      }
    }
    if (root.position.x > 15 && !this.combatStarted) {
      this.combatStarted = true;
      this.notify(
        "Spirit grove · watch the golden windup, then dodge the charge",
        6,
      );
    }
  }
  updateAttack(dt) {
    if (this.attackTime <= 0) {
      this.attackPhase = 0;
      return;
    }
    const data = this.attackData();
    const previousPhase = this.attackPhase;
    this.attackTime = Math.max(0, this.attackTime - dt);
    this.attackPhase = 1 - this.attackTime / this.attackDuration;
    const phase = this.attackPhase;
    if (!this.swingPlayed && phase >= data.active[0] - 0.08) {
      this.swingPlayed = true;
      this.audio.play("swing", { combo: data.heavy ? 3 : this.combo });
    }
    this.move(
      this.player.root.position,
      this.forward().multiplyScalar(
        dt * data.lunge * attackEnvelope(phase, data),
      ),
    );
    if (
      this.specialAttack === "chargedHeavy" &&
      !this.attackBurstPlayed &&
      phase >= data.hit
    ) {
      this.attackBurstPlayed = true;
      this.effects.slam(this.player.root.position);
      this.audio.play("slam");
    }
    const active = phase >= data.active[0] && previousPhase <= data.active[1];
    if (active && (!data.aerial || this.player.root.position.y < 0.08)) {
      // A few arc samples also keep fast animation frames from skipping victims.
      const a = Math.max(previousPhase, data.active[0]);
      const b = Math.min(phase, data.active[1]);
      for (let i = 0; i < 3; i++)
        this.strike(THREE.MathUtils.lerp(a, b, i / 2));
      this.emitTrail(phase);
    }
    if (this.queuedCombo && phase >= data.link) {
      this.startAttack(
        this.specialAttack ? 1 : this.combo === 3 ? 1 : this.combo + 1,
      );
    } else if (this.attackTime === 0) {
      this.comboWindow =
        this.specialAttack || this.combo === 3 ? 0 : COMBO_GRACE;
      this.attackPhase = 0;
    }
  }
  emitTrail(phase) {
    const root = this.player.root;
    // If the character supplies exact weapon endpoints, prefer the rig pose.
    const endpoints = this.player.weaponEndpoints?.();
    if (endpoints) {
      this.effects.spectralWeapon(endpoints.tip);
      this.effects.trail(
        endpoints.tip,
        endpoints.heel,
        this.attackData().heavy ? 3 : this.combo,
      );
      return;
    }
    const front = this.forward(
      root.rotation.y + (this.combo === 2 ? sweepAngle(phase) : 0),
    );
    const tip = root.position.clone().addScaledVector(front, 3.3);
    tip.y += 1.07;
    const heel = root.position.clone().addScaledVector(front, 0.85);
    heel.y += 1.0;
    this.effects.trail(tip, heel, this.combo);
  }
  enemyState(e, state, duration) {
    e.state = state;
    e.timer = duration;
    e.stateDuration = duration;
    this.drawBar(e);
  }
  updateEnemies(dt) {
    const root = this.player.root;
    const attackers = this.enemies.filter(
      (e) => e.hp > 0 && ["windup", "lunge"].includes(e.state),
    ).length;
    let attackSlots = Math.max(0, 2 - attackers);
    for (let i = 0; i < this.enemies.length; i++) {
      const e = this.enemies[i];
      if (e.hp <= 0) continue;
      const oldPos = e.mesh.position.clone();
      if (e.knockback.lengthSq() > 0.001) {
        this.move(
          e.mesh.position,
          e.knockback.clone().multiplyScalar(dt),
          0.52,
        );
        e.knockback.multiplyScalar(Math.exp(-dt * 11));
      }
      e.cooldown = Math.max(0, e.cooldown - dt);
      e.stun = Math.max(0, e.stun - dt);
      const delta = root.position.clone().sub(e.mesh.position);
      delta.y = 0;
      const distance = delta.length();
      e.bar.visible = distance < 12 && root.position.x > 15;
      const inGrove = root.position.x > 15 && distance < 15 && !this.victory;
      if (!inGrove) {
        const home = e.home.clone().sub(e.mesh.position);
        home.y = 0;
        if (home.length() > 0.12) {
          const heading = Math.atan2(-home.x, -home.z);
          e.mesh.rotation.y +=
            angleDelta(heading, e.mesh.rotation.y) * (1 - Math.exp(-dt * 6));
          this.move(
            e.mesh.position,
            home.normalize().multiplyScalar(dt * 1.6),
            0.52,
          );
          e.state = "approach";
        } else e.state = "idle";
        e.cooldown = Math.max(e.cooldown, 0.6);
      } else if (e.stun > 0) {
        e.state = "stagger";
        e.timer = e.stun;
      } else {
        if (e.state === "idle" || e.state === "stagger") e.state = "approach";
        if (e.state === "approach") {
          const heading = Math.atan2(-delta.x, -delta.z);
          e.mesh.rotation.y +=
            angleDelta(heading, e.mesh.rotation.y) * (1 - Math.exp(-dt * 7));
          if (distance > 2.05) {
            // Mild lateral approach gives opponents room instead of one pile.
            const target = delta.clone().normalize();
            if (distance < 5 && i % 2)
              target.applyAxisAngle(UP, i % 3 ? 0.24 : -0.24);
            this.move(
              e.mesh.position,
              target.multiplyScalar(dt * (1.65 + i * 0.07)),
              0.52,
            );
          } else if (
            e.cooldown === 0 &&
            attackSlots > 0 &&
            root.position.y < 0.9
          ) {
            attackSlots--;
            this.enemyState(e, "windup", 0.65 + i * 0.035);
            e.attackDirection.copy(delta).normalize();
            e.hitPlayer = false;
            this.audio.play("enemyWindup");
          }
        } else {
          e.timer = Math.max(0, e.timer - dt);
          if (e.state === "windup") {
            const progress = 1 - e.timer / e.stateDuration;
            if (progress < 0.48 && distance > 0.001) {
              e.attackDirection.copy(delta).normalize();
              e.mesh.rotation.y = Math.atan2(-delta.x, -delta.z);
            }
            if (e.timer === 0) {
              this.enemyState(e, "lunge", 0.3);
              this.audio.play("enemyAttack");
            }
          } else if (e.state === "lunge") {
            const phase = 1 - e.timer / e.stateDuration;
            e.previous.copy(e.mesh.position);
            this.move(
              e.mesh.position,
              e.attackDirection
                .clone()
                .multiplyScalar(dt * (5.2 + Math.sin(phase * Math.PI) * 3)),
              0.52,
            );
            if (
              !e.hitPlayer &&
              this.sweptContact(
                e.previous,
                e.mesh.position,
                root.position,
                1.05,
              ) &&
              root.position.y < 0.75 &&
              this.invulnerable === 0
            ) {
              e.hitPlayer = true;
              this.damagePlayer(15, e.attackDirection);
            }
            if (e.timer === 0) this.enemyState(e, "recover", 0.78);
          } else if (e.state === "recover" && e.timer === 0) {
            e.state = "approach";
            e.cooldown = 0.4 + i * 0.08;
          }
        }
      }
      // Opponents are solid but slide apart; jump/dodge can pass their bodies.
      for (let j = 0; j < i; j++) {
        const other = this.enemies[j];
        if (other.hp <= 0) continue;
        const separation = e.mesh.position.clone().sub(other.mesh.position);
        separation.y = 0;
        const l = separation.length();
        if (l < 1.1 && l > 0.001)
          this.move(
            e.mesh.position,
            separation.normalize().multiplyScalar((1.1 - l) * 0.4),
            0.52,
          );
      }
      if (
        root.position.y < 0.45 &&
        this.dashTime === 0 &&
        e.state !== "lunge"
      ) {
        const separation = root.position.clone().sub(e.mesh.position);
        separation.y = 0;
        const l = separation.length();
        if (l < 0.88 && l > 0.001)
          this.move(
            root.position,
            separation.normalize().multiplyScalar((0.88 - l) * 0.75),
          );
      }
      const speed = e.mesh.position.distanceTo(oldPos) / Math.max(dt, 0.001);
      const phase = e.stateDuration
        ? clamp(1 - e.timer / e.stateDuration, 0, 1)
        : 0;
      e.visual.animate(dt, {
        state: e.state,
        phase,
        time: this.time,
        speed,
        stun: e.stun,
        dead: false,
      });
    }
  }
  sweptContact(a, b, p, radius) {
    const dx = b.x - a.x,
      dz = b.z - a.z;
    const lengthSq = dx * dx + dz * dz;
    const t = lengthSq
      ? clamp(((p.x - a.x) * dx + (p.z - a.z) * dz) / lengthSq, 0, 1)
      : 0;
    return Math.hypot(a.x + dx * t - p.x, a.z + dz * t - p.z) < radius;
  }
  damagePlayer(damage, direction) {
    this.hp = Math.max(0, this.hp - damage);
    this.invulnerable = 0.8;
    this.cancelAttack();
    this.abilities.voiceKind = "Hurt";
    this.abilities.voiceTime = this.abilities.voiceDuration = 0.45;
    this.velocity.addScaledVector(direction, 4);
    this.effects.impact(this.player.root.position, direction, { heavy: false });
    this.audio.play("playerHit");
    this.cameraImpact?.(0.1);
    this.notify("Hit · dodge the golden windup with K", 2.1);
    if (this.hp === 0) this.end(false);
  }
  reset() {
    this.hp = this.maxHp;
    this.kills = 0;
    this.victory = false;
    this.victoryPending = 0;
    this.active = true;
    this.paused = false;
    this.dialogue = null;
    this.combatStarted = false;
    this.cancelAttack();
    this.abilities.reset();
    this.aerialUsed = false;
    this.aerialLanded = false;
    this.hitStop = 0;
    this.invulnerable = 0;
    this.dashTime = 0;
    this.dashCooldown = 0;
    this.velocity.set(0, 0, 0);
    this.velocityY = 0;
    this.speed = 0;
    this.player.root.position.set(0, 0, 12);
    this.player.root.rotation.set(0, 0, 0);
    for (const e of this.enemies) {
      e.hp = e.maxHp;
      e.mesh.position.copy(e.home);
      e.mesh.rotation.set(0, 0, 0);
      e.state = "idle";
      e.cooldown = 0.8;
      e.stun = 0;
      e.knockback.set(0, 0, 0);
      e.deathTime = 0;
      e.deathEffect = false;
      e.visual.reset();
      this.drawBar(e);
    }
    this.input.clear();
    this.effects.clear();
    this.notify("A new dawn · the shrine remembers your offering");
  }
  end(win) {
    this.active = false;
    this.paused = false;
    this.input.clear();
    this.onEnd(win);
  }
}

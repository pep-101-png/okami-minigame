import * as THREE from "three";
import { wolf, demon } from "./models.js";
import { animateWolf } from "./animation.js";
import { Effects } from "./effects.js";
export class Game {
  constructor(scene, input, world, onEnd) {
    Object.assign(this, { scene, input, world, onEnd });
    this.player = wolf();
    scene.add(this.player.root);
    this.player.root.position.set(0, 0, 6);
    this.hp = 100;
    this.kills = 0;
    this.enemies = [];
    this.active = false;
    this.time = 0;
    this.velocityY = 0;
    this.velocity = new THREE.Vector3();
    this.speed = 0;
    this.attackTime = 0;
    this.combo = 0;
    this.comboWindow = 0;
    this.invulnerable = 0;
    this.dashTime = 0;
    this.dashCooldown = 0;
    this.attackBuffer = 0;
    this.jumpBuffer = 0;
    this.coyote = 0.1;
    this.effects = new Effects(scene);
    for (const [x, z] of [
      [-5, -5],
      [5, -5],
      [0, -9],
      [-7, 1],
      [7, 1],
    ]) {
      const mesh = demon();
      mesh.position.set(x, 0, z);
      scene.add(mesh);
      const canvas = document.createElement("canvas");
      canvas.width = 128;
      canvas.height = 16;
      const texture = new THREE.CanvasTexture(canvas),
        bar = new THREE.Sprite(
          new THREE.SpriteMaterial({ map: texture, depthTest: false }),
        );
      bar.scale.set(1.1, 0.1, 1);
      bar.position.y = 2.2;
      mesh.add(bar);
      const e = {
        mesh,
        hp: 5,
        maxHp: 5,
        cooldown: 1,
        texture,
        canvas,
        bar,
        state: "approach",
        timer: 0,
        stun: 0,
        attackDirection: new THREE.Vector3(),
      };
      this.enemies.push(e);
      this.drawBar(e);
    }
  }
  drawBar(e) {
    const c = e.canvas.getContext("2d");
    c.clearRect(0, 0, 128, 16);
    c.fillStyle = "#413d2a";
    c.fillRect(0, 0, 128, 16);
    c.fillStyle = "#c74532";
    c.fillRect(2, 2, (124 * Math.max(0, e.hp)) / e.maxHp, 12);
    e.texture.needsUpdate = true;
  }
  collide(pos, r = 0.5) {
    const len = Math.hypot(pos.x, pos.z);
    if (len > 11.3) {
      pos.x *= 11.3 / len;
      pos.z *= 11.3 / len;
    }
    for (const o of this.world.obstacles) {
      const dx = pos.x - o.x,
        dz = pos.z - o.z,
        d = Math.hypot(dx, dz),
        min = r + o.r;
      if (d < min) {
        pos.x = o.x + (d ? dx / d : 1) * min;
        pos.z = o.z + (d ? dz / d : 0) * min;
      }
    }
  }
  startAttack() {
    this.combo = this.comboWindow > 0 ? (this.combo % 3) + 1 : 1;
    this.attackDuration = [0, 0.3, 0.32, 0.43][this.combo];
    this.attackTime = this.attackDuration;
    this.comboWindow = 0.8;
    this.didHit = false;
    this.attackBuffer = 0;
  }
  strike() {
    const root = this.player.root,
      forward = new THREE.Vector3(0, 0, -1).applyAxisAngle(
        new THREE.Vector3(0, 1, 0),
        root.rotation.y,
      );
    for (const e of this.enemies) {
      if (e.hp <= 0) continue;
      const diff = e.mesh.position.clone().sub(root.position);
      diff.y = 0;
      if (
        diff.length() < 3.5 &&
        diff.normalize().dot(forward) > 0.5 &&
        root.position.y < 1.6
      ) {
        e.hp = Math.max(0, e.hp - (this.combo === 3 ? 3 : 1));
        e.mesh.position.addScaledVector(forward, this.combo === 3 ? 1.4 : 0.45);
        e.stun = 0.35;
        e.state = "approach";
        e.cooldown = 0.8;
        this.effects.burst(e.mesh.position, 16);
        this.drawBar(e);
        if (e.hp === 0) {
          e.mesh.visible = false;
          this.kills++;
          this.effects.burst(e.mesh.position, 20, "#e7b743");
          if (this.kills === this.enemies.length) this.end(true);
        }
      }
    }
  }
  update(dt) {
    this.time += dt;
    this.effects.update(dt);
    for (const p of this.world.petals.children) {
      p.position.y -= dt * 0.35;
      p.position.x += Math.sin(this.time + p.position.z) * dt * 0.15;
      p.rotation.z += dt;
      if (p.position.y < 0) p.position.y = 7;
    }
    if (!this.active) {
      animateWolf(this.player, {
        dt,
        time: this.time,
        speed: 0,
        air: false,
        attack: 0,
      });
      return;
    }
    const root = this.player.root;
    for (const key of [
      "invulnerable",
      "comboWindow",
      "dashCooldown",
      "attackBuffer",
      "jumpBuffer",
    ])
      this[key] = Math.max(0, this[key] - dt);
    if (this.input.consume("attack")) this.attackBuffer = 0.25;
    if (this.input.consume("jump")) this.jumpBuffer = 0.15;
    let x =
        Number(this.input.keys.has("KeyD")) -
        Number(this.input.keys.has("KeyA")),
      z =
        Number(this.input.keys.has("KeyS")) -
        Number(this.input.keys.has("KeyW"));
    const direction = new THREE.Vector3(x, 0, z);
    if (direction.lengthSq())
      direction
        .normalize()
        .applyAxisAngle(new THREE.Vector3(0, 1, 0), this.input.yaw);
    if (this.input.consume("dash") && this.dashCooldown === 0) {
      this.dashTime = 0.22;
      this.dashCooldown = 0.8;
      this.invulnerable = 0.28;
      this.effects.burst(root.position, 8, "#e0cf91");
    }
    const dashing = this.dashTime > 0;
    this.dashTime = Math.max(0, this.dashTime - dt);
    if (direction.lengthSq() && !dashing) {
      const angle = Math.atan2(-direction.x, -direction.z);
      root.rotation.y +=
        Math.atan2(
          Math.sin(angle - root.rotation.y),
          Math.cos(angle - root.rotation.y),
        ) *
        (1 - Math.exp(-dt * 22));
    }
    const maxSpeed = this.input.keys.has("ShiftLeft") ? 8 : 5.7;
    const desired = direction.multiplyScalar(
      this.attackTime > 0 ? maxSpeed * 0.65 : maxSpeed,
    );
    this.velocity.lerp(
      desired,
      1 - Math.exp(-dt * (desired.lengthSq() ? 20 : 25)),
    );
    if (dashing) {
      const f = new THREE.Vector3(0, 0, -1).applyAxisAngle(
        new THREE.Vector3(0, 1, 0),
        root.rotation.y,
      );
      root.position.addScaledVector(f, dt * 13);
    } else root.position.addScaledVector(this.velocity, dt);
    this.speed = this.velocity.length();
    if (root.position.y <= 0.001) this.coyote = 0.1;
    else this.coyote = Math.max(0, this.coyote - dt);
    if (this.jumpBuffer > 0 && this.coyote > 0) {
      this.velocityY = 7.8;
      this.jumpBuffer = 0;
      this.coyote = 0;
      this.effects.burst(root.position, 5, "#ddd0a1");
    }
    this.velocityY -= 22 * dt;
    root.position.y = Math.max(0, root.position.y + this.velocityY * dt);
    if (root.position.y === 0) this.velocityY = 0;
    if (this.attackBuffer > 0 && this.attackTime <= 0) this.startAttack();
    let phase = 0;
    if (this.attackTime > 0) {
      this.attackTime = Math.max(0, this.attackTime - dt);
      phase = 1 - this.attackTime / this.attackDuration;
      if (phase > 0.24 && phase < 0.65) {
        const f = new THREE.Vector3(0, 0, -1).applyAxisAngle(
          new THREE.Vector3(0, 1, 0),
          root.rotation.y,
        );
        root.position.addScaledVector(f, dt * (this.combo === 3 ? 5 : 2.5));
      }
      if (phase > 0.33 && !this.didHit) {
        this.didHit = true;
        this.strike();
      }
    }
    this.collide(root.position);
    animateWolf(this.player, {
      dt,
      time: this.time,
      speed: this.speed,
      air: root.position.y > 0.05,
      attack: this.attackTime > 0 ? phase : 0,
      dash: dashing,
    });
    for (let i = 0; i < this.enemies.length; i++) {
      const e = this.enemies[i];
      if (e.hp <= 0) continue;
      e.cooldown = Math.max(0, e.cooldown - dt);
      e.stun = Math.max(0, e.stun - dt);
      if (e.stun > 0) continue;
      const delta = root.position.clone().sub(e.mesh.position);
      delta.y = 0;
      const distance = delta.length();
      if (e.state === "approach") {
        e.mesh.rotation.y = Math.atan2(-delta.x, -delta.z);
        if (distance > 2) {
          e.mesh.position.addScaledVector(
            delta.normalize(),
            dt * (1.4 + i * 0.08),
          );
        } else if (e.cooldown === 0) {
          e.state = "windup";
          e.timer = 0.6;
          e.attackDirection.copy(delta.normalize());
        }
      } else {
        e.timer -= dt;
        if (e.state === "windup") {
          e.mesh.scale.set(1.05, 1 + Math.sin(e.timer * 20) * 0.045, 1.05);
          if (e.timer <= 0) {
            e.state = "lunge";
            e.timer = 0.24;
          }
        } else if (e.state === "lunge") {
          e.mesh.position.addScaledVector(e.attackDirection, dt * 7);
          if (
            e.mesh.position.distanceTo(root.position) < 1.25 &&
            root.position.y < 0.75 &&
            this.invulnerable === 0
          ) {
            this.hp = Math.max(0, this.hp - 15);
            this.invulnerable = 0.8;
            this.effects.burst(root.position, 10);
            if (this.hp === 0) this.end(false);
          }
          if (e.timer <= 0) {
            e.state = "recover";
            e.timer = 0.7;
          }
        } else if (e.timer <= 0) {
          e.state = "approach";
          e.cooldown = 0.6;
          e.mesh.scale.setScalar(1);
        }
      }
      e.bar.material.color.set(e.state === "windup" ? "#ff6b37" : "#ffffff");
      e.mesh.position.y = Math.sin(this.time * 5 + i) * 0.025;
      for (let j = 0; j < i; j++) {
        const o = this.enemies[j];
        if (o.hp <= 0) continue;
        const d = e.mesh.position.clone().sub(o.mesh.position);
        d.y = 0;
        const length = d.length();
        if (length < 1.15 && length > 0.001)
          e.mesh.position.addScaledVector(d.normalize(), dt * 2);
      }
      this.collide(e.mesh.position, 0.55);
      // Solid bodies resolve penetration but allow aerial evasion.
      if (root.position.y < 0.5) {
        const away = root.position.clone().sub(e.mesh.position);
        away.y = 0;
        const l = away.length();
        if (l < 0.8 && l > 0.001) {
          root.position.addScaledVector(away.normalize(), (0.8 - l) * 0.5);
          this.collide(root.position);
        }
      }
    }
    this.player.body.visible =
      this.invulnerable <= 0 || Math.floor(this.time * 20) % 2 === 0;
  }
  end(win) {
    this.active = false;
    document.exitPointerLock?.();
    this.onEnd(win);
  }
}

import { groundAt } from "./world.js";
import { damp, clamp } from "./math.js";
export function hitEnemy(e, damage, dir, g, brush = false) {
  if (e.dead) return;
  if ((e.type === "armour" || e.type === "boss") && e.exposed <= 0 && !brush) {
    g.effect(e.x, e.y - 50, "shield", 6);
    g.say("Ink-cut the glowing seal to break its guard.", 2);
    return;
  }
  e.hp -= damage;
  e.hurt = 0.28;
  e.vx = dir * (e.type === "boss" ? 80 : 210);
  e.state = "stagger";
  e.timer = 0.36;
  g.hitstop = 0.055;
  g.audio.play("hit");
  g.effect(e.x, e.y - 45, "hit", 12);
  if (e.hp <= 0) {
    e.dead = true;
    e.death = 0;
    g.effect(e.x, e.y - 35, "spirit", 26);
    g.player.pearls += e.type === "boss" ? 10 : 2;
    if (e.type === "boss") {
      g.world.bossDefeated = true;
      g.world.trees[2].restored = true;
      g.world.restored = true;
      g.world.restoration = 0;
      g.audio.play("win");
      g.say("The seal breaks. Follow the petals to the dawn shrine.", 5);
      g.effect(e.x, e.y - 80, "bloom", 70);
    } else g.audio.play("bloom");
  }
}
export function updateEnemies(g, dt) {
  const w = g.world,
    p = g.player;
  for (const e of w.enemies) {
    e.age += dt;
    e.hurt = Math.max(0, e.hurt - dt);
    e.exposed = Math.max(0, e.exposed - dt);
    if (e.dead) {
      e.death += dt;
      continue;
    }
    if (e.type === "boss" && !w.bossAwake) {
      if (p.x > 5040) {
        w.bossAwake = true;
        e.state = "intro";
        e.timer = 2.5;
        g.say("Kurobane · Keeper of the Broken River", 3.2);
        g.audio.play("heavy");
      } else continue;
    }
    const dx = p.x - e.x,
      dy = p.y - e.y,
      near = Math.abs(dx) < (e.type === "boss" ? 800 : 580);
    if (!near) {
      e.x += Math.sin(e.age) * dt * 15;
      continue;
    }
    if (!["tell", "attack"].includes(e.state)) e.facing = dx > 0 ? 1 : -1;
    e.timer -= dt;
    if (e.state === "stagger") {
      e.x += e.vx * dt;
      e.vx = damp(e.vx, 0, 8, dt);
      if (e.timer <= 0) {
        e.state = "recover";
        e.timer = 0.35;
      }
      continue;
    }
    if (e.state === "intro") {
      if (e.timer <= 0) {
        e.state = "recover";
        e.timer = 0.4;
      }
      continue;
    }
    if (e.type === "boss") {
      e.phase = e.hp <= 20 ? 2 : 1;
      if (e.state === "patrol" || e.state === "recover") {
        if (e.timer <= 0) {
          e.move = (e.move || 0) + 1;
          e.state = "tell";
          e.timer = e.phase === 2 ? 0.6 : 0.95;
          e.pattern = e.move % 3;
          g.audio.play("enemy");
        }
      } else if (e.state === "tell" && e.timer <= 0) {
        e.state = "attack";
        e.timer = e.pattern === 0 ? 0.7 : 0.45;
        if (e.pattern === 1) {
          for (let i = -1; i <= 1; i++)
            w.projectiles.push({
              x: e.x,
              y: e.y - 80,
              vx: e.facing * (180 + i * 40),
              vy: -210 - i * 45,
              life: 4,
              kind: "curse",
            });
          g.effect(e.x, e.y, "shock", 22);
        }
        if (e.pattern === 2) {
          e.vy = -500;
          e.jump = true;
        }
        g.audio.play("heavy");
      } else if (e.state === "attack") {
        if (e.pattern === 0) e.x += e.facing * (e.phase === 2 ? 520 : 390) * dt;
        if (e.jump) {
          e.vy += 1300 * dt;
          e.y += e.vy * dt;
          if (e.y >= 580) {
            e.y = 580;
            e.jump = false;
            for (const dir of [-1, 1])
              w.projectiles.push({
                x: e.x,
                y: 562,
                vx: dir * 340,
                vy: 0,
                life: 2,
                kind: "wave",
              });
            g.effect(e.x, 580, "shock", 30);
            g.audio.play("land");
          }
        }
        if (Math.abs(dx) < 100 && Math.abs(dy) < 100) p.damage(2, e.facing, g);
        if (e.timer <= 0 && !e.jump) {
          e.state = "recover";
          e.timer = e.phase === 2 ? 0.55 : 1.1;
          e.exposed = Math.max(e.exposed, 1.2);
        }
      }
      e.x = Math.max(5120, Math.min(5830, e.x));
      continue;
    }
    if (e.type === "moth") {
      e.y = 375 + Math.sin(e.age * 2.2) * 45;
      if (e.state === "patrol") {
        e.x += e.facing * 65 * dt;
        if (e.timer <= 0) {
          e.state = "tell";
          e.timer = 0.65;
        }
      } else if (e.state === "tell" && e.timer <= 0) {
        e.state = "attack";
        e.timer = 0.8;
        e.targetY = p.y - 45;
      } else if (e.state === "attack") {
        e.x += e.facing * 250 * dt;
        e.y = damp(e.y, e.targetY, 9, dt);
        if (Math.abs(dx) < 45 && Math.abs(p.y - 45 - e.y) < 50)
          p.damage(1, e.facing, g);
        if (e.timer <= 0) {
          e.state = "recover";
          e.timer = 1.1;
        }
      } else if (e.timer <= 0) {
        e.state = "patrol";
        e.timer = 1.2;
      }
      continue;
    }
    if (e.type === "archer") {
      e.x = clamp(e.x, e.home - 85, e.home + 85);
      if (e.state === "patrol" || e.state === "recover") {
        if (Math.abs(dx) < 170) e.x -= e.facing * 60 * dt;
        if (e.timer <= 0) {
          e.state = "tell";
          e.timer = 0.8;
          e.aim = { x: p.x, y: p.y - 35 };
        }
      } else if (e.state === "tell" && e.timer <= 0) {
        const target = e.aim || { x: p.x, y: p.y - 35 },
          shotY = target.y - (e.y - 40),
          shotX = target.x - e.x,
          shotLength = Math.hypot(shotX, shotY) || 1;
        w.projectiles.push({
          x: e.x,
          y: e.y - 40,
          vx: (shotX / shotLength) * 285,
          vy: (shotY / shotLength) * 285,
          life: 3,
          kind: "arrow",
        });
        e.state = "recover";
        e.timer = 1.5;
        g.audio.play("enemy");
      }
      continue;
    }
    const range = e.type === "brute" ? 160 : 100;
    if (e.state === "recover" && e.timer <= 0) e.state = "patrol";
    if (e.state === "patrol" || e.state === "recover") {
      if (e.state === "patrol" && Math.abs(dx) > range * 0.75)
        e.x += e.facing * (e.type === "brute" ? 65 : 95) * dt;
      if (Math.abs(dx) < range && e.timer <= 0) {
        e.state = "tell";
        e.timer = e.type === "brute" ? 1 : 0.65;
        g.audio.play("enemy");
      }
    } else if (e.state === "tell" && e.timer <= 0) {
      e.state = "attack";
      e.timer = 0.38;
    } else if (e.state === "attack") {
      e.x += e.facing * (e.type === "brute" ? 180 : 230) * dt;
      if (Math.abs(dx) < (e.type === "brute" ? 100 : 65) && Math.abs(dy) < 100)
        p.damage(e.type === "brute" ? 2 : 1, e.facing, g);
      if (e.timer <= 0) {
        e.state = "recover";
        e.timer = 0.9;
      }
    }
    e.y = groundAt(w, e.x);
  }
  for (const pr of w.projectiles) {
    pr.x += pr.vx * dt;
    pr.y += pr.vy * dt;
    if (pr.kind === "curse") pr.vy += 210 * dt;
    pr.life -= dt;
    if (pr.reflected) {
      for (const e of w.enemies)
        if (!e.dead && Math.hypot(pr.x - e.x, pr.y - (e.y - 40)) < 45) {
          hitEnemy(e, 2, Math.sign(pr.vx), g, true);
          pr.life = 0;
        }
    }
    if (!pr.reflected && Math.hypot(pr.x - p.x, pr.y - (p.y - 35)) < 35) {
      p.damage(1, Math.sign(pr.vx), g);
      pr.life = 0;
    }
  }
  w.projectiles = w.projectiles.filter((p) => p.life > 0);
}

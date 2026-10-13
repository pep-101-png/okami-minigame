import { chromium } from "playwright";
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { resolve } from "node:path";
import { existsSync } from "node:fs";
const out = resolve(
  process.env.SMOKE_OUT_DIR || ".test-artifacts",
  `wolf-${new Date().toISOString().replace(/[:.]/g, "-")}`,
);
await mkdir(out, { recursive: true });
const report = { started: new Date().toISOString(), checks: [], errors: [] };
const browser = await chromium.launch({
  executablePath:
    process.env.CHROMIUM_PATH ||
    (existsSync("/usr/bin/chromium") ? "/usr/bin/chromium" : undefined),
  args: [
    "--no-sandbox",
    "--use-angle=swiftshader",
    "--enable-unsafe-swiftshader",
  ],
});
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
page.on("pageerror", (e) => report.errors.push(e.message));
page.on("console", (m) => {
  if (m.type() === "error") report.errors.push(m.text());
});
await page.addInitScript(() => {
  const raf = requestAnimationFrame;
  window.__wolfQA = { pause: false };
  window.requestAnimationFrame = (cb) =>
    raf(function tick(t) {
      if (__wolfQA.pause) return raf(tick);
      cb(t);
    });
});
await page.goto(process.env.SMOKE_BASE_URL || "http://127.0.0.1:4173");
await page.waitForFunction(() => window.__game);
await page.click("#start");
await page.evaluate(() => (__wolfQA.pause = true));
const step = (seconds) =>
  page.evaluate((seconds) => {
    for (let t = 0; t < seconds; t += 1 / 60) __game.update(1 / 60);
  }, seconds);
const reset = () =>
  page.evaluate(() => {
    const g = __game;
    g.reset();
    g.enemies.forEach((e) => {
      e.stun = 100;
      e.mesh.position.copy(e.home);
    });
    g.player.root.position.set(0, 0, 12);
  });
const mouse = async (button) => {
  await page.mouse.move(650, 420);
  await page.mouse.down({ button });
};
async function check(name, fn) {
  try {
    const details = await fn();
    report.checks.push({ name, pass: true, details });
    console.log("PASS", name);
  } catch (e) {
    report.checks.push({ name, pass: false, error: e.stack });
    console.log("FAIL", name, e.message);
  }
}
try {
  await check(
    "two visible layered eye meshes are attached outside the head surface",
    async () => {
      const d = await page.evaluate(() => {
        const p = __game.player;
        return p.eyes.map((eye) => {
          eye.updateWorldMatrix(true, true);
          return {
            name: eye.name,
            visible: eye.visible,
            children: eye.children.length,
            scale: eye.scale.toArray(),
            world: eye.getWorldPosition(eye.position.clone()).toArray(),
          };
        });
      });
      assert.equal(d.length, 2);
      assert(
        d.every(
          (e) => e.visible && e.children >= 4 && e.scale.every(Number.isFinite),
        ),
      );
      assert(Math.abs(d[0].world[0] - d[1].world[0]) > 0.15);
      return d;
    },
  );
  await check(
    "quick physical left click retains the normal combo",
    async () => {
      await reset();
      await mouse("left");
      await step(0.05);
      await page.mouse.up({ button: "left" });
      await step(0.04);
      const d = await page.evaluate(() => ({
        combo: __game.combo,
        kind: __game.specialAttack,
        time: __game.attackTime,
      }));
      assert(d.combo === 1 && d.kind === null && d.time > 0);
      return d;
    },
  );
  await check(
    "left hold is a charge and release selects charged thrust",
    async () => {
      await reset();
      await mouse("left");
      await step(0.6);
      let d = await page.evaluate(() => ({
        charging: !!__game.abilities.charging,
        ratio: __game.abilities.chargeRatio,
        state: __game.player.state,
        attack: __game.attackTime,
      }));
      assert(
        d.charging &&
          d.ratio > 0.4 &&
          d.attack === 0 &&
          d.state === "ChargeLight",
      );
      await page.mouse.up({ button: "left" });
      await step(0.04);
      const release = await page.evaluate(() => ({
        kind: __game.specialAttack,
        clip: __game.player.state,
        damage: __game.attackData().damage,
      }));
      assert.equal(release.kind, "chargedLight");
      assert.equal(release.clip, "ChargedThrust");
      return { d, release };
    },
  );
  await check(
    "full light charge scales damage and hit window drives a real hit",
    async () => {
      await reset();
      await page.evaluate(() => {
        const g = __game;
        g.player.root.position.set(26, 0, 0);
        g.player.root.rotation.y = 0;
        g.enemies.forEach((e) => e.mesh.position.set(42, 0, 20));
        g.enemies[0].mesh.position.set(26, 0, -3);
      });
      await mouse("left");
      await step(1.2);
      await page.mouse.up({ button: "left" });
      await step(0.44);
      const d = await page.evaluate(() => ({
        kind: __game.specialAttack,
        damage: __game.attackData().damage,
        hp: __game.enemies[0].hp,
        hit: __game.didHit,
      }));
      assert(d.damage === 4 && d.hp === 1 && d.hit);
      return d;
    },
  );
  await check("physical right click is a distinct heavy attack", async () => {
    await reset();
    await mouse("right");
    await step(0.04);
    await page.mouse.up({ button: "right" });
    await step(0.04);
    const d = await page.evaluate(() => ({
      kind: __game.specialAttack,
      state: __game.player.state,
      data: __game.attackData(),
    }));
    assert.equal(d.kind, "heavy");
    assert.equal(d.state, "HeavyArc");
    assert(d.data.heavy);
    return d;
  });
  await check(
    "full right hold releases charged heavy with stronger damage and radial geometry",
    async () => {
      await reset();
      await mouse("right");
      await step(1.2);
      const hold = await page.evaluate(() => ({
        state: __game.player.state,
        ratio: __game.abilities.chargeRatio,
      }));
      assert.equal(hold.state, "ChargeHeavy");
      assert.equal(hold.ratio, 1);
      await page.mouse.up({ button: "right" });
      await step(0.05);
      const d = await page.evaluate(() => ({
        kind: __game.specialAttack,
        state: __game.player.state,
        damage: __game.attackData().damage,
        radial: __game.attackData().radial,
      }));
      assert.equal(d.kind, "chargedHeavy");
      assert.equal(d.state, "ChargedHeavy");
      assert(d.damage === 6 && d.radial);
      return d;
    },
  );
  await check(
    "charged heavy hits forward and rear targets through its real active window",
    async () => {
      await reset();
      await page.evaluate(() => {
        const g = __game;
        g.player.root.position.set(26, 0, 0);
        g.player.root.rotation.y = 0;
        g.enemies.forEach((e) => e.mesh.position.set(42, 0, 20));
        g.enemies[0].mesh.position.set(26, 0, -2.5);
        g.enemies[1].mesh.position.set(26, 0, 2.5);
      });
      await mouse("right");
      await step(1.2);
      await page.mouse.up({ button: "right" });
      await step(0.76);
      const d = await page.evaluate(() => ({
        front: __game.enemies[0].hp,
        rear: __game.enemies[1].hp,
        hits: __game.hitTargets.size,
      }));
      assert(d.front === 0 && d.rear === 0 && d.hits === 2);
      return d;
    },
  );
  await check(
    "charging while moving blends real leg motion with the upper-body windup",
    async () => {
      await reset();
      await page.keyboard.down("KeyW");
      await mouse("left");
      await step(0.4);
      const before = await page.evaluate(() => {
        const b = __game.player.body.getObjectByName("b_LeftForeArm_010");
        return {
          state: __game.player.state,
          z: __game.player.root.position.z,
          q: b.quaternion.toArray(),
        };
      });
      await step(0.25);
      const after = await page.evaluate(() => {
        const b = __game.player.body.getObjectByName("b_LeftForeArm_010");
        return {
          state: __game.player.state,
          z: __game.player.root.position.z,
          q: b.quaternion.toArray(),
        };
      });
      assert(
        before.state === "ChargeLight" &&
          after.state === "ChargeLight" &&
          after.z < before.z,
      );
      assert(before.q.some((v, i) => Math.abs(v - after.q[i]) > 0.02));
      await page.keyboard.up("KeyW");
      await page.keyboard.press("KeyK");
      await page.mouse.up({ button: "left" });
      return { before, after };
    },
  );
  await check(
    "charge cancels on dodge and late mouse release cannot fire an attack",
    async () => {
      await reset();
      await mouse("left");
      await step(0.5);
      await page.keyboard.press("KeyK");
      await step(0.04);
      assert(
        await page.evaluate(
          () => !__game.abilities.charge && __game.dashTime > 0,
        ),
      );
      await page.mouse.up({ button: "left" });
      await step(0.4);
      assert(await page.evaluate(() => __game.attackTime === 0));
    },
  );
  await check(
    "bark stuns visible forward enemies without damage, respects cover/backward direction and cooldown",
    async () => {
      await reset();
      await page.evaluate(() => {
        const g = __game;
        g.player.root.position.set(26, 0, 0);
        g.player.root.rotation.y = 0;
        g.enemies.forEach((e, i) => {
          e.stun = 0;
          e.cooldown = 100;
          e.mesh.position.set(42, 0, 20);
        });
        g.enemies[0].mesh.position.set(26, 0, -3);
        g.enemies[1].mesh.position.set(26, 0, 3);
      });
      await page.keyboard.press("KeyB");
      await step(0.02);
      const d = await page.evaluate(() => ({
        front: __game.enemies[0].stun,
        back: __game.enemies[1].stun,
        hp: __game.enemies[0].hp,
        cooldown: __game.abilities.barkCooldown,
        waves: __game.effects.items.length,
      }));
      assert(
        d.front > 1.5 &&
          d.back === 0 &&
          d.hp === 5 &&
          d.cooldown > 5.9 &&
          d.cooldown <= 6 &&
          d.waves > 0,
      );
      await page.keyboard.press("KeyB");
      await step(0.03);
      assert(await page.evaluate(() => __game.abilities.barkCooldown < 6));
      return d;
    },
  );
  await check("bark does not stun through solid cover", async () => {
    await reset();
    await page.evaluate(() => {
      const g = __game;
      g.player.root.position.set(26, 0, 0);
      g.player.root.rotation.y = 0;
      g.enemies.forEach((e) => {
        e.stun = 0;
        e.cooldown = 100;
        e.mesh.position.set(42, 0, 20);
      });
      g.enemies[0].mesh.position.set(26, 0, -3);
      g.world.boxes.push({
        x: 26,
        z: -1.5,
        halfX: 0.45,
        halfZ: 0.25,
        qa: true,
      });
    });
    await page.keyboard.press("KeyB");
    await step(0.03);
    const stun = await page.evaluate(() => {
      const g = __game;
      const stun = g.enemies[0].stun;
      g.world.boxes = g.world.boxes.filter((b) => !b.qa);
      return stun;
    });
    assert.equal(stun, 0);
    return { stun };
  });
  await check(
    "three vocal options and damage whimper synthesize nonempty audio",
    async () => {
      await reset();
      const d = await page.evaluate(() => {
        const g = __game,
          sounds = [];
        const buffers = [],
          create = g.audio.context.createBuffer.bind(g.audio.context);
        g.audio.context.createBuffer = (...args) => {
          const buffer = create(...args);
          buffers.push(buffer);
          return buffer;
        };
        for (const name of ["barkSoft", "growl", "howl", "whimper"]) {
          g.audio.lastSound.delete(name);
          const before = g.audio.voices;
          const accepted = g.audio.play(name);
          sounds.push({ name, accepted, added: g.audio.voices - before });
        }
        g.abilities.voiceTime = 0;
        g.abilities.voiceOption = "howl";
        g.input.voice = true;
        g.update(0.01);
        g.damagePlayer(1, g.forward());
        g.audio.context.createBuffer = create;
        const waves = buffers.map((buffer) => {
          let peak = 0,
            sum = 0,
            finite = true;
          for (const v of buffer.getChannelData(0)) {
            peak = Math.max(peak, Math.abs(v));
            sum += v * v;
            finite &&= Number.isFinite(v);
          }
          return {
            seconds: buffer.duration,
            peak,
            rms: Math.sqrt(sum / buffer.length),
            finite,
          };
        });
        return {
          waves,
          sounds,
          voice: g.abilities.voiceKind,
          voices: g.audio.voices,
          hp: g.hp,
        };
      });
      assert(d.sounds.every((s) => s.accepted && s.added > 0));
      assert(
        d.waves.length >= 4 &&
          d.waves.every((w) => w.finite && w.rms > 0.01 && w.peak < 1),
      );
      assert.equal(d.voice, "Hurt");
      assert.equal(d.hp, 99);
      return d;
    },
  );
  await check(
    "running flowers/leaves emit locally, remain bounded and expire",
    async () => {
      await reset();
      await page.keyboard.down("KeyW");
      await page.keyboard.down("ShiftLeft");
      await step(1);
      await page.keyboard.up("KeyW");
      await page.keyboard.up("ShiftLeft");
      const d = await page.evaluate(() => ({
        count: __game.effects.items.length,
        flowers: __game.effects.items.filter(
          (p) => p.mesh.material.map === __game.effects.flowerMap,
        ).length,
        leaves: __game.effects.items.filter(
          (p) => p.mesh.material.map === __game.effects.leafMap,
        ).length,
        limit: __game.effects.limit,
      }));
      assert(d.flowers > 0 && d.leaves > 0 && d.count <= d.limit);
      await step(3);
      assert(await page.evaluate(() => __game.effects.items.length < 8));
      return d;
    },
  );
  await check(
    "jump has distinct rise/fall poses and a landing, not a frozen airborne loop",
    async () => {
      await reset();
      await page.keyboard.press("Space");
      await step(0.14);
      const rise = await page.evaluate(() => ({
        state: __game.player.state,
        y: __game.player.root.position.y,
        v: __game.velocityY,
      }));
      assert.equal(rise.state, "JumpRise");
      await step(0.3);
      const fall = await page.evaluate(() => ({
        state: __game.player.state,
        y: __game.player.root.position.y,
        v: __game.velocityY,
      }));
      assert.equal(fall.state, "JumpFall");
      await step(0.32);
      const land = await page.evaluate(() => ({
        state: __game.player.state,
        y: __game.player.root.position.y,
      }));
      assert(land.y === 0 && ["Land", "Idle"].includes(land.state));
      return { rise, fall, land };
    },
  );
  await check(
    "clicking during a jump triggers one aerial dive and impact recovery",
    async () => {
      await reset();
      await page.keyboard.press("Space");
      await step(0.17);
      await mouse("left");
      await step(0.03);
      await page.mouse.up({ button: "left" });
      await step(0.03);
      const d = await page.evaluate(() => ({
        kind: __game.specialAttack,
        used: __game.aerialUsed,
        state: __game.player.state,
        v: __game.velocityY,
      }));
      assert.equal(d.kind, "aerial");
      assert.equal(d.state, "AirStrike");
      assert(d.used && d.v < 0);
      await step(0.4);
      const landed = await page.evaluate(() => ({
        y: __game.player.root.position.y,
        landed: __game.aerialLanded,
      }));
      assert(landed.y === 0 && landed.landed);
      return { d, landed };
    },
  );
  await check(
    "silk fur ribbons animate through local time uniforms with bounded geometry",
    async () => {
      const d = await page.evaluate(() => ({
        count: __game.player.fur.ribbons.length,
        finite: __game.player.fur.ribbons.every((r) =>
          [...r.geometry.attributes.position.array].every(Number.isFinite),
        ),
      }));
      assert(d.count >= 4 && d.finite);
      return d;
    },
  );
  await check(
    "all new authored action clips contain real finite animation tracks",
    async () => {
      const names = [
        "ChargedThrust",
        "HeavyArc",
        "ChargedHeavy",
        "AirStrike",
        "ChargeLight",
        "ChargeHeavy",
        "JumpRise",
        "JumpFall",
        "Bark",
        "Growl",
        "Howl",
        "Hurt",
      ];
      const d = await page.evaluate(
        (names) =>
          names.map((name) => {
            const c = __game.player.actions[name]?.getClip();
            return {
              name,
              duration: c?.duration,
              tracks: c?.tracks.length,
              finite: c?.tracks.every((t) =>
                [...t.values].every(Number.isFinite),
              ),
            };
          }),
        names,
      );
      assert(d.every((c) => c.duration > 0.1 && c.tracks > 10 && c.finite));
      return d;
    },
  );
  await reset();
  await page.evaluate(() => {
    __wolfQA.pause = false;
    __game.player.root.position.set(0, 0, 12);
  });
  await page.waitForTimeout(800);
  await page.screenshot({ path: resolve(out, "wolf-village.png") });
  await page.evaluate(() => (__wolfQA.pause = true));
  await check("no browser JavaScript/shader failures", () => {
    assert.deepEqual(report.errors, []);
  });
} finally {
  report.finished = new Date().toISOString();
  report.passed = report.checks.filter((c) => c.pass).length;
  report.failed = report.checks.filter((c) => !c.pass).length;
  await writeFile(resolve(out, "report.json"), JSON.stringify(report, null, 2));
  await browser.close();
  console.log(`${report.passed} passed; ${report.failed} failed. ${out}`);
  process.exitCode = report.failed ? 1 : 0;
}

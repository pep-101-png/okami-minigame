import { chromium } from "playwright";
import assert from "node:assert/strict";
import { writeFile, mkdir } from "node:fs/promises";
import { recognise } from "../src/brush.js";
const results = [],
  errors = [],
  base = process.env.GAME_URL || "http://127.0.0.1:5180";
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || "/usr/bin/chromium",
  headless: true,
  args: ["--no-sandbox"],
});
const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
page.on("pageerror", (e) => errors.push(e.message));
page.on("console", (m) => {
  if (m.type() === "error") errors.push(m.text());
});
async function test(name, fn) {
  try {
    await fn();
    results.push({ name, status: "passed" });
    console.log("PASS", name);
  } catch (e) {
    results.push({ name, status: "failed", reason: e.message });
    console.log("FAIL", name, e.message);
  }
}
const ev = (fn) => page.evaluate(fn);
async function fresh() {
  await page.goto(base);
  await page.locator("#play").click();
  await page.waitForTimeout(100);
}
async function fixture(x, y = 575) {
  await page.evaluate(
    ({ x, y }) => {
      const g = inkbound.game;
      Object.assign(g.player, { x, y, vx: 0, vy: 0, grounded: true });
      g.renderer.camera.x = Math.max(0, x - 420);
      g.renderer.camera.y = y - 540;
      g.renderer.camera.zoom = 1;
    },
    { x, y },
  );
  await page.waitForTimeout(60);
}
async function draw(points) {
  const ps = await page.evaluate(
    (ps) => ps.map((p) => inkbound.renderer.worldToScreen(p)),
    points,
  );
  await page.mouse.move(ps[0].x, ps[0].y);
  await page.mouse.down();
  for (const p of ps.slice(1)) await page.mouse.move(p.x, p.y);
  await page.mouse.up();
  await page.waitForTimeout(70);
}
const circle = (x, y, rx = 112, ry = 100) =>
  Array.from({ length: 57 }, (_, i) => ({
    x: x + Math.cos((i / 56) * 6.283185) * rx,
    y: y + Math.sin((i / 56) * 6.283185) * ry,
  }));
const line = (x, y, x2, y2) =>
  Array.from({ length: 25 }, (_, i) => ({
    x: x + ((x2 - x) * i) / 24,
    y: y + ((y2 - y) * i) / 24,
  }));
const spiral = (x, y) =>
  Array.from({ length: 100 }, (_, i) => {
    const t = i / 99,
      r = 65 * (1 - t);
    return {
      x: x + Math.cos(t * Math.PI * 5) * r,
      y: y + Math.sin(t * Math.PI * 5) * r,
    };
  });
await test("Drawn gesture recognition: line, oval, zigzag, spiral and curved water", async () => {
  assert.equal(recognise(line(100, 100, 450, 130)).kind, "slash");
  assert.equal(recognise(circle(200, 200, 100, 70)).kind, "bloom");
  assert.equal(
    recognise(
      Array.from({ length: 45 }, (_, i) => ({
        x: 100 + i * 8,
        y: 200 + Math.sin(i * 0.4) * 36,
      })),
    ).kind,
    "wind",
  );
  assert.equal(recognise(spiral(200, 200)).kind, "bomb");
  assert.equal(
    recognise(
      Array.from({ length: 40 }, (_, i) => ({
        x: 100 + i * 2,
        y: 100 + i * 5 + Math.sin((i / 39) * Math.PI) * 120,
      })),
    ).kind,
    "water",
  );
});
await test("Keyboard acceleration, sprint and turning", async () => {
  await fresh();
  const x = await ev(() => inkbound.game.player.x);
  await page.keyboard.down("KeyD");
  await page.waitForTimeout(130);
  const v = await ev(() => inkbound.game.player.vx);
  await page.keyboard.down("ShiftLeft");
  await page.waitForTimeout(400);
  const p = await ev(() => ({
    x: inkbound.game.player.x,
    v: inkbound.game.player.vx,
  }));
  assert(v > 40 && v < 285);
  assert(p.v > 350 && p.x > x + 100);
  await page.keyboard.up("KeyD");
  await page.keyboard.up("ShiftLeft");
  await page.keyboard.down("KeyA");
  await page.waitForTimeout(110);
  assert.equal(await ev(() => inkbound.game.player.facing), -1);
  await page.keyboard.up("KeyA");
});
await test("Jump rises and lands; double jump stays locked initially", async () => {
  await fresh();
  await page.keyboard.down("Space");
  await page.waitForTimeout(160);
  const p = await ev(() => ({
    y: inkbound.game.player.y,
    v: inkbound.game.player.vy,
  }));
  assert(p.y < 510 && p.v < 0);
  await page.keyboard.up("Space");
  await page.keyboard.press("Space");
  assert.equal(await ev(() => inkbound.game.player.jumps), 1);
  await page.waitForTimeout(700);
  assert.equal(await ev(() => inkbound.game.player.grounded), true);
  assert.equal(await ev(() => inkbound.game.player.y), 575);
});
await test("Riverbank step-up preserves ground collision while walking across connected terrain", async () => {
  await fresh();
  await fixture(1930, 620);
  await page.keyboard.down("KeyD");
  await page.waitForTimeout(450);
  await page.keyboard.up("KeyD");
  assert((await ev(() => inkbound.game.player.x)) > 1990);
  assert.equal(await ev(() => inkbound.game.player.y), 575);
  assert(await ev(() => inkbound.game.player.grounded));
});
await test("Buffered three-hit light combo defeats a reacting spirit", async () => {
  await fresh();
  await fixture(750);
  await ev(() => {
    Object.assign(inkbound.game.world.enemies[0], {
      x: 835,
      y: 575,
      hp: 4,
      maxHp: 4,
      state: "recover",
      timer: 2,
    });
  });
  await page.keyboard.press("KeyJ");
  await page.waitForTimeout(185);
  await page.keyboard.press("KeyJ");
  await page.waitForTimeout(385);
  await page.keyboard.press("KeyJ");
  await page.waitForTimeout(740);
  assert.equal(await ev(() => inkbound.game.player.combo), 3);
  assert(await ev(() => inkbound.game.world.enemies[0].dead));
});
await test("Melee resumes pursuit after recovery; ledge archer aims at grounded wolf", async () => {
  await fresh();
  await fixture(2400, 575);
  await ev(() => {
    const w = inkbound.game.world;
    Object.assign(w.enemies[3], {
      x: 2720,
      y: 575,
      state: "recover",
      timer: 0.01,
    });
    Object.assign(w.enemies[2], { state: "recover", timer: 0.01 });
  });
  await page.waitForTimeout(350);
  assert((await ev(() => inkbound.game.world.enemies[3].x)) < 2710);
  await page.waitForTimeout(750);
  assert(
    await ev(() =>
      inkbound.game.world.projectiles.some(
        (p) => p.kind === "arrow" && p.vy > 50,
      ),
    ),
  );
});
await test("Dodge immunity and damage recovery prevent repeated contact damage", async () => {
  await fresh();
  await page.keyboard.press("KeyK");
  await page.waitForTimeout(50);
  assert.equal(
    await ev(() => {
      const g = inkbound.game;
      g.player.damage(1, -1, g);
      return g.player.hp;
    }),
    8,
  );
  await page.waitForTimeout(330);
  const p = await ev(() => {
    const g = inkbound.game;
    g.player.damage(1, -1, g);
    g.player.damage(1, -1, g);
    return { hp: g.player.hp, hurt: g.player.hurt, v: g.player.vx };
  });
  assert.equal(p.hp, 7);
  assert(p.hurt > 0 && p.v < 0);
});
await test("Brush freezes simulation; mouse Bloom restores willow and unlocks abilities", async () => {
  await fresh();
  await fixture(1770, 620);
  await page.keyboard.press("KeyB");
  const t = await ev(() => inkbound.game.time);
  await page.waitForTimeout(200);
  assert.equal(await ev(() => inkbound.game.time), t);
  await draw(circle(1900, 430, 130, 115));
  assert(await ev(() => inkbound.game.world.trees[0].restored));
  assert(await ev(() => inkbound.game.player.doubleJump));
  assert.equal(await ev(() => inkbound.game.player.unlocked), 2);
  assert((await ev(() => inkbound.game.player.ink)) < 100);
  await page.screenshot({ path: "review/willow-brush.png" });
});
await test("Water stroke fills basin, opens gate, and unlocked double jump works", async () => {
  await draw(line(1780, 613, 2170, 535));
  assert(await ev(() => inkbound.game.world.basin.filled));
  assert(await ev(() => inkbound.game.world.gate.open));
  await page.keyboard.press("KeyB");
  await fixture(2200);
  await page.keyboard.press("Digit2");
  assert.equal(await ev(() => inkbound.game.player.weapon), 1);
  await page.keyboard.down("Space");
  await page.waitForTimeout(160);
  await page.keyboard.up("Space");
  await page.keyboard.press("Space");
  assert.equal(await ev(() => inkbound.game.player.jumps), 2);
});
await test("Mouse Wind gust rings chime and reflects incoming projectiles", async () => {
  await fresh();
  await fixture(1400);
  await ev(() => {
    inkbound.game.world.projectiles.push({
      x: 1450,
      y: 400,
      vx: -200,
      vy: 0,
      life: 3,
      kind: "arrow",
    });
  });
  await page.keyboard.press("KeyB");
  await draw(
    Array.from({ length: 48 }, (_, i) => ({
      x: 1340 + i * 6,
      y: 465 + Math.sin(i * 0.5) * 25,
    })),
  );
  assert(await ev(() => inkbound.game.world.lantern.lit));
  assert(
    await ev(() =>
      inkbound.game.world.projectiles.some((p) => p.reflected && p.vx > 0),
    ),
  );
  assert.equal(await ev(() => inkbound.game.player.pearls), 3);
});
await test("Armour blocks melee; ink-cut exposes seal for heavy damage", async () => {
  await fresh();
  await fixture(3480, 560);
  assert.equal(
    await ev(() => {
      const g = inkbound.game;
      g.player.startAttack("heavy", g);
      g.resolveAttack(g.player.attack);
      g.player.attack = null;
      return g.world.enemies.find((e) => e.type === "armour").hp;
    }),
    5,
  );
  await page.keyboard.press("KeyB");
  await draw(line(3470, 520, 3620, 520));
  assert(
    (await ev(
      () =>
        inkbound.game.world.enemies.find((e) => e.type === "armour").exposed,
    )) > 0,
  );
  await page.keyboard.press("KeyB");
  await page.keyboard.press("KeyL");
  await page.waitForTimeout(400);
  assert(
    (await ev(
      () => inkbound.game.world.enemies.find((e) => e.type === "armour").hp,
    )) <= 1,
  );
});
await test("Grove Bloom requires cleared spirits, then changes world and unlocks blade", async () => {
  await fresh();
  await fixture(3850, 560);
  await page.keyboard.press("KeyB");
  await draw(circle(3910, 370, 130, 125));
  assert.equal(await ev(() => inkbound.game.world.restored), false);
  await ev(() => {
    for (const e of inkbound.game.world.enemies)
      if (e.x > 3300 && e.x < 4900) {
        e.dead = true;
        e.death = 2;
      }
  });
  await draw(circle(3910, 370, 130, 125));
  assert(await ev(() => inkbound.game.world.restored));
  assert.equal(await ev(() => inkbound.game.player.unlocked), 3);
  await page.keyboard.press("KeyB");
  await page.waitForTimeout(700);
  await page.screenshot({ path: "review/restored-grove.png" });
});
await test("Actual spiral summons timed bomb and breaks ancient wall", async () => {
  await fresh();
  await fixture(4630, 560);
  await page.keyboard.press("KeyB");
  await draw(spiral(4730, 505));
  assert.equal(await ev(() => inkbound.game.world.bombs.length), 1);
  await page.keyboard.press("KeyB");
  await page.waitForTimeout(1300);
  assert(await ev(() => inkbound.game.world.wall.broken));
});
await test("Boss introduction, brush seal break and lower-health phase change", async () => {
  await fresh();
  await fixture(5090, 580);
  await page.waitForTimeout(200);
  assert(await ev(() => inkbound.game.world.bossAwake));
  await page.keyboard.press("KeyB");
  await draw(line(5370, 490, 5610, 490));
  assert(
    (await ev(
      () => inkbound.game.world.enemies.find((e) => e.type === "boss").exposed,
    )) > 0,
  );
  await page.keyboard.press("KeyB");
  await page.waitForTimeout(2700);
  assert(
    ["tell", "attack", "recover"].includes(
      await ev(
        () => inkbound.game.world.enemies.find((e) => e.type === "boss").state,
      ),
    ),
  );
  await ev(() => {
    const e = inkbound.game.world.enemies.find((e) => e.type === "boss");
    e.hp = 20;
    e.state = "recover";
    e.timer = 0.01;
  });
  await page.waitForTimeout(100);
  assert.equal(
    await ev(
      () => inkbound.game.world.enemies.find((e) => e.type === "boss").phase,
    ),
    2,
  );
});
await test("Boss defeat opens chapter ending; reaching shrine wins; retry resets", async () => {
  await fresh();
  await fixture(5490, 580);
  await page.keyboard.press("KeyB");
  await ev(() => {
    inkbound.game.world.enemies.find((e) => e.type === "boss").hp = 1;
  });
  await draw(line(5370, 490, 5610, 490));
  assert(await ev(() => inkbound.game.world.bossDefeated));
  await page.keyboard.press("KeyB");
  await fixture(6340, 580);
  await page.keyboard.down("KeyD");
  await page.waitForTimeout(250);
  await page.keyboard.up("KeyD");
  assert.equal(await ev(() => inkbound.game.state), "won");
  await page.locator("#play").click();
  assert.equal(await ev(() => inkbound.game.world.bossDefeated), false);
});
await test("Virtual standard gamepad maps jump and analogue brush drawing", async () => {
  await fresh();
  await ev(() => {
    window.testPad = {
      axes: [0, 0, 0, 0],
      buttons: Array.from({ length: 16 }, () => ({ pressed: false })),
    };
    navigator.getGamepads = () => [window.testPad];
    testPad.buttons[0].pressed = true;
  });
  await page.waitForTimeout(130);
  assert((await ev(() => inkbound.game.player.y)) < 575);
  await ev(() => {
    testPad.buttons[0].pressed = false;
    testPad.buttons[5].pressed = true;
  });
  await page.waitForTimeout(100);
  assert(await ev(() => inkbound.game.brush.active));
  await ev(() => {
    testPad.buttons[5].pressed = false;
    testPad.buttons[7].pressed = true;
    testPad.axes[2] = 0.8;
  });
  await page.waitForTimeout(300);
  assert((await ev(() => inkbound.game.brush.points.length)) > 5);
  await ev(() => {
    testPad.buttons[7].pressed = false;
    testPad.axes[2] = 0;
  });
  await page.waitForTimeout(70);
  assert((await ev(() => inkbound.game.brush.history.length)) > 0);
});
await test("Pause freezes physics; local audio runs; browser has no runtime errors", async () => {
  await fresh();
  await page.keyboard.press("Escape");
  const t = await ev(() => inkbound.game.time);
  await page.waitForTimeout(100);
  assert.equal(await ev(() => inkbound.game.time), t);
  assert.equal(await ev(() => inkbound.game.audio.ctx.state), "running");
  await page.locator("#play").click();
  assert.equal(await ev(() => inkbound.game.state), "playing");
  assert.deepEqual(errors, []);
});
await mkdir("review", { recursive: true });
await writeFile(
  "review/validation.json",
  JSON.stringify(
    {
      date: new Date().toISOString(),
      target: base,
      results,
      errors,
      note: "Real keyboard/mouse integration checks with isolated position/enemy fixtures. Not a no-assistance full playthrough.",
    },
    null,
    2,
  ),
);
await browser.close();
if (results.some((r) => r.status === "failed")) process.exitCode = 1;

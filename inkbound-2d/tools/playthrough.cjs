const { chromium } = require("playwright");
const fs = require("fs");
(async () => {
  const b = await chromium.launch({
    executablePath: "/usr/bin/chromium",
    headless: true,
    args: ["--no-sandbox"],
  });
  const page = await b.newPage({ viewport: { width: 1280, height: 720 } });
  await page.goto(process.env.GAME_URL || "http://127.0.0.1:5180");
  await page.locator("#play").click();
  const ev = (f) => page.evaluate(f);
  const events = [];
  async function log(msg) {
    const p = await ev(() => ({
      x: Math.round(inkbound.game.player.x),
      hp: inkbound.game.player.hp,
      ink: Math.round(inkbound.game.player.ink),
      state: inkbound.game.state,
    }));
    events.push({ msg, ...p });
    console.log(msg, p);
    if (p.state === "defeat") throw Error("Player defeated");
  }
  async function go(target, sprint = true) {
    const start = Date.now();
    for (let i = 0; i < 140; i++) {
      const p = await ev(() => ({
        x: inkbound.game.player.x,
        hp: inkbound.game.player.hp,
        state: inkbound.game.state,
      }));
      if (p.state === "won") break;
      if (p.hp === 0) throw Error("Died while moving");
      if (Math.abs(p.x - target) < 24) break;
      await page.keyboard.up(p.x < target ? "KeyA" : "KeyD");
      await page.keyboard.down(p.x < target ? "KeyD" : "KeyA");
      if (sprint) await page.keyboard.down("ShiftLeft");
      if (Math.abs(p.x - target) < 200) await page.keyboard.down("ControlLeft");
      else await page.keyboard.up("ControlLeft");
      await page.waitForTimeout(65);
      if (Date.now() - start > 12000)
        throw Error("Movement blocked at " + p.x + " target " + target);
    }
    await page.keyboard.up("KeyA");
    await page.keyboard.up("KeyD");
    await page.keyboard.up("ShiftLeft");
    await page.keyboard.up("ControlLeft");
    await page.waitForTimeout(230);
  }
  async function toggleBrush() {
    const active = await ev(() => inkbound.game.brush.active);
    await page.keyboard.press("KeyB");
    await page.waitForFunction(
      (previous) => inkbound.game.brush.active !== previous,
      active,
    );
  }
  async function draw(points) {
    const ps = await page.evaluate(
      (ps) => ps.map((p) => inkbound.renderer.worldToScreen(p)),
      points,
    );
    if (ps.some((p) => p.x < 0 || p.x > 1280 || p.y < 0 || p.y > 720))
      throw Error("Gesture target outside camera");
    await page.mouse.move(ps[0].x, ps[0].y);
    await page.mouse.down();
    for (const p of ps.slice(1)) await page.mouse.move(p.x, p.y);
    await page.mouse.up();
    await page.waitForTimeout(80);
  }
  const circle = (x, y) =>
    Array.from({ length: 60 }, (_, i) => ({
      x: x + Math.cos((i / 59) * 6.283185) * 125,
      y: y + Math.sin((i / 59) * 6.283185) * 118,
    }));
  const line = (x, y, x2, y2) =>
    Array.from({ length: 30 }, (_, i) => ({
      x: x + ((x2 - x) * i) / 29,
      y: y + ((y2 - y) * i) / 29,
    }));
  async function cutEnemy(index) {
    await toggleBrush();
    const e = await page.evaluate((i) => inkbound.game.world.enemies[i], index);
    await draw(
      line(
        e.x - 100,
        e.y - (e.type === "boss" ? 90 : 40),
        e.x + 100,
        e.y - (e.type === "boss" ? 90 : 40),
      ),
    );
    await toggleBrush();
  }
  async function heavyFight(index) {
    for (let i = 0; i < 14; i++) {
      let e = await page.evaluate((i) => inkbound.game.world.enemies[i], index);
      if (e.dead) return;
      if (e.type === "armour" && e.exposed < 1) await cutEnemy(index);
      await go(e.x - 100, false);
      await page.keyboard.down("KeyD");
      await page.waitForTimeout(35);
      await page.keyboard.up("KeyD");
      await page.keyboard.press("KeyL");
      await page.waitForTimeout(650);
      if (e.state === "tell") {
        await page.keyboard.press("KeyK");
        await page.waitForTimeout(200);
      }
    }
    throw Error("Could not defeat " + index);
  }
  await go(1750);
  await log("Reached river alive");
  await toggleBrush();
  await draw(circle(1900, 430));
  await draw(line(1780, 613, 2170, 535));
  await toggleBrush();
  await log("Willow restored and river gate opened");
  if (!(await ev(() => inkbound.game.world.gate.open)))
    throw Error("Gate stayed locked");
  await go(3400);
  await heavyFight(4);
  await log("Armoured spirit defeated");
  await heavyFight(5);
  await log("Grove imp defeated");
  await go(3980);
  await cutEnemy(6);
  await cutEnemy(6);
  await log("Flying spirit defeated");
  await go(4330);
  await heavyFight(7);
  await log("Brute defeated");
  await go(3900);
  await toggleBrush();
  await draw(circle(3910, 370));
  await toggleBrush();
  await log("Grove restored");
  if (!(await ev(() => inkbound.game.world.restored)))
    throw Error("Restoration failed");
  await page.keyboard.press("Digit3");
  await go(4630);
  await page.keyboard.press("KeyL");
  await page.waitForTimeout(850);
  await go(5100);
  await log("Boss awakened");
  await page.waitForTimeout(2500);
  for (let i = 0; i < 28; i++) {
    let e = await ev(() =>
      inkbound.game.world.enemies.find((e) => e.type === "boss"),
    );
    if (e.dead) break;
    let p = await ev(() => ({
      x: inkbound.game.player.x,
      ink: inkbound.game.player.ink,
    }));
    await go(e.x + (p.x < e.x ? -135 : 135), false);
    e = await ev(() =>
      inkbound.game.world.enemies.find((e) => e.type === "boss"),
    );
    p = await ev(() => ({
      x: inkbound.game.player.x,
      ink: inkbound.game.player.ink,
    }));
    if (Math.abs(e.x - p.x) > 195) {
      await page.keyboard.press("Space");
      await page.keyboard.press("KeyK");
      await page.waitForTimeout(260);
      continue;
    }
    const face = e.x > p.x ? "KeyD" : "KeyA";
    await page.keyboard.down(face);
    await page.waitForTimeout(35);
    await page.keyboard.up(face);
    if (p.ink > 27) {
      await cutEnemy(8);
      await cutEnemy(8);
    } else if (e.exposed < 0.9) await cutEnemy(8);
    e = await ev(() =>
      inkbound.game.world.enemies.find((e) => e.type === "boss"),
    );
    if (e.dead) break;
    await page.keyboard.press("KeyL");
    await page.waitForTimeout(450);
    await page.keyboard.press("KeyK");
    await page.waitForTimeout(330);
    await log(
      "Boss exchange " +
        i +
        " · HP " +
        (await ev(
          () => inkbound.game.world.enemies.find((e) => e.type === "boss").hp,
        )),
    );
  }
  if (!(await ev(() => inkbound.game.world.bossDefeated)))
    throw Error("Boss remained alive");
  await go(6440);
  await log("Chapter finished");
  if (!(await ev(() => inkbound.game.state === "won")))
    throw Error("No victory");
  fs.writeFileSync(
    "review/playthrough.json",
    JSON.stringify(
      {
        date: new Date().toISOString(),
        events,
        method:
          "Real keyboard/mouse playthrough from start to victory. No game-state edits, teleporting, health changes, or enemy fixtures.",
      },
      null,
      2,
    ),
  );
  await page.screenshot({ path: "review/victory.png" });
  await b.close();
})().catch((e) => {
  console.error(e);
  process.exit(1);
});

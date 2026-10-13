import { chromium } from "playwright";
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
const out = process.env.FOUNDATION_OUT_DIR || ".test-artifacts/foundation";
await mkdir(out, { recursive: true });
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || "/usr/bin/chromium",
  args: [
    "--no-sandbox",
    "--use-angle=swiftshader",
    "--enable-unsafe-swiftshader",
  ],
});
const page = await browser.newPage({ viewport: { width: 1200, height: 850 } });
const errors = [],
  requests = [],
  checks = [];
page.on("pageerror", (e) => errors.push(e.message));
page.on("console", (m) => {
  if (m.type() === "error") errors.push(m.text());
});
page.on("request", (r) => requests.push(r.url()));
async function check(name, fn) {
  try {
    const details = await fn();
    checks.push({ name, passed: true, details });
    console.log("PASS", name);
  } catch (e) {
    checks.push({ name, passed: false, error: e.message });
    console.log("FAIL", name, e.message);
  }
}
try {
  await page.goto(process.env.FOUNDATION_URL || "http://127.0.0.1:4173");
  await page.waitForFunction(() => window.review?.advance);
  await page.evaluate(() => (review.paused = true));
  await check(
    "standalone viewer has a new anatomical mesh and 27-bone shoulder/mane rig",
    async () => {
      const d = await page.evaluate(() => {
        let skin;
        review.model.body.traverse((o) => {
          if (o.isSkinnedMesh && o.name.includes("PaintedWolf")) skin = o;
        });
        return {
          vertices: skin.geometry.attributes.position.count,
          bones: skin.skeleton.bones.length,
          shoulder: !!review.model.body.getObjectByName("b_LeftScapula"),
          mane: !!review.model.body.getObjectByName("b_ManeFlow"),
        };
      });
      assert(d.vertices > 3000 && d.bones === 27 && d.shoulder && d.mane);
      return d;
    },
  );
  await check(
    "idle, walk, trot and run drive distinct changing finite bone poses",
    async () => {
      const rows = await page.evaluate(() => {
        const rows = [];
        for (const mode of ["idle", "walk", "trot", "run"]) {
          review.mode = mode;
          if(mode === "idle") {review.model.previousAir=false;review.model.landing=0;review.model.root.position.y=0;}
          const samples = [];
          for (let i = 0; i < 30; i++) {
            review.advance(1 / 30);
            if (i % 5 === 0)
              samples.push(
                review.model.body
                  .getObjectByName("b_LeftForeArm_010")
                  .quaternion.toArray(),
              );
          }
          rows.push({
            mode,
            state: review.model.state,
            samples,
            finite: review.model.body.position.toArray().every(Number.isFinite),
          });
        }
        return rows;
      });
      assert.deepEqual(
        rows.map((r) => r.state),
        ["Idle", "Walk", "Trot", "Run"],
      );
      assert(
        rows.every((r) => r.finite && r.samples.flat().every(Number.isFinite)),
      );
      assert(
        rows
          .slice(1)
          .every((r) =>
            r.samples.some((q) =>
              q.some((v, k) => Math.abs(v - r.samples[0][k]) > 0.02),
            ),
          ),
      );
      return rows;
    },
  );
  await check(
    "jump traverses rise, fall, landing and idle with finite grounded recovery",
    async () => {
      const d = await page.evaluate(() => {
        review.mode = "jump";
        review.jumpTime = 0;
        const states = new Set();
        let highest = 0;
        for (let i = 0; i < 80; i++) {
          review.advance(1 / 60);
          states.add(review.model.state);
          highest = Math.max(highest, review.model.root.position.y);
        }
        return {
          states: [...states],
          highest,
          y: review.model.root.position.y,
        };
      });
      assert(
        ["JumpRise", "JumpFall", "Land", "Idle"].every((s) =>
          d.states.includes(s),
        ),
      );
      assert(d.highest > 1 && d.y === 0);
      return d;
    },
  );
  await check(
    "animation buttons, weapon visibility and orbit controls are usable",
    async () => {
      await page.click('[data-mode="walk"]');
      assert.equal(
        await page.getAttribute('[data-mode="walk"]', "aria-pressed"),
        "true",
      );
      await page.check("#weapon");
      assert(await page.evaluate(() => review.model.spear.visible));
      await page.uncheck("#weapon");
      assert(!(await page.evaluate(() => review.model.spear.visible)));
      const before = await page.evaluate(() =>
        review.camera.position.toArray(),
      );
      await page.mouse.move(900, 600);
      await page.mouse.down();
      await page.mouse.move(750, 540, { steps: 8 });
      await page.mouse.up();
      await page.waitForTimeout(150);
      const after = await page.evaluate(() => review.camera.position.toArray());
      assert(after.some((v, i) => Math.abs(v - before[i]) > 0.1));
    },
  );
  await check(
    "viewer loads no town, enemy, quest, input or game modules and has no shader/JS errors",
    () => {
      assert.deepEqual(
        requests.filter((u) => /\/(town|enemy|quests|game|input)\.js/.test(u)),
        [],
      );
      assert.deepEqual(errors, []);
    },
  );
} finally {
  await writeFile(
    `${out}/report.json`,
    JSON.stringify(
      { time: new Date().toISOString(), checks, errors, requests },
      null,
      2,
    ),
  );
  await browser.close();
  process.exitCode = checks.some((c) => !c.passed) ? 1 : 0;
}

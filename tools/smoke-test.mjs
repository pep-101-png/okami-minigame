/**
 * Browser integration checks against an already running Vite server.
 * npm run build && npm run preview -- --port 4173
 * PLAYWRIGHT_MODULE=/path/to/playwright/index.mjs node tools/smoke-test.mjs
 * Chromium software WebGL keeps this usable on a cloud machine without a GPU.
 * Test artifacts use an ignored local directory. No game state is saved.
 */
import assert from "node:assert/strict";
import { access, mkdir, writeFile } from "node:fs/promises";
import { constants } from "node:fs";
import { resolve } from "node:path";
import { pathToFileURL } from "node:url";

const began = new Date();
const baseURL = process.env.SMOKE_BASE_URL || "http://127.0.0.1:4173";
const output = resolve(process.env.SMOKE_OUT_DIR || ".test-artifacts", `${began.toISOString().replace(/[:.]/g, "-")}-${process.pid}`);
await mkdir(output, { recursive: true });
const report = { startedUTC: began.toISOString(), baseURL, output, checks: [], browserErrors: [], failedRequests: [], responsesWithErrors: [], externalRequests: [], screenshots: [] };
const playwright = process.env.PLAYWRIGHT_MODULE
  ? await import(pathToFileURL(resolve(process.env.PLAYWRIGHT_MODULE)).href)
  : await import("playwright");
let chromiumPath = process.env.CHROMIUM_PATH;
if (!chromiumPath) {
  try { await access("/usr/bin/chromium", constants.X_OK); chromiumPath = "/usr/bin/chromium"; } catch { /* Use Playwright's installed browser on other machines. */ }
}
const browser = await playwright.chromium.launch({
  ...(chromiumPath ? { executablePath: chromiumPath } : {}),
  args: ["--no-sandbox", "--use-angle=swiftshader", "--enable-unsafe-swiftshader"],
});
const context = await browser.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1 });
// Only the harness controls this pause. App code and normal keyboard listeners
// remain untouched; fixed simulation steps make combat timings reproducible.
await context.addInitScript(() => {
  window.__smoke = { paused: false, frames: 0, frameIntervals: [], lastFrame: null };
  const nativeRAF = window.requestAnimationFrame.bind(window);
  window.requestAnimationFrame = (callback) => nativeRAF(function frame(now) {
    if (window.__smoke.paused) return nativeRAF(frame);
    if (window.__smoke.lastFrame !== null) {
      window.__smoke.frameIntervals.push(now - window.__smoke.lastFrame);
      if (window.__smoke.frameIntervals.length > 120) window.__smoke.frameIntervals.shift();
    }
    window.__smoke.lastFrame = now;
    window.__smoke.frames++;
    callback(now);
  });
});
const page = await context.newPage();
page.setDefaultTimeout(15000);
page.on("pageerror", error => report.browserErrors.push(error.message));
page.on("console", message => { if (message.type() === "error") report.browserErrors.push(`${message.text()} (${message.location().url || "console"})`); });
page.on("requestfailed", request => report.failedRequests.push({ url: request.url(), error: request.failure()?.errorText }));
page.on("request", request => {
  const url = new URL(request.url());
  if (["http:", "https:"].includes(url.protocol) && url.origin !== new URL(baseURL).origin)
    report.externalRequests.push(request.url());
});
page.on("response", response => {
  if (response.status() >= 400) report.responsesWithErrors.push({ url: response.url(), status: response.status() });
});

async function check(name, callback) {
  const start = Date.now();
  try {
    const detail = await callback();
    report.checks.push({ name, pass: true, milliseconds: Date.now() - start, detail });
    process.stdout.write(`PASS ${name}\n`);
  } catch (error) {
    report.checks.push({ name, pass: false, milliseconds: Date.now() - start, error: error.stack || String(error) });
    process.stdout.write(`FAIL ${name}: ${error.message}\n`);
  } finally {
    await page.evaluate(() => {
      const input = window.__game?.input;
      if (input) {
        input.keys.clear();
        for (const key of ["attack", "jump", "dash", "interact", "pause", "mute"]) input[key] = false;
      }
    }).catch(() => {});
  }
}
async function frameReady() {
  await page.evaluate(() => { window.__smoke.paused = false; window.__smoke.lastFrame = null; window.__smoke.target = window.__smoke.frames + 2; });
  await page.waitForFunction(() => window.__smoke.frames >= window.__smoke.target);
}
async function fresh() {
  await page.goto(baseURL, { waitUntil: "domcontentloaded" });
  await page.waitForFunction(() => window.__game && document.querySelector("#start"));
  await page.locator("#start").click();
  await page.waitForFunction(() => window.__game.active);
  await page.evaluate(() => {
    window.__smoke.step = (seconds, dt = 1 / 120) => {
      const game = window.__game;
      for (let t = 0; t < seconds - 1e-8; t += dt) game.update(Math.min(dt, seconds - t));
    };
  });
}
async function pause() { await page.evaluate(() => { window.__smoke.paused = true; }); }
async function step(seconds) { await page.evaluate(seconds => window.__smoke.step(seconds), seconds); }
async function tap(key) { await page.keyboard.press(key); await step(1 / 120); }
async function settle() { await step(0.3); }
async function snapshot(label) {
  await frameReady();
  const path = resolve(output, `${label}.png`);
  await page.screenshot({ path });
  report.screenshots.push(path);
  await pause();
}
async function clearMotion(position = [0, 0, 12]) {
  await page.evaluate(position => {
    const g = window.__game;
    g.input.keys.clear();
    for (const key of ["attack", "jump", "dash", "interact"]) g.input[key] = false;
    g.dialogue = null;
    g.active = true;
    g.paused = false;
    g.player.root.position.set(...position);
    g.player.root.rotation.y = 0;
    g.velocity.set(0, 0, 0);
    g.velocityY = 0;
    g.speed = 0;
    for (const key of ["dashTime", "dashCooldown", "attackTime", "attackBuffer", "jumpBuffer", "comboWindow", "hitStop", "landing", "dodgeBuffer"]) g[key] = 0;
    g.queuedCombo = false;
    g.attackPhase = 0;
    g.coyote = 0.1;
    g.invulnerable = 0;
  }, position);
}

try {
  await check("production startup and locally loaded skinned wolf", async () => {
    await fresh();
    const data = await page.evaluate(() => {
      const p = window.__game.player, meshes = [];
      p.body.traverse(o => { if (o.isSkinnedMesh) meshes.push({ name: o.name, bones: o.skeleton.bones.length, vertices: o.geometry.attributes.position.count }); });
      return { active: window.__game.active, bootHidden: getComputedStyle(document.querySelector("#boot")).display === "none", skinnedMeshes: meshes,
        localModels: performance.getEntriesByType("resource").filter(e => e.name.endsWith(".glb")).map(e => ({ url: e.name, bytes: e.encodedBodySize })) };
    });
    assert(data.active && data.bootHidden, "Game did not leave the loading/start state");
    assert(data.skinnedMeshes.length > 0, "Wolf is not a skinned mesh");
    assert(data.skinnedMeshes.some(m => m.bones >= 12 && m.vertices > 100), "Wolf does not have an articulated skeleton");
    assert(data.localModels.length > 0 && data.localModels.every(m => new URL(m.url).origin === new URL(baseURL).origin), "Local GLB was not loaded");
    return data;
  });
  if (!await page.evaluate(() => !!window.__game).catch(() => false)) throw new Error("Startup failed; dependent checks cannot run.");

  await check("visible rendered frame with useful color variation", async () => {
    await frameReady();
    const png = await page.locator("body > canvas").screenshot();
    await writeFile(resolve(output, "gameplay-canvas.png"), png);
    report.screenshots.push(resolve(output, "gameplay-canvas.png"));
    const histogram = await page.evaluate(async b64 => {
      const image = new Image(); image.src = `data:image/png;base64,${b64}`; await image.decode();
      const canvas = document.createElement("canvas"); canvas.width = image.width; canvas.height = image.height;
      const ctx = canvas.getContext("2d"); ctx.drawImage(image, 0, 0); const data = ctx.getImageData(0, 0, canvas.width, canvas.height).data;
      let lit = 0, count = 0; const colors = new Set();
      for (let i = 0; i < data.length; i += 64) {
        const r = data[i], g = data[i + 1], b = data[i + 2];
        if (r + g + b > 50) lit++;
        colors.add(`${r >> 4},${g >> 4},${b >> 4}`); count++;
      }
      return { width: canvas.width, height: canvas.height, litRatio: lit / count, colorBuckets: colors.size };
    }, png.toString("base64"));
    assert(histogram.litRatio > 0.7 && histogram.colorBuckets > 40, "Rendered frame is dark/blank or has no meaningful scene color");
    const playerBounds = await page.evaluate(() => {
      const p = __game.player, camera = window.__camera;
      p.root.updateMatrixWorld(true); camera.updateMatrixWorld(true);
      let box;
      p.body.traverse(o => {
        if (!o.isSkinnedMesh) return;
        o.skeleton.update(); o.computeBoundingBox(); const bounds = o.boundingBox.clone().applyMatrix4(o.matrixWorld);
        if (!box) box = bounds; else box.union(bounds);
      });
      const center = box.getCenter(p.root.position.clone()).project(camera), size = box.getSize(p.root.position.clone());
      const corners = [];
      for (const x of [box.min.x, box.max.x]) for (const y of [box.min.y, box.max.y]) for (const z of [box.min.z, box.max.z]) {
        const v = p.root.position.clone().set(x, y, z).project(camera);
        corners.push([(v.x + 1) * innerWidth / 2, (1 - v.y) * innerHeight / 2]);
      }
      const minX = Math.max(0, Math.floor(Math.min(...corners.map(c => c[0])) - 16)), maxX = Math.min(innerWidth, Math.ceil(Math.max(...corners.map(c => c[0])) + 16));
      const minY = Math.max(0, Math.floor(Math.min(...corners.map(c => c[1])) - 16)), maxY = Math.min(innerHeight, Math.ceil(Math.max(...corners.map(c => c[1])) + 16));
      return { centerNDC: center.toArray(), sizeMeters: size.toArray(), visible: p.root.visible && p.body.visible, crop: { x: minX, y: minY, width: maxX - minX, height: maxY - minY } };
    });
    assert(playerBounds.visible && playerBounds.centerNDC.every(Number.isFinite) && playerBounds.centerNDC.every(v => Math.abs(v) < 1) && playerBounds.crop.width > 30 && playerBounds.crop.height > 30, "The scene rendered but the wolf is invisible/offscreen");
    assert(playerBounds.sizeMeters.every(v => v > 0.1 && v < 8), "Skinned wolf has missing or exploded bounds");
    const cropPath = resolve(output, "wolf-gameplay-crop.png"); await page.screenshot({ path: cropPath, clip: playerBounds.crop }); report.screenshots.push(cropPath);
    await snapshot("village-gameplay");
    return { ...histogram, playerBounds };
  });

  await check("animation clip data drives changing finite bone transforms", async () => {
    await pause();
    const data = await page.evaluate(() => {
      const p = window.__game.player, clips = Object.entries(p.actions).map(([name, action]) => {
        const clip = action.getClip();
        return { name, seconds: clip.duration, tracks: clip.tracks.length, samples: clip.tracks.reduce((total, t) => total + t.times.length, 0), finite: clip.tracks.every(t => [...t.times, ...t.values].every(Number.isFinite)) };
      });
      const bones = []; p.body.traverse(o => { if (o.isBone) bones.push(o); });
      const vectors = () => bones.flatMap(b => [...b.position.toArray(), ...b.quaternion.toArray(), ...b.scale.toArray()]);
      const samples = {};
      const weaponSamples = {};
      for (const name of ["Walk", "Run", "Thrust", "Sweep", "Finish"]) {
        p.mixer.stopAllAction();
        const action = p.actions[name]; action.reset().setEffectiveWeight(1).play(); action.time = action.getClip().duration * 0.1; p.mixer.update(0); const a = vectors();
        action.time = action.getClip().duration * 0.6; p.mixer.update(0); const b = vectors();
        samples[name] = { changedComponents: a.filter((v, i) => Math.abs(v - b[i]) > 0.002).length, largestChange: Math.max(...a.map((v, i) => Math.abs(v - b[i]))), finite: b.every(Number.isFinite), reasonableScale: bones.every(bone => bone.scale.toArray().every(v => v > 0.05 && v < 5)) };
        const endpoints = p.weaponEndpoints?.();
        if (endpoints) weaponSamples[name] = { tip: endpoints.tip.toArray(), heel: endpoints.heel.toArray(), length: endpoints.tip.distanceTo(endpoints.heel) };
      }
      const cylinders = p.spear.children.filter(o => o.geometry?.type === "CylinderGeometry").sort((a, b) => b.geometry.parameters.height - a.geometry.parameters.height);
      const shaftAxis = p.root.position.clone().set(0, 1, 0).applyQuaternion(cylinders[0].getWorldQuaternion(p.root.quaternion.clone()));
      const gripAxis = p.root.position.clone().set(0, 1, 0).applyQuaternion(cylinders[1].getWorldQuaternion(p.root.quaternion.clone()));
      let attachedToHead = false;
      for (let parent = p.spear.parent; parent; parent = parent.parent) if (parent === p.head) attachedToHead = true;
      p.mixer.stopAllAction(); p.state = null;
      return { clips, boneCount: bones.length, samples, weaponSamples, weapon: { attachedToHead, shaftGripDot: shaftAxis.dot(gripAxis) } };
    });
    const required = ["Idle", "Walk", "Run", "Jump", "Land", "Dodge", "Thrust", "Sweep", "Finish"];
    for (const name of required) {
      const clip = data.clips.find(c => c.name === name);
      assert(clip && clip.seconds > 0.15 && clip.tracks >= 8 && clip.finite, `${name} has missing/invalid animation data`);
    }
    for (const [name, sample] of Object.entries(data.samples)) assert(sample.finite && sample.reasonableScale && sample.changedComponents >= 8, `${name} does not articulate enough bones or has invalid transforms`);
    assert(data.weapon.attachedToHead && Math.abs(data.weapon.shaftGripDot) < 0.05, "Spear lacks its perpendicular mouth-held grip");
    assert(Object.keys(data.weaponSamples).length === 5 && Object.values(data.weaponSamples).every(w => [...w.tip, ...w.heel, w.length].every(Number.isFinite) && w.length > 2 && w.length < 4), "Animated weapon endpoints detached, collapsed, or exploded");
    return data;
  });

  await check("real WASD keyboard inputs move in camera-relative directions", async () => {
    const result = [];
    for (const [key, x, z] of [["KeyW", 0, -1], ["KeyS", 0, 1], ["KeyA", -1, 0], ["KeyD", 1, 0]]) {
      await pause(); await clearMotion();
      const before = await page.evaluate(() => ({ x: __game.player.root.position.x, z: __game.player.root.position.z, yaw: __game.input.yaw }));
      await page.keyboard.down(key); await step(0.4);
      const after = await page.evaluate(() => ({ x: __game.player.root.position.x, z: __game.player.root.position.z, state: __game.player.state, speed: __game.speed }));
      await page.keyboard.up(key); await settle();
      const dx = after.x - before.x, dz = after.z - before.z;
      const projection = dx * (x * Math.cos(before.yaw) + z * Math.sin(before.yaw)) + dz * (-x * Math.sin(before.yaw) + z * Math.cos(before.yaw));
      assert(projection > 0.6, `${key} did not move correctly: ${JSON.stringify({ before, after })}`);
      assert(["Walk", "Run"].includes(after.state), `${key} did not enter locomotion animation`);
      result.push({ key, distance: Math.hypot(dx, dz), projection, state: after.state, speed: after.speed });
    }
    return result;
  });

  await check("walk-run-idle blending and real frames stay stable", async () => {
    await pause(); await clearMotion();
    await page.keyboard.down("KeyW"); await step(0.35);
    const walk = await page.evaluate(() => ({ speed: __game.speed, state: __game.player.state }));
    await page.keyboard.down("ShiftLeft"); await step(0.35);
    const run = await page.evaluate(() => ({ speed: __game.speed, state: __game.player.state }));
    await page.keyboard.up("ShiftLeft"); await page.keyboard.up("KeyW"); await step(0.8);
    const idle = await page.evaluate(() => ({ speed: __game.speed, state: __game.player.state }));
    assert(walk.state === "Walk" && run.state === "Run" && run.speed > walk.speed * 1.2 && idle.state === "Idle", "Locomotion did not blend between walking, running, and idle");
    await clearMotion();
    await page.keyboard.down("KeyW");
    await frameReady();
    await page.waitForFunction(() => __game.speed > 1);
    const firstTime = await page.evaluate(() => __game.player.actions.Walk.time);
    const firstFrame = await page.evaluate(() => __smoke.frames);
    await page.waitForFunction(firstFrame => __smoke.frames >= firstFrame + 3, firstFrame);
    const live = await page.evaluate(() => {
      const p = __game.player, actions = Object.entries(p.actions).filter(([, a]) => a.isRunning()).map(([name, a]) => ({ name, weight: a.getEffectiveWeight(), time: a.time }));
      let finite = true, normalized = true;
      p.body.traverse(o => { if (o.isBone) { finite &&= [...o.position.toArray(), ...o.quaternion.toArray(), ...o.scale.toArray()].every(Number.isFinite); normalized &&= Math.abs(o.quaternion.length() - 1) < 0.01; } });
      const intervals = __smoke.frameIntervals.filter(v => v > 0 && v < 500).slice(-24);
      const averageFrameMs = intervals.length ? intervals.reduce((a, b) => a + b, 0) / intervals.length : null;
      return { frames: __smoke.frames, position: p.root.position.toArray(), actions, finite, normalized, softwareRendering: { sampledFrames: intervals.length, averageFrameMs, fps: averageFrameMs ? 1000 / averageFrameMs : null } };
    });
    await page.keyboard.up("KeyW"); await pause();
    assert(live.finite && live.normalized && live.actions.every(a => a.weight >= 0 && a.weight <= 1.01), "Live animation produced invalid bones/weights");
    assert(live.actions.some(a => ["Walk", "Run"].includes(a.name) && a.weight > 0.2 && Math.abs(a.time - firstTime) > 0.001), "Live locomotion action did not contribute weight or advance time");
    return { walk, run, idle, live };
  });

  await check("jump and dodge use physical inputs with grounded recovery", async () => {
    await pause(); await clearMotion();
    await tap("Space"); await step(0.1);
    const airborne = await page.evaluate(() => ({ y: __game.player.root.position.y, state: __game.player.state }));
    const contact = await page.evaluate(() => {
      for (let i = 0; i < 180; i++) {
        __smoke.step(1 / 120);
        if (__game.player.root.position.y < 0.001) return { y: __game.player.root.position.y, state: __game.player.state };
      }
      return null;
    });
    assert(contact && contact.state === "Land", "Touchdown skipped its immediate landing animation");
    await step(0.5);
    const landed = await page.evaluate(() => ({ y: __game.player.root.position.y, state: __game.player.state }));
    await clearMotion(); await tap("KeyK"); await step(0.08);
    const dodge = await page.evaluate(() => ({ z: __game.player.root.position.z, state: __game.player.state, immune: __game.invulnerable, cooldown: __game.dashCooldown }));
    await step(1);
    const recovered = await page.evaluate(() => ({ state: __game.player.state, cooldown: __game.dashCooldown }));
    assert(airborne.y > 0.3 && airborne.state === "Jump", "Jump did not leave ground/enter Jump animation");
    assert(landed.y < 0.001 && ["Idle", "Land"].includes(landed.state), "Wolf did not recover onto ground");
    assert(dodge.z < 11.5 && dodge.state === "Dodge" && dodge.immune > 0, "Dodge did not move or protect the wolf");
    assert(recovered.cooldown === 0 && recovered.state === "Idle", "Dodge recovery/cooldown did not finish");
    return { airborne, contact, landed, dodge, recovered };
  });

  await check("buildings, trees and town bounds prevent penetration", async () => {
    await pause();
    const data = await page.evaluate(() => {
      const g = __game, p = g.player.root.position;
      const boxes = g.world.boxes.map(box => {
        p.set(box.x, 0, box.z); g.collide(p);
        return { box, resolved: p.toArray(), outside: Math.abs(p.x - box.x) >= box.halfX + 0.42 || Math.abs(p.z - box.z) >= box.halfZ + 0.42 };
      });
      const trees = g.world.obstacles.map(o => { p.set(o.x, 0, o.z); g.collide(p); return { obstacle: o, resolved: p.toArray(), outside: Math.hypot(p.x - o.x, p.z - o.z) >= o.r + 0.42 }; });
      const b = g.world.bounds; p.set(b.maxX + 50, 0, b.minZ - 50); g.collide(p);
      return { boxes, trees, bounds: b, boundaryPosition: p.toArray(), inside: p.x <= b.maxX - 0.42 && p.z >= b.minZ + 0.42 };
    });
    assert(data.boxes.length >= 5 && data.boxes.every(x => x.outside), "Building collision allowed penetration");
    assert(data.trees.every(x => x.outside) && data.inside, "Tree/boundary collision allowed penetration");
    const wall = await page.evaluate(() => __game.world.boxes[0]);
    await clearMotion([wall.x, 0, wall.z + wall.halfZ + 0.6]);
    const yaw = await page.evaluate(() => { const yaw = __game.input.yaw; __game.input.yaw = 0; return yaw; });
    await page.keyboard.down("ShiftLeft"); await page.keyboard.down("KeyW"); await step(0.6);
    await tap("KeyK"); await step(0.4);
    await page.keyboard.up("KeyW"); await page.keyboard.up("ShiftLeft");
    const highSpeed = await page.evaluate(yaw => {
      const g = __game, box = g.world.boxes[0], position = g.player.root.position.toArray();
      g.input.yaw = yaw;
      return { position, outside: position[2] >= box.z + box.halfZ + 0.42 };
    }, yaw);
    assert(highSpeed.outside, "Sprinting/dodging into a building tunneled through its wall");
    data.highSpeedWallContact = highSpeed;
    await clearMotion();
    return data;
  });

  await check("NPC dialogue opens, advances, holds movement and closes", async () => {
    await pause(); await clearMotion();
    const name = await page.evaluate(() => {
      const g = __game, npc = g.world.npcs[0]; g.player.root.position.copy(npc.root.position); g.player.root.position.x += 0.9; return npc.name;
    });
    await tap("KeyE");
    const opened = await page.evaluate(() => ({ name: __game.dialogue?.npc.name, line: __game.dialogue?.line, position: __game.player.root.position.toArray() }));
    assert(opened.name === name && opened.line === 0, "E did not open the nearby NPC dialogue");
    await page.keyboard.down("KeyW"); await step(0.35); await page.keyboard.up("KeyW");
    const after = await page.evaluate(() => __game.player.root.position.toArray());
    assert.deepEqual(after, opened.position, "Moving while reading NPC dialogue should be held");
    await tap("KeyE");
    assert(await page.evaluate(() => !__game.dialogue || __game.dialogue.line === 1), "E did not advance dialogue");
    let taps = 1;
    while (await page.evaluate(() => !!__game.dialogue)) {
      await tap("KeyE"); if (++taps > 12) throw new Error("Dialogue would not close after twelve advances");
    }
    await snapshot("npc-dialogue-closed");
    return { npc: name, advancesToClose: taps, movementHeld: true };
  });

  await check("village remains safe and grove enemies return to their leash", async () => {
    await pause(); await clearMotion();
    const result = await page.evaluate(() => {
      const g = __game; g.hp = 100;
      for (const e of g.enemies) { e.mesh.position.set(14.5, 0, 0); e.state = "lunge"; e.timer = 1; e.stun = 0; e.attackDirection.set(-1, 0, 0); }
      g.player.root.position.set(10, 0, 0); g.invulnerable = 0;
      __smoke.step(3);
      return { hp: g.hp, enemies: g.enemies.map(e => ({ x: e.mesh.position.x, home: e.home.toArray(), state: e.state })), active: g.active };
    });
    assert(result.hp === 100 && result.active && result.enemies.every(e => e.x > 15), "Grove enemies chased/damaged the wolf in the village");
    return result;
  });

  await check("physical buffered combo progresses one-two-three and resets", async () => {
    await pause(); await clearMotion();
    await page.evaluate(() => { for (const e of __game.enemies) { e.mesh.position.copy(e.home); e.stun = 100; } });
    const trace = [];
    await tap("KeyJ");
    for (let i = 0; i < 450; i++) {
      const state = await page.evaluate(() => ({ combo: __game.combo, remaining: __game.attackTime, duration: __game.attackDuration, animation: __game.player.state, hit: !!__game.didHit }));
      if (!trace.some(s => s.combo === state.combo) && state.remaining > 0) trace.push(state);
      if (state.combo === 3 && state.remaining > 0 && state.remaining < state.duration * 0.3) break;
      if (state.remaining > 0 && state.remaining < state.duration * 0.3 && state.combo < 3 && !trace.find(s => s.combo === state.combo)?.buffered) {
        const entry = trace.find(s => s.combo === state.combo); if (entry) entry.buffered = true;
        await page.keyboard.press("KeyJ");
      }
      await step(1 / 120);
    }
    assert.deepEqual(trace.map(s => s.combo), [1, 2, 3], `Buffered combo did not progress through three attacks: ${JSON.stringify(trace)}`);
    assert.deepEqual(trace.map(s => s.animation), ["Thrust", "Sweep", "Finish"], "Combo animations did not match attack number");
    await step(1.5); await tap("KeyJ");
    const reset = await page.evaluate(() => __game.combo);
    assert(reset === 1, "Expired combo did not restart at first attack");
    await snapshot("combat-combo");
    return { attacks: trace, reset };
  });

  await check("attack timing and directional cones distinguish thrust/sweep/finish", async () => {
    await pause();
    const data = await page.evaluate(() => {
      const g = __game, results = [];
      for (const combo of [1, 2, 3]) {
        g.player.root.position.set(26, 0, 0); g.player.root.rotation.y = 0; g.dialogue = null; g.hitStop = 0; g.velocity.set(0, 0, 0); g.attackTime = 0; g.attackBuffer = 0;
        for (let i = 0; i < g.enemies.length; i++) { const e = g.enemies[i]; e.hp = 20; e.maxHp = 20; e.stun = 100; e.mesh.visible = true; e.knockback?.set(0, 0, 0); e.mesh.position.set(40, 0, 20); }
        g.combo = combo - 1; g.comboWindow = 1; g.startAttack(combo); g.player.root.rotation.y = 0;
        const duration = g.attackDuration, definition = g.attacks?.[combo];
        const hitFraction = definition?.hit ?? [0, 0.3, 0.48, 0.52][combo];
        const active = definition?.active ?? [hitFraction, hitFraction];
        const positions = [[26, 0, -2], [28, 0, 0], [26, 0, 2]];
        positions.forEach((p, i) => g.enemies[i].mesh.position.set(...p));
        __smoke.step(Math.max(0, duration * active[0] - 1 / 120));
        const before = g.enemies.slice(0, 3).map(e => e.hp);
        __smoke.step(duration * (active[1] - active[0]) + 0.18);
        const after = g.enemies.slice(0, 3).map(e => e.hp);
        results.push({ combo: g.combo, duration, hitFraction, activeWindow: active, before, after, definition });
      }
      return results;
    });
    for (const test of data) {
      assert(test.before.every(hp => hp === 20), `Attack ${test.combo} hit before its authored contact time`);
      assert(test.after[0] < 20 && test.after[2] === 20, `Attack ${test.combo} hit/missed incorrect forward/rear cone: ${JSON.stringify(test)}`);
      if (test.combo === 2) assert(test.after[1] < 20, "Sweep did not reach the wolf's side");
      else assert(test.after[1] === 20, "A forward thrust incorrectly hit a perpendicular enemy");
    }
    assert(data[0].duration < data[1].duration && data[1].duration < data[2].duration, "Combo has no rhythmic progression in its timings");
    const wallBlocked = await page.evaluate(() => {
      const g = __game, box = g.world.boxes[0], e = g.enemies[0];
      g.player.root.position.set(box.x, 0, box.z + box.halfZ + 0.5); g.player.root.rotation.y = 0;
      e.mesh.position.set(box.x, 0, box.z + box.halfZ - 0.5); e.hp = 20;
      g.startAttack(1); g.player.root.rotation.y = 0; g.strike();
      return { hp: e.hp, clearShot: g.clearShot(g.player.root.position, e.mesh.position) };
    });
    assert(wallBlocked.hp === 20 && !wallBlocked.clearShot, "Spear contact passed through a building wall");
    return { attacks: data, wallBlocked };
  });

  await check("buffered contact combo preserves hit pauses and dodge recovery", async () => {
    await fresh(); await pause(); await clearMotion([26, 0, 0]);
    await page.evaluate(() => {
      const g = __game;
      for (const e of g.enemies) { e.mesh.position.set(40, 0, 18); e.stun = 100; }
      const e = g.enemies[0]; e.mesh.position.set(26, 0, -2); e.home.copy(e.mesh.position); e.hp = e.maxHp = 50;
    });
    await tap("KeyJ");
    const contacts = [];
    for (const [combo, hp] of [[1, 49], [2, 47], [3, 44]]) {
      const contact = await page.evaluate(({ combo, hp }) => {
        const g = __game, e = g.enemies[0];
        for (let i = 0; i < 400; i++) {
          if (g.combo === combo && e.hp === hp) return { combo: g.combo, hp: e.hp, hitStop: g.hitStop, phase: g.attackPhase, animation: g.player.state };
          __smoke.step(1 / 120);
        }
        return { combo: g.combo, hp: e.hp, hitStop: g.hitStop, phase: g.attackPhase, animation: g.player.state };
      }, { combo, hp });
      assert(contact.combo === combo && contact.hp === hp && contact.hitStop > 0, `Combo ${combo} contact or impact pause failed: ${JSON.stringify(contact)}`);
      contacts.push(contact);
      if (combo < 3) {
        await tap("KeyJ");
        assert(await page.evaluate(() => __game.queuedCombo), "An actual J press during hit stop was lost");
      }
    }
    await page.evaluate(() => {
      const g = __game, cancel = g.attacks[3].cancel;
      for (let i = 0; i < 150 && g.attackPhase < cancel; i++) __smoke.step(1 / 120);
    });
    await tap("KeyK"); await step(0.025);
    const cancelled = await page.evaluate(() => ({ state: __game.player.state, attackTime: __game.attackTime, dashTime: __game.dashTime }));
    assert(cancelled.state === "Dodge" && cancelled.attackTime === 0 && cancelled.dashTime > 0, "Dodge did not flow out of the finisher's recovery");
    return { contacts, cancelled };
  });

  await check("enemy windup-lunge-recovery animation and damage", async () => {
    await fresh(); await pause(); await clearMotion([26, 0, 0]);
    const result = await page.evaluate(() => {
      const g = __game, e = g.enemies[0];
      for (const o of g.enemies) { o.mesh.position.set(40, 0, 18); o.stun = 100; }
      e.mesh.position.set(26, 0, -1.65); e.cooldown = 0; e.state = "approach"; e.stun = 0;
      const states = [], transforms = [];
      for (let i = 0; i < 240; i++) {
        g.update(1 / 120);
        if (!states.includes(e.state)) states.push(e.state);
        if (i % 12 === 0) {
          const r = e.visual.rig;
          const joints = [r.torso, r.head, ...r.arms.flatMap(a => [a.shoulder, a.elbow]), ...r.legs.flatMap(l => [l.hip, l.knee, l.foot])];
          transforms.push({ state: e.state, joints: joints.flatMap(o => [...o.position.toArray(), ...o.quaternion.toArray()]) });
        }
      }
      return { states, hp: g.hp, enemyPosition: e.mesh.position.toArray(), transforms };
    });
    assert(["windup", "lunge", "recover"].every(state => result.states.includes(state)), "Enemy did not traverse readable attack phases");
    assert(result.hp < 100 && result.hp > 0, "Enemy attack did not apply health damage");
    assert(result.transforms.every(s => s.joints.every(Number.isFinite)), "Enemy joint poses contain invalid values");
    const first = result.transforms[0].joints;
    const changing = result.transforms.filter(s => s.joints.some((v, i) => Math.abs(v - first[i]) > 0.01));
    assert(changing.length >= 4 && result.transforms.some(s => s.state === "lunge" && s.joints.filter((v, i) => Math.abs(v - first[i]) > 0.01).length >= 8), "Enemy attack phases did not articulate multiple rig joints");
    return result;
  });

  await check("defeat UI and restart reset combat without stale state", async () => {
    await pause(); await clearMotion([26, 0, 0]);
    await page.evaluate(() => {
      const g = __game; g.hp = 1; g.invulnerable = 0; const e = g.enemies[0];
      e.stun = 0; e.hitPlayer = false; e.mesh.position.set(26, 0, 0.5); e.state = "lunge"; e.timer = 0.2; e.attackDirection.set(0, 0, -1); g.update(1 / 120);
    });
    assert(await page.evaluate(() => __game.hp === 0 && !__game.active), "Lethal damage did not end the run");
    await frameReady();
    assert(await page.locator("#restart").isVisible(), "Defeat restart button was not shown");
    await page.locator("#restart").click();
    await page.waitForFunction(() => __game.hp === 100 && __game.enemies.every(e => e.hp === e.maxHp));
    if (await page.locator("#start").isVisible().catch(() => false)) await page.locator("#start").click();
    await page.waitForFunction(() => __game.active);
    await pause();
    // A reload can replace the harness's simulation helper.
    await page.evaluate(() => { __smoke.step ??= (seconds, dt = 1 / 120) => { for (let t = 0; t < seconds - 1e-8; t += dt) __game.update(Math.min(dt, seconds - t)); }; });
    const reset = await page.evaluate(() => ({ hp: __game.hp, active: __game.active, kills: __game.kills, combo: __game.combo, attackTime: __game.attackTime, invulnerable: __game.invulnerable, enemies: __game.enemies.map(e => ({ visible: e.mesh.visible, dead: e.visual.dead, finished: e.visual.finished, opacity: e.visual.materials.map(m => m.opacity) })) }));
    assert(reset.kills === 0 && reset.attackTime === 0 && reset.invulnerable === 0 && reset.enemies.every(e => e.visible && !e.dead && !e.finished && e.opacity.every(v => v === 1)), "Restart left stale attack/death state");
    return reset;
  });

  await check("win occurs after five deaths then permits further exploration", async () => {
    await pause(); await clearMotion([26, 0, 0]);
    const result = await page.evaluate(() => {
      const g = __game; g.combo = 0; g.comboWindow = 0; g.startAttack(1); g.player.root.rotation.y = 0;
      g.enemies.forEach(e => { e.hp = 1; e.mesh.visible = true; e.stun = 100; e.mesh.position.set(26, 0, -2); });
      g.strike();
      const dying = g.enemies.map(e => ({ hp: e.hp, state: e.state, visible: e.mesh.visible, deathTime: e.visual?.deathTime }));
      __smoke.step(1.6);
      return { kills: g.kills, victory: g.victory, active: g.active, dying, enemies: g.enemies.map(e => ({ hp: e.hp, state: e.state, visible: e.mesh.visible, finished: e.visual?.finished, deathTime: e.visual?.deathTime })) };
    });
    assert(result.kills === 5 && result.victory && !result.active && result.enemies.every(e => e.hp === 0), "Restoring all spirits did not produce victory");
    assert(result.dying.every(e => e.state === "dead" && e.visible) && result.enemies.every(e => e.finished || !e.visible), "Enemies did not visibly enter a death animation before fading away");
    await frameReady(); await page.locator("#restart").click(); await pause();
    assert(await page.evaluate(() => __game.active && __game.victory), "Victory continue button reset/stopped exploration");
    await clearMotion(); await page.keyboard.down("KeyW"); await step(0.3); await page.keyboard.up("KeyW");
    assert(await page.evaluate(() => __game.player.root.position.z < 11.5), "Wolf could not explore after victory");
    await step(2);
    return result;
  });

  await check("collectible flowers and shrine offering form a complete activity", async () => {
    await fresh(); await pause();
    const flowers = await page.evaluate(() => {
      const a = __game.activities; return a ? a.blooms.map(b => ({ id: b.id, position: b.root.position.toArray() })) : [];
    });
    assert(flowers.length >= 3, "Town has no implemented flower activity");
    for (const flower of flowers) {
      await clearMotion(flower.position); await tap("KeyE");
      await page.evaluate(() => { __game.dialogue = null; });
    }
    const collected = await page.evaluate(() => ({ count: __game.activities.collected, flags: __game.activities.blooms.map(b => b.collected) }));
    assert(collected.count === flowers.length && collected.flags.every(Boolean), "E did not collect all flower activities");
    const shrinePosition = await page.evaluate(() => __game.activities.shrine?.position?.toArray?.() || __game.activities.shrine?.root?.position?.toArray?.() || [0, 0, -21]);
    await clearMotion(shrinePosition); await tap("KeyE");
    const reward = await page.evaluate(() => ({ offered: __game.activities.offered, hp: __game.hp, maxHp: __game.maxHp, bloomsHidden: __game.activities.blooms.every(b => !b.root.visible) }));
    assert(reward.offered && reward.hp === 120 && reward.maxHp === 120 && reward.bloomsHidden, "Offering did not grant its once-only health reward and hide gathered flowers");
    await page.evaluate(() => { __game.hp = 40; }); await tap("KeyE");
    const healing = await page.evaluate(() => ({ hp: __game.hp, maxHp: __game.maxHp }));
    assert(healing.hp === 120 && healing.maxHp === 120, "Shrine did not heal the wolf or stacked its maximum health reward");
    return { flowers, collected, shrinePosition, reward, healing };
  });

  await check("audio starts after a gesture and mute toggles cleanly", async () => {
    await frameReady();
    const button = page.locator("#sound-toggle, #mute, button[aria-label*='sound' i], button[aria-label*='audio' i]").first();
    assert(await button.count(), "No audio/mute button is present");
    const audio = await page.evaluate(() => ({ unlocked: __game.audio.unlocked, state: __game.audio.context?.state, volume: __game.audio.volume, maxVoices: __game.audio.maxVoices }));
    assert(audio.unlocked && audio.state === "running", "Start/keyboard gestures did not unlock local sound synthesis");
    const before = await button.getAttribute("aria-pressed");
    await button.click();
    await page.waitForFunction(before => document.querySelector("#sound-toggle")?.getAttribute("aria-pressed") !== before, before);
    const after = await button.getAttribute("aria-pressed");
    await button.click();
    await page.waitForFunction(before => document.querySelector("#sound-toggle")?.getAttribute("aria-pressed") === before, before);
    const restored = await button.getAttribute("aria-pressed");
    assert(before !== after && restored === before, "Mute UI state did not toggle and restore");
    const synthesis = await page.evaluate(() => {
      const a = __game.audio;
      a.setMuted(false);
      const hit = a.play("heavyHit", { heavy: true });
      const swing = a.play("swing", { combo: 2 });
      const voices = a.voices;
      a.setMuted(true); const mutedPlay = a.play("playerHit"); a.setMuted(false);
      return { hit, swing, voices, voiceLimit: a.maxVoices, mutedPlay, masterGain: a.master.gain.value };
    });
    assert(synthesis.hit && synthesis.swing && synthesis.voices > 0 && synthesis.voices <= synthesis.voiceLimit && !synthesis.mutedPlay, "Weapon synthesis did not create bounded audible voices or respect mute");
    return { before, after, restored, title: await button.getAttribute("title"), audio, synthesis };
  });

  await check("resize updates canvas and retains rendered scene", async () => {
    await page.setViewportSize({ width: 900, height: 640 }); await frameReady();
    const small = await page.evaluate(() => { const c = document.querySelector("body > canvas"); return { width: c.width, height: c.height, clientWidth: c.clientWidth, clientHeight: c.clientHeight }; });
    assert(small.clientWidth === 900 && small.clientHeight === 640, "Canvas did not resize with viewport");
    await snapshot("resized-900x640");
    await page.setViewportSize({ width: 1440, height: 900 }); await frameReady();
    return small;
  });

  await check("blocked WebGL shows useful visible startup error", async () => {
    const blocked = await context.newPage();
    await blocked.addInitScript(() => {
      const getContext = HTMLCanvasElement.prototype.getContext;
      HTMLCanvasElement.prototype.getContext = function (kind, ...args) {
        if (/webgl/i.test(kind)) return null;
        return getContext.call(this, kind, ...args);
      };
    });
    try {
      await blocked.goto(baseURL, { waitUntil: "domcontentloaded" });
      await blocked.waitForFunction(() => /3D rendering is unavailable/i.test(document.querySelector("#boot-message")?.textContent || ""), null, { timeout: 10000 });
      const message = await blocked.locator("#boot-message").textContent();
      assert(await blocked.locator("#boot").isVisible(), "Blocked graphics left a blank screen instead of an error");
      const path = resolve(output, "webgl-unavailable.png"); await blocked.screenshot({ path }); report.screenshots.push(path);
      return { message };
    } finally { await blocked.close(); }
  });

  await check("no JavaScript, request, or external dependency failures", async () => {
    assert.equal(report.browserErrors.length, 0, report.browserErrors.join("\n"));
    assert.equal(report.responsesWithErrors.length, 0, JSON.stringify(report.responsesWithErrors));
    assert.equal(report.failedRequests.length, 0, JSON.stringify(report.failedRequests));
    assert.equal(report.externalRequests.length, 0, JSON.stringify(report.externalRequests));
    return { browserErrors: 0, requestFailures: 0, externalRequests: 0 };
  });
} catch (error) {
  report.fatal = error.stack || String(error);
  process.stdout.write(`FATAL ${error.message}\n`);
} finally {
  report.finishedUTC = new Date().toISOString();
  report.finishedSydney = new Intl.DateTimeFormat("en-AU", { timeZone: "Australia/Sydney", dateStyle: "full", timeStyle: "long" }).format(new Date());
  report.durationSeconds = (Date.now() - began.getTime()) / 1000;
  report.passed = report.checks.filter(c => c.pass).length;
  report.failed = report.checks.filter(c => !c.pass).length;
  await writeFile(resolve(output, "report.json"), `${JSON.stringify(report, null, 2)}\n`);
  await browser.close();
  process.stdout.write(`${report.passed} passed; ${report.failed} failed. Report: ${resolve(output, "report.json")}\n`);
  if (report.failed || report.fatal) process.exitCode = 1;
}

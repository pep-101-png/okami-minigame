import * as THREE from "three";
import "./style.css";
import { Input } from "./input.js";
import { createTown } from "./town.js";
import { ATTACKS } from "./combat.js";
import { Game } from "./game.js";
import { loadWolf } from "./wolf.js";
import { FollowCamera } from "./camera.js";
import { createPainterlyRenderer } from "./rendering.js";

await loadWolf();
document.querySelector("#app").innerHTML = `
  <div id="hud">
    <div class="eyebrow">A SPIRIT'S JOURNEY</div><div class="title">Sunward</div>
    <div class="subtitle">THE CRIMSON GUARDIAN</div>
    <div class="health-wrap"><div class="row"><span>VITALITY</span><span id="hp">100 / 100</span></div><div class="bar"><div class="fill" id="health"></div></div></div>
    <button id="sound-toggle" type="button" aria-pressed="false">SOUND ON · M</button>
    <div class="quest"><div class="eyebrow">WINDFLOWER VILLAGE</div><strong>Restore the eastern grove</strong><small id="count">0 / 5 spirits restored</small><small id="task-summary">Windflowers · 0 / 3</small></div>
    <div id="wolf-status"><span id="bark-status">B · Guardian bark ready</span><span id="voice-status">V · Growl</span></div>
    <div id="charge-meter" class="hidden"><span id="charge-name">Charging</span><div class="charge-track"><div id="charge-fill"></div></div><small>Release to strike · K to cancel</small></div>
    <div class="center" id="combo">守護 · PROTECT THE GROVE</div>
    <div class="controls"><span><b>W A S D</b> Move</span><span><b>E</b> Interact</span><span><b>SPACE</b> Jump · <b>SHIFT</b> Run</span><span><b>K</b> Dodge · <b>LMB / J</b> Normal · hold to charge</span><span><b>RMB / L</b> Heavy · hold to charge &nbsp; <b>B</b> Bark stun</span></div>
    <div class="badge">ACT I / DAWN</div>
  </div>
  <div id="toast" role="status" aria-live="polite"></div>
  <div id="overlay"><div class="panel"><div class="eyebrow">THE SACRED GROVE CALLS</div><h1>A light in the mist.</h1><p>Walk the painted streets of Windflower. Talk to Hana in the garden, collect three windflowers for the northern shrine, and follow the road east to restore five restless spirits.</p><p>Tap left click to link strikes, or hold and release to charge. Right click is heavy; attack in the air to dive. B unleashes a stunning bark. Watch the spirits wind up, then dodge their charge.</p><button id="start">ENTER THE VILLAGE →</button></div></div>
  <div id="pause-panel" class="hidden"><div class="panel"><div class="eyebrow">A MOMENT OF STILLNESS</div><h1>Paused.</h1><p>WASD moves · Shift runs · Space jumps.<br>Tap left click/J for combos; hold for charged thrust.<br>Tap right click/L for heavy; hold for Sunbreak.<br>Attack while jumping for Falling Star.<br>B barks and stuns · V plays your selected voice.<br>K dodges · E interacts · Wheel zooms · M mutes.</p><label class="voice-control" for="voice-select">Wolf voice (V) <select id="voice-select"><option value="growl">Growl</option><option value="bark">Soft bark</option><option value="howl">Howl</option></select></label><label class="volume-control" for="volume">Sound volume <input id="volume" type="range" min="0" max="100" value="45"></label><button id="resume">RETURN TO THE VILLAGE →</button></div></div>
  <div id="dialogue" class="hidden"></div><div id="talk-prompt"></div>`;
const ui = Object.fromEntries(
  [
    "overlay",
    "hp",
    "health",
    "count",
    "combo",
    "dialogue",
    "talk-prompt",
    "toast",
    "task-summary",
    "sound-toggle",
    "pause-panel",
  ].map((id) => [id, document.getElementById(id)]),
);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.NoToneMapping;
document.body.prepend(renderer.domElement);
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(
  38,
  innerWidth / innerHeight,
  0.1,
  140,
);
const input = new Input(renderer.domElement);
const world = createTown(scene);
const followCamera = new FollowCamera(camera, input);
const painterly = createPainterlyRenderer(renderer, scene, camera);
const game = new Game(scene, input, world, (win) => {
  ui.overlay.classList.remove("hidden");
  ui.overlay.querySelector(".panel").innerHTML =
    `<div class="eyebrow">${win ? "THE LIGHT RETURNS" : "THE GROVE STILL CALLS"}</div><h1>${win ? "Dawn is restored." : "Rise once more."}</h1><p>${win ? "The five spirits are at peace. Return to the village, finish your windflower offering, or rest beneath the blossoms." : "Your spirit endures. Offer windflowers at the northern shrine for extra vitality. Dodge the golden windup, then step in during recovery."}</p><button id="restart">${win ? "CONTINUE EXPLORING →" : "TRY AGAIN →"}</button>`;
  document.getElementById("restart").onclick = () => {
    ui.overlay.classList.add("hidden");
    input.clear();
    if (win) game.active = true;
    else game.reset();
  };
});
game.cameraImpact = (strength) => followCamera.impact(strength);
renderer.domElement.addEventListener("webglcontextlost", (event) => {
  event.preventDefault();
  window.showGameError?.(
    "The graphics connection was lost. Reload the page to restore the village.",
  );
});
document.getElementById("start").onclick = () => {
  game.active = true;
  input.clear();
  ui.overlay.classList.add("hidden");
  game.audio.unlock();
};
document.getElementById("resume").onclick = () => {
  game.paused = false;
  input.clear();
};
document.getElementById("voice-select").onchange = (event) => {
  game.abilities.voiceOption = event.target.value;
};
document.getElementById("volume").oninput = (event) =>
  game.audio.setVolume(Number(event.target.value) / 100);
ui["sound-toggle"].onclick = () => {
  game.audio.unlock();
  game.audio.toggleMute();
};
window.addEventListener("blur", () => {
  if (game.active) game.paused = true;
});
let previous = performance.now();
let displayedDialogue = null;
function frame(now) {
  const dt = Math.min((now - previous) / 1000, 0.05);
  previous = now;
  game.update(dt);
  followCamera.update(game.player.root, dt, game.speed, game.velocity);
  ui.hp.textContent = `${game.hp} / ${game.maxHp}`;
  ui.health.style.width = `${(game.hp / game.maxHp) * 100}%`;
  ui.count.textContent = `${game.kills} / ${game.enemies.length} spirits restored`;
  ui["task-summary"].textContent = game.activities.summary;
  ui.combo.textContent =
    game.attackTime > 0
      ? game.attackData().name
      : game.player.root.position.x > 15
        ? game.victory
          ? "SPIRIT GROVE · AT PEACE"
          : "SPIRIT GROVE · WATCH THE WINDUP"
        : "WINDFLOWER · SAFE HAVEN";
  const charge = game.abilities.charge;
  const charging = game.abilities.charging;
  document
    .getElementById("charge-meter")
    .classList.toggle("hidden", !charging || !game.active || game.paused);
  document.getElementById("charge-fill").style.width =
    `${game.abilities.chargeRatio * 100}%`;
  document.getElementById("charge-name").textContent =
    charge?.kind === "heavy"
      ? game.abilities.chargeRatio === 1
        ? "SUNBREAK READY"
        : "CHARGING HEAVY"
      : game.abilities.chargeRatio === 1
        ? "DAWN THRUST READY"
        : "CHARGING THRUST";
  document.getElementById("bark-status").textContent =
    game.abilities.barkCooldown > 0
      ? `B · Bark ${game.abilities.barkCooldown.toFixed(1)}s`
      : "B · Guardian bark ready";
  document.getElementById("voice-status").textContent =
    `V · ${game.abilities.voiceOption}`;
  const nearestActivity =
    game.nearActivity &&
    (!game.nearNpc ||
      game.nearActivity.root.position.distanceTo(game.player.root.position) <
        game.nearNpc.root.position.distanceTo(game.player.root.position));
  ui["talk-prompt"].textContent =
    game.active &&
    !game.dialogue &&
    !game.paused &&
    game.player.root.position.x < 15
      ? nearestActivity
        ? game.activities.prompt(game.nearActivity)
        : game.nearNpc
          ? `E · Talk to ${game.nearNpc.name}`
          : ""
      : "";
  ui.toast.textContent =
    game.toast.timer > 0 && game.active && !game.dialogue && !game.paused
      ? game.toast.text
      : "";
  ui.dialogue.classList.toggle("hidden", !game.dialogue);
  const dialogueKey = game.dialogue
    ? `${game.dialogue.npc.name}:${game.dialogue.line}`
    : null;
  if (dialogueKey && dialogueKey !== displayedDialogue) {
    ui.dialogue.replaceChildren();
    const name = document.createElement("strong"),
      text = document.createElement("p"),
      hint = document.createElement("small");
    name.textContent = game.dialogue.npc.name;
    text.textContent = game.dialogue.lines[game.dialogue.line];
    hint.textContent =
      game.dialogue.line === game.dialogue.lines.length - 1
        ? "E · Close"
        : "E · Continue";
    ui.dialogue.append(name, text, hint);
  }
  displayedDialogue = dialogueKey;
  ui["pause-panel"].classList.toggle("hidden", !game.paused);
  ui["sound-toggle"].textContent = game.audio.muted
    ? "SOUND OFF · M"
    : "SOUND ON · M";
  ui["sound-toggle"].setAttribute("aria-pressed", String(game.audio.muted));
  painterly.render();
  requestAnimationFrame(frame);
}
camera.position.set(9, 8, 24);
requestAnimationFrame(frame);
window.addEventListener("resize", () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  painterly.resize(innerWidth, innerHeight);
});
// Inspectable state for browser checks; no hidden autoplay or remote assets.
window.__game = game;
window.__combat = ATTACKS;
window.__camera = camera;
window.__renderer = renderer;
window.__view = { scene, camera, renderer, painterly, followCamera };

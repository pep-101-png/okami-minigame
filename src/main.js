import * as THREE from "three";
import "./style.css";
import { Input } from "./input.js";
import { createWorld } from "./world.js";
import { Game } from "./game.js";
import { requestPointer } from "./pointer.js";
import { FollowCamera } from "./camera.js";
import { createPainterlyRenderer } from "./rendering.js";
document.querySelector("#app").innerHTML =
  `<div id="hud"><div class="eyebrow">A SPIRIT'S JOURNEY</div><div class="title">Sunward</div><div class="subtitle">THE CRIMSON GUARDIAN</div><div class="health-wrap"><div class="row"><span>VITALITY</span><span id="hp">100 / 100</span></div><div class="bar"><div class="fill" id="health"></div></div></div><div class="quest"><div class="eyebrow">THE SACRED GROVE</div><strong>Cleanse the shadows</strong><small id="count">0 / 5 spirits restored</small></div><div class="center" id="combo">守護 • PROTECT THE GROVE</div><div class="controls"><span><b>W A S D</b> Move</span><span><b>MOUSE</b> Look</span><span><b>SPACE</b> Jump · <b>SHIFT</b> Run · <b>K</b> Dodge</span><span><b>CLICK / J</b> Spear combo</span><span><b>ESC</b> Release cursor</span></div><div class="badge">ACT I / DAWN</div></div><div id="overlay"><div class="panel"><div class="eyebrow">THE SACRED GROVE CALLS</div><h1>A light in the mist.</h1><p>Take the path of the white wolf. Restore five wandering spirits with your sacred spear. Chain three thrusts, hold Shift to run, and press K to dodge. Watch for the spirits’ attack windups.</p><button id="start">ENTER THE GROVE →</button></div></div>`;
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(Math.min(devicePixelRatio, 1.5));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.NoToneMapping;
document.body.prepend(renderer.domElement);
const scene = new THREE.Scene(),
  camera = new THREE.PerspectiveCamera(55, innerWidth / innerHeight, 0.1, 100);
const input = new Input(renderer.domElement);
const world = createWorld(scene);
const followCamera = new FollowCamera(camera, input);
const painterly = createPainterlyRenderer(renderer, scene, camera);
const overlay = document.querySelector("#overlay");
const game = new Game(scene, input, world, (win) => {
  overlay.classList.remove("hidden");
  overlay.querySelector(".panel").innerHTML =
    `<div class="eyebrow">${win ? "THE LIGHT RETURNS" : "THE GROVE STILL CALLS"}</div><h1>${win ? "Dawn is restored." : "Rise once more."}</h1><p>${win ? "The shadows fade. Beneath the blossoms, the sacred grove breathes again." : "Your spirit endures. Keep your distance, chain your thrusts, and leap over attacks."}</p><button id="restart">RETURN TO THE GROVE →</button>`;
  document.querySelector("#restart").onclick = () => location.reload();
});
renderer.domElement.addEventListener("webglcontextlost", (event) => {
  event.preventDefault();
  window.showGameError(
    "The graphics connection was lost. Reload the page to restore the grove.",
  );
});
document.querySelector("#start").onclick = () => {
  game.active = true;
  overlay.classList.add("hidden");
  requestPointer(renderer.domElement);
};
let previous = performance.now();
function frame(now) {
  const dt = Math.min((now - previous) / 1000, 0.05);
  previous = now;
  game.update(dt);
  followCamera.update(game.player.root, dt, game.speed);
  document.querySelector("#hp").textContent = `${game.hp} / 100`;
  document.querySelector("#health").style.width = `${game.hp}%`;
  document.querySelector("#count").textContent =
    `${game.kills} / 5 spirits restored`;
  document.querySelector("#combo").textContent =
    game.attackTime > 0
      ? ["", "一 • FIRST THRUST", "二 • SECOND THRUST", "三 • CRIMSON FINISH"][
          game.combo
        ]
      : "守護 • PROTECT THE GROVE";
  painterly.render();
  requestAnimationFrame(frame);
}
camera.position.set(0, 6, 13);
requestAnimationFrame(frame);
window.addEventListener("resize", () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight);
  painterly.resize(innerWidth, innerHeight);
});
// Read-only state exposed for automated smoke checks and future debugging.
window.__game = game;

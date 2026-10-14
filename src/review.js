import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { wolf, loadWolf } from "./divine-wolf.js";
await loadWolf();
import { animateWolf } from "./animation.js";
import { createPainterlyRenderer } from "./rendering.js";
const scene = new THREE.Scene();
scene.background = new THREE.Color("#e9dec0");
scene.add(new THREE.HemisphereLight("#fff6df", "#857859", 1.3));
const light = new THREE.DirectionalLight("#fff0cc", 1.5);
light.position.set(-3, 7, -4);
light.castShadow = true;
light.shadow.bias = -0.001;
light.shadow.normalBias = 0.035;
light.shadow.mapSize.set(1024, 1024);
light.shadow.camera.near = 0.1;
light.shadow.camera.far = 25;
scene.add(light);
const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(innerWidth, innerHeight);
renderer.setPixelRatio(1);
renderer.shadowMap.enabled = true;
document.body.append(renderer.domElement);
const floor = new THREE.Mesh(
  new THREE.PlaneGeometry(30, 30),
  new THREE.MeshStandardMaterial({ color: "#ddd0ae", roughness: 1 }),
);
floor.rotation.x = -Math.PI / 2;
floor.receiveShadow = true;
floor.position.y = -0.015;
scene.add(floor);
const camera = new THREE.PerspectiveCamera(
  38,
  innerWidth / innerHeight,
  0.1,
  100,
);
camera.position.set(-6.5, 2.8, -2.2);
camera.lookAt(0, 0.95, -0.75);
const painterly = createPainterlyRenderer(renderer, scene, camera),
  model = wolf();
scene.add(model.root);
model.spear.visible = false;
const controls = new OrbitControls(camera, renderer.domElement);
controls.target.set(0, 1, -0.3);
controls.enableDamping = true;
controls.minDistance = 3.5;
controls.maxDistance = 13;
controls.maxPolarAngle = Math.PI * 0.49;
controls.update();
document.querySelectorAll("[data-mode]").forEach((button) =>
  button.addEventListener("click", () => {
    review.mode = button.dataset.mode;
    review.paused = false;
    review.jumpTime = 0;
    document
      .querySelectorAll("[data-mode]")
      .forEach((b) => b.setAttribute("aria-pressed", String(b === button)));
  }),
);
document
  .querySelector("#weapon")
  ?.addEventListener("change", (e) => (model.spear.visible = e.target.checked));
window.review = {
  model,
  camera,
  scene,
  mode: "idle",
  controls,
  jumpTime: 0,
  phase: 0.5,
  frozen: true,
  paused: false,
};
let prev = performance.now(),
  time = 0;
function advance(dt) {
  time += dt;
  const r = window.review,
    mode = r.mode;
  let air = false,
    verticalVelocity = 0;
  model.root.position.y = 0;
  if (mode === "jump") {
    r.jumpTime = (r.jumpTime + dt) % 1.45;
    const t = r.jumpTime;
    model.root.position.y = Math.max(0, 7.7 * t - 10.5 * t * t);
    air = model.root.position.y > 0.005;
    verticalVelocity = 7.7 - 21 * t;
  }
  animateWolf(model, {
    dt,
    time,
    speed:
      mode === "walk" ? 1.8 : mode === "trot" ? 3.6 : mode === "run" ? 6.8 : 0,
    air,
    verticalVelocity,
    attack: 0,
    dash: false,
  });
}
window.review.advance = advance;
function frame(now) {
  const dt = Math.min((now - prev) / 1000, 0.04);
  prev = now;
  if (!review.paused) advance(dt);
  controls.update();
  painterly.render();
  document.querySelector("#status").textContent =
    `${review.mode === "jump" ? "Jump & land" : review.mode} · wolf only`;
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

window.review.sample = (name, seconds) => {
  window.review.paused = true;
  model.mixer.stopAllAction();
  const action = model.actions[name];
  action.reset().setEffectiveWeight(1).play();
  action.time = seconds;
  model.mixer.update(0);
  model.updateDetails?.();
  painterly.render();
};

window.review.render = () => painterly.render();

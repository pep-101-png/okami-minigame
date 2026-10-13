import * as THREE from "three";
import { wolf, loadWolf } from "./wolf.js";
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
camera.position.set(-6, 2.5, -0.3);
camera.lookAt(0, 0.95, -0.75);
const painterly = createPainterlyRenderer(renderer, scene, camera),
  model = wolf();
scene.add(model.root);
window.review = {
  model,
  camera,
  scene,
  mode: "side",
  phase: 0.5,
  frozen: true,
  paused: false,
};
let prev = performance.now(),
  time = 0;
function frame(now) {
  const dt = Math.min((now - prev) / 1000, 0.04);
  prev = now;
  time += dt;
  const r = window.review;
  const mode = r.mode;
  if (!window.review.paused)
    animateWolf(model, {
      dt,
      time,
      speed: mode === "walk" ? 3 : mode === "run" ? 8 : 0,
      air: false,
      attack: mode === "sweep" || mode === "finish" ? r.phase : 0,
      dash: false,
      combo: mode === "sweep" ? 2 : 3,
    });
  painterly.render();
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

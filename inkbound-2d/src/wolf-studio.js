import "./style.css";
import { Player } from "./player.js";
import { loadPaintedArt, drawPaintedWolf } from "./painted-art.js";
await loadPaintedArt(true);
const canvas = document.querySelector("#studio"),
  c = canvas.getContext("2d"),
  p = new Player();
let mode = "Idle",
  clock = 0,
  last = performance.now();
Object.assign(p, { x: 640, y: 555 });
const names = [
  "Idle",
  "Walk",
  "Run",
  "Sprint",
  "Jump",
  "Combo",
  "Heavy",
  "Air strike",
  "Hurt",
  "Brush",
  "Defeat",
];
document.querySelector("#controls").style.cssText =
  "position:fixed;left:30px;right:30px;top:25px;text-align:center;pointer-events:auto";
document.querySelector("#modes").innerHTML = names
  .map((n) => `<button data-mode="${n}">${n}</button>`)
  .join("");
document.querySelectorAll("[data-mode]").forEach(
  (b) =>
    (b.onclick = () => {
      mode = b.dataset.mode;
      clock = 0;
    }),
);
window.wolfStudio = {
  player: p,
  get mode() {
    return mode;
  },
  setMode(n) {
    mode = n;
    clock = 0;
  },
  get clock() {
    return clock;
  },
};
function resize() {
  canvas.width = innerWidth;
  canvas.height = innerHeight;
}
resize();
window.addEventListener("resize", resize);
function frame(now) {
  let dt = Math.min((now - last) / 1000, 0.033);
  last = now;
  clock += dt;
  c.setTransform(innerWidth / 1280, 0, 0, innerHeight / 720, 0, 0);
  c.fillStyle = "#f0e6d1";
  c.fillRect(0, 0, 1280, 720);
  c.fillStyle = "#92794b20";
  c.beginPath();
  c.ellipse(640, 600, 175, 7, 0, 0, Math.PI * 2);
  c.fill();
  c.strokeStyle = "#ae9b78";
  c.lineWidth = 1;
  c.beginPath();
  c.moveTo(200, 600);
  c.lineTo(1080, 600);
  c.stroke();
  p.x = 640;
  p.y = 600;
  p.vx = { Walk: 110, Run: 285, Sprint: 440 }[mode] || 0;
  p.stride += Math.abs(p.vx) * dt * (p.vx > 340 ? 0.028 : 0.038);
  p.grounded = true;
  p.vy = 0;
  p.attack = null;
  p.hurt = 0;
  p.brush = mode === "Brush";
  p.dead = mode === "Defeat";
  p.deathTime = clock;
  if (mode === "Jump") {
    let t = clock % 1.4;
    p.y = 600 - Math.max(0, 630 * t - 825 * t * t);
    p.vy = -630 + 1650 * t;
    p.grounded = t > 0.765;
  }
  if (mode === "Combo" || mode === "Heavy" || mode === "Air strike") {
    const duration = mode === "Heavy" ? 1.05 : 0.72,
      cycle = clock % (duration + 0.22),
      combo =
        mode === "Combo" ? (Math.floor(clock / (duration + 0.22)) % 3) + 1 : 1;
    if (cycle < duration)
      p.attack = {
        kind:
          mode === "Heavy" ? "heavy" : mode === "Air strike" ? "air" : "light",
        combo,
        t: cycle,
        duration,
      };
    if (mode === "Air strike") {
      p.y = 500;
      p.grounded = false;
    }
  }
  if (mode === "Hurt") p.hurt = clock % 1.4 < 0.6 ? 1 : 0;
  c.save();
  c.translate(640, 600);
  c.scale(2, 2);
  c.translate(-640, -600);
  drawPaintedWolf(c, p, clock);
  c.restore();
  c.fillStyle = "#6c654e";
  c.font = "17px Georgia";
  c.textAlign = "center";
  c.fillText(mode, 640, 665);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

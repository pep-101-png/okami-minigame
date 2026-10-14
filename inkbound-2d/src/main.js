import "./style.css";
import { Input } from "./input.js";
import { Renderer } from "./renderer.js";
import { Game } from "./game.js";
import { loadPaintedArt, artStatus } from "./painted-art.js";
document.querySelector("#ui").innerHTML =
  '<div class="overlay"><div class="card"><h1>Preparing the ink…</h1><p>Loading painted character frames.</p></div></div>';
try {
  await loadPaintedArt();
} catch (error) {
  document.querySelector("#ui").innerHTML =
    '<div class="overlay"><div class="card"><h1>The artwork could not load.</h1><p>Refresh the page to retry. Keep the game server window open.</p><button onclick="location.reload()">RETRY</button></div></div>';
  throw error;
}
const canvas = document.querySelector("#game"),
  input = new Input(canvas),
  renderer = new Renderer(canvas),
  game = new Game(input, renderer);
window.inkbound = { game, input, renderer, artStatus };
game.deferHUD = true;
let last = performance.now(),
  accumulator = 0;
const STEP = 1 / 60;
function frame(now) {
  const elapsed = Math.min((now - last) / 1000, 0.12);
  last = now;
  accumulator += elapsed;
  let steps = 0;
  while (accumulator >= STEP && steps < 7) {
    game.update(STEP);
    accumulator -= STEP;
    steps++;
  }
  game.renderHUD();
  renderer.draw(game);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

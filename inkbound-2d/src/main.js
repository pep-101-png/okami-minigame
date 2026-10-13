import "./style.css";
import { Input } from "./input.js";
import { Renderer } from "./renderer.js";
import { Game } from "./game.js";
const canvas = document.querySelector("#game"),
  input = new Input(canvas),
  renderer = new Renderer(canvas),
  game = new Game(input, renderer);
window.inkbound = { game, input, renderer };
let last = performance.now();
function frame(now) {
  const dt = Math.min((now - last) / 1000, 0.033);
  last = now;
  game.update(dt);
  renderer.draw(game);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

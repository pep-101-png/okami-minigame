# Sunward — The Crimson Guardian

A procedural Three.js arena minigame inspired by Japanese ink painting and folklore. No external models or textures are required. Fonts have local fallbacks.

## Development

Node.js 22.12+ or 24 recommended. Run `npm ci`, then `npm run dev`. Run `npm run build` for production, and `npm run preview` to serve the build.

Enter the grove, then use WASD to move relative to the camera, mouse to look, Space to jump, and left click or J to thrust. Chain attacks within one second for a three-hit combo. The third hit deals double damage. Restore all five spirits to win; losing all vitality ends the run. Escape releases the cursor. A desktop browser with WebGL is required.

## Modules

- `src/models.js`: procedural wolf, mouth-held side-handle spear, and spirits.
- `src/world.js`: arena, obstacles, lighting, torii, lanterns, blossoms.
- `src/input.js`: keyboard and pointer-lock camera input.
- `src/game.js`: movement, gravity, collisions, combat, health, win/loss.
- `src/main.js`: rendering, follow camera, HUD, lifecycle.

All art is original procedural geometry. Runtime needs no credentials or external services.

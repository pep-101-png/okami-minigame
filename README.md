# Sunward — The Crimson Guardian

A procedural Three.js arena minigame inspired by Japanese ink painting and folklore. No external models or textures are required. All art, foliage, paper textures, and shading are generated locally; no network requests are needed during play.

## Development

Node.js 22.12+ or 24 recommended. Run `npm ci`, then `npm run dev`. Run `npm run build` for production, and `npm run preview` to serve the build.

Enter Windflower Village. Use WASD to move relative to the fixed 2.5D camera; Space jumps, Shift runs, and K dodges. Press E near a villager to talk, then E to advance or close the conversation. Four villagers live along the main street, and one walks between waypoints. Buildings and stalls have collision boundaries.

Follow the east road to the spirit grove. Left click or J chains a quick thrust, turning sweep, and lunging finisher with distinct windups, hit timing, arcs, damage, recoil, and brief impact pauses. The village is safe: spirits remain in the grove. Restore all five spirits to win, then choose Continue Exploring to keep walking around. Losing all vitality allows a restart. A desktop browser with WebGL 2 is required.

## Modules

- `src/models.js`: procedural wolf, mouth-held side-handle spear, and spirits.
- `src/world.js`: spirit grove, lighting, torii, lanterns, blossoms.
- `src/town.js`: village architecture, NPCs, conversations, routes, building colliders.
- `src/combat.js`: data-driven combo timings, arcs, damage, and lunges.
- `src/input.js`: keyboard and pointer-lock camera input.
- `src/game.js`: movement, gravity, collisions, combat, health, win/loss.
- `src/animation.js`: articulated gait, jump poses, head-led thrusts.
- `src/art.js`: toon shading, ink outlines, brush strokes, paper texture.
- `src/camera.js`: smooth follow camera and speed-based field of view.
- `src/effects.js`: ink impact and dodge particles.
- `src/rendering.js`: screen-space ink edges, grain, and vignette.
- `src/main.js`: rendering, HUD, lifecycle.

All art is original procedural geometry. Runtime needs no credentials or external services.

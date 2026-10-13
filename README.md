# Wolf-only foundation review branch

This branch opens the isolated wolf viewer rather than the town. See [screenshots and movement preview](notes/foundation/REVIEW.md). Run `npm run dev` or the existing `START-GAME.cmd` launcher to inspect the viewer locally. Build: `npm run build`. Viewer checks: `npm run test:foundation` against a running production preview on port 4173.

The playable game remains on `sunward-minigame`. The game instructions below describe that branch; its full-game test suites are not the selected workflow for this review branch.

# Sunward — The Crimson Guardian

A playable Three.js + Vite town and combat minigame inspired by Japanese painted fantasy art. Explore Windflower Village with a controlled 2.5D camera, talk to villagers, gather windflowers, restore a shrine, and cleanse the eastern spirit grove.

The wolf uses a locally included skinned model adapted from an artist-rigged, licensed canine foundation. The source is a fox adapted for this original wolf interpretation; it is not extracted from Ōkami. Its existing artist-made walk/run cycles are retained, with additional local combat, jump, dodge and landing clips. See [asset attribution](THIRD_PARTY.md).

## Run on Windows

On Windows you can double-click **START-GAME.cmd** in the extracted folder. It finds the existing portable Desktop Node download, installs missing dependencies, and starts Vite. The helper has not been run on Windows in this cloud validation; the manual commands below are the fallback.

Install Node.js 22.12+ or 24. Open a command window in this folder (the folder with `package.json`) and run:

```bat
npm ci
npm run dev
```

Open the **Local** address printed by Vite and keep the terminal open. If using the portable Node folder from this project conversation, first run:

```bat
set "PATH=C:\Users\giuse\Desktop\node-v24.21.0-win-x64;%PATH%"
```

If npm reports that esbuild's setup script is not approved, finish it with:

```bat
npm install-scripts approve esbuild
npm rebuild esbuild
npm run dev
```

## Controls and activities

- **WASD:** move relative to the fixed camera. **Shift:** run.
- **Space:** jump. **K:** directional dodge.
- **Tap left click / J:** quick thrust → turning sweep → lunging finish. Hold and release for a charged Dawn Thrust; charging longer increases its damage.
- **Tap right click / L:** Moon Arc heavy sweep. Hold and release for charged Sunbreak, a wider heavy strike with its own animation. Right click does not open the browser menu in the game canvas.
- **Left click / J while jumping:** Falling Star aerial dive.
- **B:** loud Guardian Bark, stunning nearby forward spirits for 1.65 seconds; six-second cooldown. Cover blocks the stun.
- **V:** selected vocal sound. Choose growl, soft bark, or howl from the pause menu. Damage produces a whimper.
- **E:** talk, collect a nearby windflower, or offer flowers at the northern shrine.
- **Mouse wheel:** camera zoom. **Escape:** pause. **M / sound button:** mute sound.

Talk to Hana, collect three windflowers around the village, then offer them at the northern shrine for a vitality upgrade. The village is safe. Follow the east road to the grove and restore its five restless spirits; enemies wind up their attacks and stagger when hit. You can continue exploring after victory or retry after defeat without reloading the page.

The wolf has visible amber-and-ink eyes that follow the animated face, sparse silky fur wisps, and blossoms/leaves trailing behind during running. Jumping uses separate rise, fall, and landing poses; charging while moving layers leg animation under the windup.

The local model, textures, and recorded canine vocals and original synthesized weapon/world audio need no external requests during play. Audio starts only after a player gesture. A desktop browser with WebGL 2 is required.

## Development and checks

`npm run build` creates the production build. `npm run preview -- --port 4173` serves it. In a second terminal, `npm run test:smoke` runs the browser integration suite. On a machine without installed Chromium, run `npx playwright install chromium` first. Use `npm run test:wolf` for the charged attack, bark, voice, foliage, eye, fur and aerial-attack checks. See [validation instructions](tools/VALIDATION.md).

The model adaptation can be rebuilt with Blender 4.3.2:

```sh
blender -b --python tools/adapt_wolf.py
```

The script verifies its locally included source binary's checksum before import. Blender is needed only for editing/rebuilding the model, not for playing the game.

## Modules

- `src/wolf.js`, `src/wolf-paint.js`, `src/wolf-fur.js`, `src/animation.js`: local model loading, painted atlas, skin outlines, action blending, contact-driven footfalls, face tracking, silk wisps and mouth-held spear.
- `src/wolf-abilities.js`: hold/release charges, bark stun/cooldown, vocal options, and running foliage.
- `src/combat.js`, `src/game.js`: attack windows, swept hits, input queues, dodge cancellation, movement, collision, enemy behavior and game lifecycle.
- `src/models.js`, `src/enemy.js`: articulated reed sentinels and their animation/death state.
- `src/effects.js`, `src/audio.js`: bounded painted impact/trail/death effects and original WebAudio cues.
- `src/town.js`, `src/world.js`, `src/quests.js`: village, NPCs, spirit grove, shrine and windflower activities.
- `src/art.js`, `src/rendering.js`: local pigment surface textures, toon materials, ink edges and paper grain.
- `src/input.js`, `src/camera.js`, `src/main.js`: controls, smooth fixed camera, HUD and startup.

[Development priorities](TODO.md) remain the guide for further iteration. [Build log](notes/BUILD_LOG.md) records actual revisions, interruption and validation; technical success is not a claim of artistic perfection.

Wolf revision controls remain: hold/release left click for the coiled charged pounce, right click for overhead cleaver, hold/release right click for charged ground break, click in the air for tucked spear dive/slam. B is the recorded stun bark; V plays the vocal selected in Pause. The spear has an original spectral leaf blade, animated tassels and pale attack trails. Recorded-audio licenses are listed in Credits and THIRD_PARTY.md.

Latest combat revision: tap left click/J three times to connect Reed Crosscut, Crescent Sweep and Sunward Vault. Tap right click/L twice for Sky Cleaver into Rising Tempest; the second press can be buffered during the first strike or entered within its brief recovery window. Holding/releasing either button still selects the charged attack. Eyes, vocal audio and spear artwork remain the approved versions.

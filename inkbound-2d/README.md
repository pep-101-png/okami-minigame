# Inkbound — The River Remembers

An original 2D side-scrolling divine-wolf action-adventure prototype. This is a **separate project**. It neither imports nor modifies the existing Three.js game, assets, launcher, or package files. Branch: `inkbound-2d-prototype`.

## Play on Windows

Extract the standalone ZIP into a **new folder**, then double-click **START-2D-GAME.cmd** inside `inkbound-2d`. Keep its CMD window open. It finds an installed Node.js or your portable `Desktop\node-v*-win-x64` folder, runs the included compiled game on port 5180 using only Node. **The standalone ZIP does not need npm installation.** If running a source checkout without `dist/`, the launcher instead installs this project's dependencies, checks esbuild, and starts Vite. Your old game's START-GAME.cmd still belongs to the old game.

If using CMD manually, open a terminal **in this folder**, then:

```bat
npm ci
npm run dev
```

Use Node 22.12+ or Node 24. If npm holds esbuild's setup script, the launcher attempts `npm install-scripts approve esbuild` followed by `npm rebuild esbuild`. Do not enter these commands into the Node REPL.

## Controls

| Action                      | Keyboard / mouse               | Standard controller                     |
| --------------------------- | ------------------------------ | --------------------------------------- |
| Move                        | A/D or arrows                  | Left stick                              |
| Walk / sprint               | Ctrl / Shift                   | Left shoulder for sprint                |
| Jump / unlocked double jump | Space                          | A                                       |
| Three-hit light chain       | J / left click                 | X                                       |
| Heavy attack                | L / right click                | Y                                       |
| Aerial dive / landing shock | Attack in the air              | Attack in the air                       |
| Dodge                       | K                              | B                                       |
| Brush Mode                  | B / Tab                        | Right shoulder                          |
| Draw while time is frozen   | Hold left click, draw, release | Right stick; hold/release right trigger |
| Cycle unlocked weapon       | Q; 1/2/3 selects               | Left trigger                            |
| Pause                       | Escape                         | Start                                   |
| Sound                       | M                              | Back                                    |

Controller mappings are implemented through the browser Gamepad API; a physical controller has not been tested in this cloud environment. The prototype currently requires a keyboard/mouse or controller, rather than touch controls.

## A complete first chapter

Start in the riverside hamlet and follow the bank east. Grounded movement accelerates into a run, carries momentum through jumps, supports coyote time and jump buffering, and steps up the shallow riverbanks. Sprint uses a bounding gait. Camera look-ahead, jump following, sprint pullback and boss framing keep the wolf visible.

The continuous level has terraced ledges, treasure, a river puzzle, a locked gate, a cursed grove, a breakable ancient wall and a boss shrine. Optional offerings lie on the higher terraces; the willow unlocks double jump so you can return for them. Finish by defeating the guardian and reaching the shrine at the eastern end.

1. **Circle the dead river willow's crown** to restore it. This unlocks double jump and River Beads.
2. Draw from the **blue river seal** to the **stone basin** to redirect water. The restored willow and filled basin open the river gate.
3. Release the grove's four spirits. **Slash the armoured spirit's seal** before attacking it.
4. Circle the great grove tree after its spirits are defeated. Flowers, cherry blossoms, clear water, rabbits, butterflies, falling petals and a brighter original score return. Health refills; Mountain Fang unlocks.
5. Break the ancient wall with a heavy attack or an ink bomb.
6. Face **Kurobane**, a two-phase corrupted guardian with a charge, curse volley and jumping ground shock. Cut his forehead seal to expose him; punish recovery windows and dodge the golden attack tells.
7. Walk to the eastern shrine after freeing the guardian to complete the chapter.

## Brush gestures

Brush Mode **freezes gameplay** and holds the camera still. Draw directly onto the scene; no power-selection menu. The ink meter regenerates when playing.

- **Straight line:** cut spirits; expose armoured/boss seals.
- **Closed circle/oval:** bloom valid dead tree crowns. The grove checks whether its spirits are cleared.
- **Horizontal zigzag:** gust nearby enemies, reflect projectiles, and ring the village wind chime for an offering.
- **Spiral winding inward:** create a timed ink bomb. Leave Brush Mode for its fuse to run.
- **Stroke from river seal to basin:** redirect water; straight or curved strokes between these valid endpoints work.

Recognition uses endpoint distance, stroke length, bounds and signed turns with generous target tolerance. Invalid casts explain the missing target without consuming ink. Different symbols can still be ambiguous; the river endpoints take priority for water.

## Combat / weapon differences

Light attacks buffer into a three-hit chain. Running attacks carry a lunge; aerial attacks spin into a dive and produce a landing shock. Heavy attacks have a longer windup and stronger impact. Hit-stop retains newly pressed action inputs. Dodge has a cooldown and invulnerability; damage grants protected recovery and knockback.

- **Dawn Mirror:** fast close melee; landed strikes replenish a little ink.
- **River Beads:** longer reach with a slower chain; hits pull surviving spirits toward the wolf.
- **Mountain Fang:** slower, stronger blade strikes, wider heavy reach, and wall breaking.

The enemy roster includes pursuing mask spirits, swooping moth spirits, a projectile archer, a guarded sentinel, a slow heavy spirit, and the boss. Tells, attacks, stagger and recovery are separate states.

## Art and audio

All game visuals are original local Canvas 2D paths, articulated limb geometry, washes, paper grain, particles and layered parallax. The wolf uses two-bone limb articulation, distinct grounded/airborne endpoints, attack body poses, breathing, tail motion, expressive eyes and flowing divine ribbons. This is high-resolution illustrated vector artwork with a paper treatment, **not a claim that a traditional artist painted a sprite sheet**. There are no external fonts, models, textures, Blender steps or copied Ōkami assets.

All music and effects are locally synthesized original placeholders using Web Audio. Audio starts after the Play button; M mutes it. The audio module is isolated so recordings and a composed score can replace these placeholders later.

## Organisation

`src/player.js` — movement, jump, dodge and combo state; `world.js` — level layout and runtime state; `enemies.js` — AI and hit reactions; `brush.js` — gesture recognition and powers; `wolf-art.js` — wolf drawing and articulation; `renderer.js` — world art/camera/particles; `audio.js` — original synthesized score and effects; `input.js` — keyboard, pointer and Gamepad; `game.js` — chapter loop and UI; `main.js` — bootstrap.

Runtime has **no framework dependency**; Vite is the development/build tool. Playwright is only a development test dependency.

## Build and validation

```sh
npm ci
npm run build
npm run dev
# in another terminal, same folder:
npm test
```

Tests require Chromium (`CHROMIUM_PATH` can override its location). In the cloud Chromium is `/usr/bin/chromium`. The browser tests use real keyboard/mouse events, with isolated position/enemy fixtures for focused checks. Their report distinguishes those checks from the full-route playthrough. See `review/validation.json`, `review/playthrough.json`, and `review/REVIEW.md`.

The original game's preservation is checked with a SHA-256 manifest of **every previously tracked file**, captured before this project was added. The new branch adds only files below `inkbound-2d/`.

## Prototype boundaries

This is one first-playable chapter, with synthesized placeholder sound and procedural illustrated art. It has no save-game system, dialogue quest campaign, inventory screen or additional chapters. Physical controller testing, broader browser/device testing and further human art/animation review remain. No claim of matching a commercial game's production quality is made.

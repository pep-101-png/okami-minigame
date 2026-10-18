# Sunward — The Painted Valley

A playable Three.js action RPG expansion of the existing Windflower Village game.
Explore the enlarged village, return to Amaterasu's walk-in home, buy permanent
blessings and weapons, and challenge three arena waves followed by Kurogane.
Coins, experience, purchased weapons, upgrades and divine growth persist through
victory, defeat, retreat and browser restarts.

The environmental art overhaul adds object/UV-space pigment and broken ink,
curved tiled roofs, verandas and painted wall scrolls, a nonrepeating valley atlas,
dimensional cherry/maple/pine canopies, wind-blown meadows, a brush-current river,
lotus pond, waterfalls, cliff terraces, bamboo boundaries and layered ink mountains.
The original Amaterasu GLB, all 41 clips, gameplay and save format are preserved.
The image-space edge filter is removed; surface textures and geometry carry the art.

Previous playable expansion: **sunward-before-art-overhaul** (`6f4f90a`).
Keep the previous folder if desired. Close its terminal before launching this build;
use the same browser and localhost address/port to retain existing progress.

## Play on Windows

The **Sunward-RPG.zip** play build is in `releases/` on branch
**sunward-painted-world**. Extract it, open the **Sunward-RPG** folder and double-click
**START-GAME.cmd**. It uses your existing Node installation or portable Desktop
Node folder. It opens the browser after the local server starts. Keep its CMD
window open. This build needs **no npm install and no install-script approvals**.
If the port is occupied, close the previous game terminal before starting it.

The Windows launcher is provided for Windows; its server and packaged game were
tested on Linux/Chromium. The `.cmd` itself cannot be executed in this environment.

## Develop from source

Node 22.12+ or Node 24 LTS:

```sh
npm ci
npm run dev
```

The source-project **START-GAME.cmd** remains available and handles the portable
Desktop Node installation. Build with `npm run build`. All models, textures and
audio are local; gameplay makes no external asset requests.

## Controls

- **WASD:** camera-relative jog; **Shift:** sprint; **Ctrl:** slow walk.
- **Space:** jump; a second airborne jump unlocks at movement upgrade level 2.
- **K:** stamina-based directional dodge with brief invulnerability.
- **Left click / J:** three-hit weapon combo; hold/release for charged light.
- **Right click / L:** heavy attacks; hold/release for a charged heavy.
- **Attack in the air:** downward Falling Star attack.
- **Q:** switch owned weapons. The spear retains long reach; Sundial Flame uses
  shorter circular strikes, area damage and painted fire arcs.
- **B:** bark stun, spending divine ink; **V:** selected vocal cue.
- **E:** talk, shop, rest, use the home altar, enter the eastern trial or collect
  the existing windflowers. The home has an open front entrance.
- **Middle-drag / Alt-drag:** orbit camera; **wheel:** zoom.
- **Escape:** pause / close shop; **M:** mute. Pause retains volume/voice controls.

Follow the western bridge to the market. Taro's shop is beside his tea stall.
The trial entrance is on the eastern road. Defeat Kurogane, return home and spend
your rewards. Retreat is available through the on-screen button during a run.

## Saving and permanent growth

The versioned save uses `localStorage` key `sunward.rpg.v2`, with a backup and
validation/recovery. Rewards save on each kill; purchases and equipment save
immediately. A visible warning identifies session-only play if storage is blocked.
Do not clear this site's browser data. Use the **same browser and printed address**
when returning: localhost and 127.0.0.1, or different ports, have different saves.
Cloud sync and save export/import are not implemented.

Permanent experience gives levels and vitality/damage. Shop upgrades improve
health, damage, movement, stamina, divine ink, bark/charge strength and each weapon.
Saved power gradually adds bone-attached shoulder/ankle curls and spectral brush
trails. The original wolf mesh, textures and materials are not recoloured or
reshaped; these effects are separate geometry and vanish at low power.

## Existing assets preserved

The playable Amaterasu is exported from the approved original Sketchfab wolf's
latest Blender movement project, with 25 named movement/jump/dodge Actions plus new original-rig spear, disc, charge and bark Actions. The
source `.blend` files and older game GLBs are preserved. The original game commit
is recoverable on **sunward-pre-expansion**; the RPG expansion before this art pass
is recoverable on **sunward-before-art-overhaul**. The standalone browser wolf viewer
and its pre-existing uncommitted work are not part of this expansion commit.

## Checks and remaining work

```sh
node tools/expansion/progression-test.mjs
# With the dev server running:
node tools/expansion/integration-test.mjs
```

Browser checks cover movement, jumping, stamina, home entry/rest, real shop
purchases, reload persistence, double-jump unlock, enemy tells/damage, arena sealing,
actual attack damage through all waves and both boss phases, victory, harder repeat
runs, defeat retention and progression-driven fur. The scripted wave-clear check
uses temporary invulnerability to isolate offensive/reward mechanics; separate
checks verify player damage and defeat. This is not a claim of human balance approval.

This is a substantial first playable RPG expansion, not a finished commercial game.
Remaining work includes further hand-polishing of the new rigged combat/bark
Actions, further bespoke
NPC/building art, more nuanced fur deformation, longer-run balance, broader GPU
and Windows testing, and save export/cloud sync. Enemies use simple steering,
not a navigation mesh. Some minor model/prop intersection remains possible.
See `notes/expansion/STATUS.md` for the continuation checklist.

Original model/audio attribution: [credits](public/credits.html),
[third-party notices](THIRD_PARTY.md). No copyrighted Ōkami music is included.

Art validation: `node tools/environment/check.mjs` with the dev server running.
`tools/environment/review.mjs` captures fixed camera views against the prior
packaged build on port 5180; set `ART_AFTER_ONLY=1` to inspect only the new version.
See `notes/environment/STATUS.md` for the art changes and remaining limitations.

# V3 — organic valley working milestone

Previous playable art build: `sunward-before-organic-v3` at `e3b463d`.
New branch: `sunward-organic-v3`. No merge into the old art branch or main.

## Implemented

- One physical heightfield shared by terrain, player grounding, NPCs, trees,
  instanced grass and the camera. Four curved variable-width worn routes depress
  the terrain; soil, ruts and meadow washes share one nonrepeating valley atlas.
- Winding recessed riverbed, changing cross-section, sloped banks, translucent
  shallow/deep water, downstream arc-length currents, rock foam and pooled wading
  ripples. Deep water blocks entry from either bank, including after prop contact.
  Two curved timber bridges use matching deck heights and solid handrails.
  A legacy bridge rock obstruction found during play checks was removed.
- Bevelled, slightly bowed timbers; softened plaster shells; hipped long-ridge
  curved roofs with raised tile ribs; suspended curved cloth market canopies;
  turned pottery, shaped stone lanterns and irregular joined fences. Shared washes,
  timber grain and existing broken-ink treatment carry across these shapes.
- Continuous curved cliff contour, layered mountains, mist and existing bamboo,
  replacing the four disconnected straight cliff strips.
- Home futon/pillow, screens, warm ribbed lanterns, ornate supernatural save mirror
  and six named empty shelf compartments. Bed interaction approaches, lowers on
  the original rig, loops slow breathing, restores resources and rises on wake.
  Equipped weapons are hidden while resting and restored on waking.
- Save/load mirror uses `sunward.rpg.v2`, its validation and backup. Older upgrades,
  currency, weapons and equipment migrate without resetting; collectibles,
  individual windflowers and milestones are additive. Loading invalid data leaves
  the current in-memory state intact. Future display entries use a small registry.

## Preservation and checks

`asset-preservation.json` compares actual buffer bytes against `e3b463d`: mesh
positions, indices, normals, UVs, weights, materials, packed images and all 41 old
animation tracks are unchanged. Only Sleep_Down, Sleep_Loop and Sleep_Up are added.
The approved source Blender file was opened for export and never saved or changed.
The standalone viewer and its pre-existing edits are outside this commit.

Build, geometry/depth tests, save migration tests, browser home/water interactions,
world-boundary/material checks and the existing RPG integration suite passed.
The latter checks purchases/reload, movement/double jump, enemy tells and damage,
three waves, both boss phases, victory, repeat difficulty and defeat retention.
Scripted invulnerability isolates offensive progression during wave clearing.
Reports are stored beside this file. No browser runtime errors or missing assets
were found in those scenarios.

`review/` has matching before/after PNGs with the same cameras, lens and resolution,
including normal gameplay-distance village, bridge, home and boundary views.
The browser also traversed terrain with the follow camera. Render counts include
shadow passes: see review/comparison.json. Software Chromium verifies rendering;
it cannot certify a hardware FPS target or Windows launcher compatibility.

## Precisely unfinished

- This is a substantial landscape/architecture pass, not final bespoke art for
  every object. Existing cart/waterwheel/gate/sign/shrine-detail designs remain;
  some use the improved timber factory but need individual silhouette redesign.
- The new rigged rest is functional and much lower than the first crouch reviewed,
  but the rear-leg tuck/head-on-pillow pose still deserves an anatomy/art pass.
  The original rig has no authored closed-eyelid sleep action. No appearance or
  eyelid texture changes were made to hide that limitation.
- River has stones, a visible bed and shallow ripples. Dedicated underwater plants,
  varied pebble beds, bank-impact spray and bespoke wading audio remain unfinished.
  No swimming is implemented; deeper water intentionally blocks entry.
- Locomotion follows terrain height but has no new slope-aware per-paw IK. Local
  paw gaps/intersections on uneven rocks and stronger slopes can remain.
- Remaining legacy prop intersections and handcrafted surface/detail polish need
  further human play/art review. The painterly treatment retains some visible
  repeated brush hatching. This is not declared a finished commercial art pass.
- Broader GPU performance, extended play balance and running the .cmd on Windows
  remain unverified here. Save export/cloud synchronisation remain unimplemented.

## Run

Download `releases/Sunward-RPG.zip`, extract, open Sunward-RPG and run
START-GAME.cmd. Node is required, but no npm install/install scripts are needed.
Use the same localhost port/browser as before to retain localStorage progress.

Source: npm ci; npm run dev. Build: npm run build.
Tests: tools/organic/{landform-test,save-test,interaction-test}.mjs,
tools/environment/check.mjs and tools/expansion/integration-test.mjs.

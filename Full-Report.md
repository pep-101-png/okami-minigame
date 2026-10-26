# Village Breeze — completion report

26 October 2026. This completes the screenshot's bridge, tower, breeze, petting and water scope for the **separate Unity Village demo**.

## Downloads

- [Complete separate demo — use this for a fresh folder](https://github.com/pep-101-png/okami-minigame/raw/refs/heads/prototype/village-breeze-20261026/Sunward-Village-Breeze-Complete-Demo.zip)
- [Cumulative Assets update — use this for an existing separate demo](https://github.com/pep-101-png/okami-minigame/raw/refs/heads/prototype/village-breeze-20261026/Sunward-Village-Breeze-Update.zip)
- [Machine-readable checks, sizes and SHA-256 hashes](Download-Verification.json)

These contain Unity project files. **There is no prebuilt Windows executable.**

## What was recovered

The screenshot's `/workspace/sunward-village-breeze` working directory was not present in this chat's environment. The latest published separate Village Life package was recovered from `prototype/village-life-20261026`, commit `e4da075bca0678eef6959c5c62b2da8c942af77e`, and overlaid on its original complete separate demo. The interrupted, unpublished additions were reconstructed from the screenshot's stated scope; their original uncommitted source was unavailable.

This work belongs to the separate prototype. It has no dependency on PR #14 and does not update or merge into the main `sunward-minigame` game.

## Changes completed

### Bridge

- Added stronger physical ink detail along the actual rail mesh's boundary and hard edges, excluding flat triangulation diagonals.
- Added 27 individually shaped walking planks with varied widths, clipped/worn corners, slightly varied ends, dark edge strokes and four original timber paint variations with grain and knots.
- Kept the original bridge shape, rail design, decorative finials, supports and continuous deck underneath. The four old repetitive overlay slat/ink batches were replaced.
- The replacement plank tops sit within 3 cm of the retained deck collision profile. Their widths range from approximately 17.6 to 25.9 cm.

[Before/after Blender bridge comparison](Bridge-Blender-Comparison.jpg)

### Shrine tower

- Removed the recovered tower's single incomplete projecting panel batch.
- Built five enclosed tiers with framed corners, timber bands, dark windows and latticework on all four sides.
- Added a stone footing and a continuous tapered finial reaching the original tower height.
- Retained the recovered roof mesh byte-for-byte.
- Inspected the tower in Blender and corrected an initially segmented/gapped finial before packaging.

[Before/after Blender tower comparison](Tower-Blender-Comparison.jpg)

### Village and farm breeze

- Increased the bounded active petal pool from 48 to 128.
- Doubled tree emission frequency; changed nearby walking-view emission from one every 5.5 seconds to one every 0.45 seconds.
- Added distributed emissions across the village/farm in overview as well as on foot, with stronger gentle horizontal drift.
- Retained the recovered cherry-petal artwork, falling/settling behaviour and room exclusion. Petals are also removed if their drift enters a room footprint.

These are configured rates; live appearance, transparency ordering and frame time still need Unity testing.

### Easier animal petting and quiet chime

- Increased maximum horizontal reach from 2.15 to 3.1 metres and widened the view-angle allowance.
- Raised the aim point toward the animal's upper body.
- Only named low fence colliders may be reached over. Other animals, walls, closed doors, tall obstructions and unrecognized objects continue to block the interaction. A full raycast result buffer fails closed.
- Preserved the existing E interaction, animal pause/attention and heart burst.
- Added an original 0.48-second, soft-attack, fading two-tone chime, played once per successful pet at low volume with distance attenuation. The existing pet cooldown prevents repeated triggering every frame.
- No animal vocals were invented or represented as recovered recordings.

### Water, splashes and rock-pool steam

- Added spatial variation to downstream painted-current speed and foam phase/drift while reusing the existing recovered water/wave artwork.
- Added a bounded pool for small splashes at four river bank/bridge locations.
- Added softly fading, slowly rising steam above the existing shrine-garden rock pool, using a new soft alpha texture.
- The existing water animation pause button also pauses the new splash and steam effects.
- New runtime meshes and material instances are released when their component is destroyed.

The separate demo's interface title is now **Sunward village - Village Breeze**.

## Verification performed

- Parsed the actual compressed geometry bundle after authoring: finite positions/UVs, valid triangle indices, supported mesh counts and valid new unit normals.
- Verified every geometry material reference and all material shader/texture GUID references resolve; checked for duplicate asset GUIDs.
- Byte-compared **651 original mesh batches** with the recovered Village Life package. Those batches, including the original roofs and retained bridge structure, are unchanged. Five intentionally superseded batches were removed.
- Batched the new detail geometry into eight material batches. The total world batch count changes from 656 to 659. This is not a measured GPU/frame-time result.
- Byte-compared the original collision-proxy data, stair ramps, house/door data, farm layout and animal animation bundle; all remain unchanged.
- Checked all 27 new boards against the retained deck profile and confirmed width variation and the maximum 3 cm top clearance.
- Parsed all **10 C# files** with the tree-sitter C# parser with no syntax errors. This does not resolve Unity assemblies or compile against Unity APIs.
- Checked the new chime's mono PCM data, sub-half-second duration, soft sample endpoints and absence of clipping. Listening through the Unity audio mixer/device was not possible here.
- Rendered and visually inspected before/after bridge and tower assets in Blender. Comparison files carry permanent non-Unity labels.
- Verified both ZIPs' CRCs. Reconstructed a fresh Assets tree from the original separate demo plus the cumulative update and byte-compared it with the intended final Assets tree.
- The update contains **246 changed/new asset files**, including all prior separate Village Life updates.

The latest existing Unity feedback release was retrieved and inspected. It is an older main-game capture from `aefd595771e933a3313ecb4170251764c94ab1e3`, run `20261021T092745607Z-9936e8`; all 14 clip entries report incomplete action coverage. Its 12 screenshots and 14 video contact sequences cannot validate this separate demo or the new additions.

## Verification limits

**Unity is unavailable in this environment.** Unity import/API compilation, effect shader compilation, actual petting/door occlusion, audio playback, transparent effect ordering, camera behaviour, collision feel, GPU performance and Windows building/playback are unverified. Blender's shader, lighting and texture approximation differ from Unity. No claim is made that the new motion/effects were observed in the running demo or on your PC.

## How to use the downloads

**Fresh copy:** extract the complete ZIP into a new folder separate from your main game. Add/open its `Sunward-Village-Demo` folder in Unity Hub, then press Play. The saved scene is `Assets/Demo/Scenes/VillageDemo.unity`. The existing `Build and Play Windows Demo.cmd` wrapper is included for your usual Windows build route.

**Existing separate demo:** close it and Unity; copy the update ZIP's `Assets` folder into the existing `Sunward-Village-Demo` folder, merge folders and replace files. Reopen in Unity or rebuild through your usual existing wrapper. No deletion of old assets is needed; superseded geometry is replaced inside the bundle.

Use E near an animal, Tab to switch walking/overview, and the existing water animation button to pause/resume all water effects. The title should say **Village Breeze**.

Main-game files, installed Windows tasks and syncing configuration were not changed. No paid APIs, new services or PC automation were used.

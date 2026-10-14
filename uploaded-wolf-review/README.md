# Uploaded wolf: colour and animation review

Separate asset preview; existing Sunward and Inkbound games are unchanged.

The supplied ZIP is **Amaterasu the Japanese Fox God** by **theamazingdonovan207**, not the earlier linked Amaterasu-and-Issun model. Its original licence and source files are preserved in `source/`.

The upload contains no skeleton or animations. Its body UV coordinates mostly sample the edge of the supplied texture. This first adaptation adds ivory surface colouring, red painted surface markings, eyes, a deforming skeleton and Idle/Walk clips. This is an initial animation study, not a finished game-ready combat rig. Foot planting, full skin-weight cleanup, and further animations remain.

- `colored-preview.png`: actual model render.
- `walk-preview.gif`: actual rendered walk loop.
- `colored-rigged.glb`: model with skin and Idle/Walk animations.
- `colored-rigged.blend`: editable model, skeleton and preview scene.
- `color_rig.py`: generation script. Requires Blender 4.3. Run `blender -b --python uploaded-wolf-review/color_rig.py` from the repository root.

Attribution: This work is based on "Amaterasu the Japanese Fox God" (https://sketchfab.com/3d-models/amaterasu-the-japanese-fox-god-6d64c6b79c0942a086cad6d988e35712) by theamazingdonovan207 (https://sketchfab.com/theamazingdonovan207) licensed under CC-BY-4.0 (https://creativecommons.org/licenses/by/4.0/). Adaptation adds colours, markings, eyes, rig and animation.

## Paint refinement

The upper eye placement replaces the earlier cheek-level eyes. The coat now has warm ivory upper planes, cooler grey underfur, uneven tonal variation and fine directional grain. Red markings are tapered painted masks, rather than raised ribbons: brow/eye/cheek strokes, a broad shoulder spiral, returning flank flames and paw marks.

`fur-tones.png` is the baked coat atlas embedded in the GLB, so the colour treatment survives export. `vermilion-markings.png` is the editable projected paint mask. Blender also includes a subtle procedural fur bump; that bump is not exported. `face-detail.png` provides a closer view; regenerate it with `blender -b --python uploaded-wolf-review/render_detail.py`.

References: the user-supplied Ōkami/Shiranui illustrations and the uploaded model's painted source textures. Live access to the Ōkami reference wiki was blocked during this pass.

## Face and gait rebuild

Based on the additional user-supplied side-view artwork and in-game reference:

- Removed the separate spherical nose and eye objects. The original muzzle tip is pigmented; the narrow ink eyes are part of the baked coat texture.
- Replaced parallel flank stripes with a chest flame, shoulder spiral and a single pointed flank sweep.
- Added separate upper-leg, lower-leg and paw joints, with calibrated IK, level paws during stance, and four staggered contact/recovery phases.
- Tail vertices and the tail ornament no longer inherit rear-leg weights.
- Baked evaluated joint motion into Idle/Walk clips and verified contact ankle height in the reimported GLB. These are in-place loops; movement integration must match ground speed.
- Blender preview uses black ink contours. The GLB includes coat colours, markings, skin weights and baked joint clips; game-side outlines still require a renderer setup.

The current model remains isolated from both games.

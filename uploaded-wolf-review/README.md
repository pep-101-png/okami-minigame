# Uploaded wolf: colour and animation review

Separate asset preview; existing Sunward and Inkbound games are unchanged.

The supplied ZIP is **Amaterasu the Japanese Fox God** by **theamazingdonovan207**, not the earlier linked Amaterasu-and-Issun model. Its original licence and source files are preserved in `source/`.

The upload contains no skeleton or animations. Its body UV coordinates mostly sample the edge of the supplied texture. This first adaptation adds ivory surface colouring, red surface-fitted markings, eyes, a deforming skeleton and Idle/Walk clips. This is an initial animation study, not a finished game-ready combat rig. Foot planting, full skin-weight cleanup, and further animations remain.

- `colored-preview.png`: actual model render.
- `walk-preview.gif`: actual rendered walk loop.
- `colored-rigged.glb`: model with skin and Idle/Walk animations.
- `colored-rigged.blend`: editable model, skeleton and preview scene.
- `color_rig.py`: generation script. Requires Blender 4.3. Run `blender -b --python uploaded-wolf-review/color_rig.py` from the repository root.

Attribution: This work is based on "Amaterasu the Japanese Fox God" (https://sketchfab.com/3d-models/amaterasu-the-japanese-fox-god-6d64c6b79c0942a086cad6d988e35712) by theamazingdonovan207 (https://sketchfab.com/theamazingdonovan207) licensed under CC-BY-4.0 (https://creativecommons.org/licenses/by/4.0/). Adaptation adds colours, markings, eyes, rig and animation.

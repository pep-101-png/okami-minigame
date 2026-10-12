# Asset attribution

## Animated canine foundation

The Sunward wolf is an adaptation of the **Fox** asset distributed in the Khronos Group glTF Sample Assets repository. It is an original wolf interpretation based on a fox source, not a model extracted from Ōkami.

Source: https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/Fox

- **PixelMannen**, model, 2014: Creative Commons Zero 1.0 Universal (CC0).
- **tomkranis**, rigging and animation, 2014: Creative Commons Attribution 4.0 International (CC BY 4.0).
- **AsoboStudio and scurest**, glTF conversion, 2017: Creative Commons Attribution 4.0 International (CC BY 4.0).

License texts:

- https://creativecommons.org/publicdomain/zero/1.0/legalcode
- https://creativecommons.org/licenses/by/4.0/legalcode

Changes made for Sunward: adjusted torso/ear/tail proportions; ivory watercolor atlas and vermilion markings; toon materials; local mouth-held side-handle spear; animation blending and steering; additional combat/jump/dodge/landing clips. The source Walk, Run and Survey (renamed Idle) cycles are retained with their existing artist-made rig. Modified files are distributed under the source's attribution terms where applicable. Attribution does not imply endorsement.

The reproducible adaptation script and original source binary are in `tools/adapt_wolf.py` and `tools/source/fox-reference.glb`. The script verifies the binary's SHA-256 before importing it. The adapted file is `public/models/sunward-wolf.glb`.

All town geometry, painted procedural surface textures, enemy geometry, UI, effects, and synthesized sound cues are original project content. No commercial Ōkami assets are included.

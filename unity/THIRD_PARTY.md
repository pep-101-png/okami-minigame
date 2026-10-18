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

## Recorded canine audio (wolf revision)

`public/audio/bark.ogg` is a cropped, faded, loudness-normalized excerpt of `4-182395-A-0.wav` from the ESC-10 subset of [ESC-50](https://github.com/karolpiczak/ESC-50). Original recording **Big_dog_bark_01.aiff**, **pgonsilva**, [Freesound 182395](https://freesound.org/people/pgonsilva/sounds/182395/), CC BY; ESC-10 is distributed under [CC BY 3.0](https://creativecommons.org/licenses/by/3.0/). The unmodified dataset excerpt is retained in `tools/source/audio/big-dog.wav`. Source attribution is preserved in `tools/source/audio/ATTRIBUTION.md`. These are recorded dog vocals, not original synthesized vocals or recordings from Ōkami.

The unmodified `wolf-growl-1.ogg`, `wolf-growl-2.ogg`, `wolf-hit-1.ogg`, and `wolf-hit-2.ogg`, plus `wolf-howl.ogg` (renamed from `wolf-die-3.ogg`), come from [Battle for Wesnoth](https://github.com/wesnoth/wesnoth/tree/master/data/core/sounds). **Lari Nieminen (zookeeper)**, GNU GPL v2 or later, per the upstream `copyrights.csv`. The GPL applies to these separately distributed audio assets; its text is included at `public/licenses/wesnoth-audio-GPL-2.txt`. Original Ogg audio is included without content modifications; the game varies playback gain/rate. The howl cue uses a wolf cry recording from that pack. Source filenames and checksums are recorded in the audio attribution file. Attribution does not imply endorsement.

## Wolf foundation review branch

The visible coat on `wolf-foundation-review` is a newly generated connected anatomical mesh (`tools/sculpt_wolf.py`), using the attributed Fox mesh as a nearest-surface skin-weight reference. The attributed canine rig and original Walk/Run clips remain the foundation, extended with two scapula controls and a weighted mane control. The additional idle and retimed diagonal trot are project modifications. Source author/license attribution above continues to apply to the reused rig/animation and their derivatives.

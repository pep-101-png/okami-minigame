# Amaterasu — Jumping and dodging milestone

Open **Amaterasu-Movement.blend** in **Blender 4.3+**, then press **Space**.
The file opens in **03 · Jump and dodge showcase**: fourteen labelled scenarios
cover the new Actions and their movement transitions. The previous movement
showcase is retained. Textures are packed; no add-ons or script trust are needed.

## New Actions

- `Jump_Standing`, `Jump_Walk`, `Jump_Jog`, `Jump_Sprint`.
- `Jump_Double`: airborne tuck/twist and a second upward arc.
- `Air_Fall`: reusable airborne loop.
- `Land_Soft`, `Land_Heavy`: separate fore/hind contact and impact recovery.
- `Dodge_Left`, `Dodge_Right`, `Dodge_Back`, `Dodge_Forward`.
- `Dodge_Walk`, `Dodge_Jog`, `Dodge_Sprint`.

Actions include phase markers and gait/phase metadata. Jump/dodge one-shots carry
root motion; the showcase uses an independent root trajectory, native NLA
crossfades and a reduced additive contact correction. Its character instances
share the original mesh/armature data. Wind uses the preserved original effect.

Choose **01 · Action inspection**, select **WOLF_RIG**, and use the lower Action
Editor dropdown to play an individual Action. See [OPEN-IN-BLENDER.txt](OPEN-IN-BLENDER.txt)
(or embedded text **JUMP & DODGE — START HERE**) for phase/export instructions.

## Preservation and review

The completed movement checkpoint is retained unchanged at
`../original-wolf-movement-system/Amaterasu-Movement.blend` and on branch
`amaterasu-movement-system`. Original mesh/UVs/normals, materials, textures,
weights, rest rig and all 24 previous Actions are checked against that file.
No game or browser-viewer files are changed.

The checks evaluate the actual skinned paws and constrained leg joints, including
quarter-frame samples and the full NLA demonstration. Review contact sheets
show side/rear poses and the demonstration. Artistic approval remains with the
user; test results are not a claim of perfect animation.

These are authored, fixed-trajectory motions. Later game integration needs
root-motion handling, terrain collision/landing selection and runtime blending.
Changing showcase timing requires rebaking its contact correction. A 60 FPS
scene timebase does not guarantee 60 drawn FPS on every GPU.

## Authoring pipeline

`author.py` reads the protected movement checkpoint and writes the new Actions.
Save that result as `review/authored-checkpoint.blend`, then run `demo.py` once
on it; running demo.py on an already assembled delivery duplicates helpers.
After demo.py, run `polish_contacts.py` for sparse subframe clearance fixes, then
finalise.py and refine_transitions.py.
`refine_transitions.py` aligns phases across the NLA overlaps and rebakes support.
`finalise.py` sets the opening scene, camera framing and embedded guide.
`validate.py` checks preservation, subframe reach and the full demonstration.
`render_actions.py`, `render_demo.py` and `sheets.py` produce review media.
`package.py` creates the ZIP and checksums after final validation.

Original asset attribution and licence: [LICENSE-SOURCE.txt](LICENSE-SOURCE.txt).

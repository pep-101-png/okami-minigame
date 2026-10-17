# Amaterasu — Idle, Walk and Run

Open **Amaterasu-Idle-Walk-Run.blend** in Blender **4.3 or newer**.
All original textures are packed. No add-ons, downloads or linked texture folders
are needed.

## Select and play an animation

1. Open the `.blend` with **File → Open**.
2. The project opens with `WOLF_RIG` selected in Pose Mode.
3. In the **Action Editor** below the 3D view, use the Action-name dropdown to
   select **IDLE**, **WALK** or **RUN**. Walk is selected initially.
4. Put the mouse over the 3D view or Timeline and press **Space** to play/pause.
5. Use **Z → Material Preview** if the original paint is not visible.

For a clean preview, turn off **Viewport Overlays** using the overlapping-circles
icon in the 3D view; turn them back on when posing controls.

You do **not** need to change the playback range when switching Actions. The
shared 720-frame review range contains complete repeats of all three loops.
The individual Actions retain their own shorter ranges for export. Expand the
Action Editor by dragging its upper border if you want more room for keyframes.

| Action | Cycle at 60 fps | Motion |
| --- | --- | --- |
| IDLE | 240 frames / 4 seconds | Breathing, small weight shifts, gentle gaze and tail motion; planted paws. |
| WALK | 72 frames / 1.2 seconds | Four distinct footfalls, planted stance, low paw recovery, shoulder and body counter-motion. |
| RUN | 40 frames / 0.667 seconds | Gallop with collected and extended flight phases, spine flexion, paw recovery and a streaming tail. |

The final key at cycle length + 1 duplicates the first key. Cycles modifiers
repeat the curves. All three Actions have fake users so Blender retains them.
Keys are on the existing animator controls; the original rig remains editable.
The text block **PLAY ANIMATIONS — START HERE** contains the same playback guide.

## Preservation and the necessary deformation fix

The approved unanimated rig remains recoverable in
[`original-sketchfab-rig`](https://github.com/pep-101-png/okami-minigame/tree/original-sketchfab-rig/original-wolf-rig).
Its `.blend` is unchanged. This animation file is a separate copy.

The original base vertices, faces, UVs, split normals, weights, rest bones,
hierarchy, controls, materials and packed texture bytes are preserved.
Nothing from the later modified wolves was transferred.

Galloping exposed folding in the original sparse joint faces. Two editable
**SIMPLE subdivision** modifiers before the existing armature add bend resolution
to the painted body and matching ink shell. SIMPLE subdivision does not smooth,
sculpt or round off the original resting surface. The face, curls and original
paint remain intact. The modifiers are unapplied in the delivered project.
The stronger poses were also moderated to avoid excessive hip compression and
overextended forelegs. No rig rebuild or new bones were needed.

## Future export

These are **in-place** Actions. Match travel speed to approximately **1.667 Blender
units/second** for Walk and **7.2** for Run, scaling model and velocity together.
Matching travel to stride speed avoids sliding during ground contact.

On a disposable export copy, clear the pose and apply the two SIMPLE subdivision
modifiers before exporting. Keep the armature. Export the three named Actions
with sampled/baked constraints and deform bones. Use each Action's own range,
not the 720-frame review range. A standard Blender glTF export was checked to
contain all three clips, their correct durations and ten skinned original parts.
Blender's volume-preserving skinning and a game's linear skinning can differ, so
the final engine appearance still needs its own visual check when game work resumes.

The game and browser viewer were neither modified nor tested. This delivery
contains no other animation types or comparison pages.

## Attribution

Based on **“Amaterasu the Japanese Fox God”** by
[theamazingdonovan207](https://sketchfab.com/theamazingdonovan207),
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
[Original source](https://sketchfab.com/3d-models/amaterasu-the-japanese-fox-god-6d64c6b79c0942a086cad6d988e35712).
Additions: separate rigged copy and the three locomotion Actions; non-smoothing
deformation resolution. Original visual design and paint retained.

# Wolf art and locomotion rebuild

An isolated derivative of the uploaded model. Inkbound and all earlier review branches are preserved. This branch integrates the derivative into Sunward; the former Sunward wolf asset and adapter remain available in source history.

This pass reworks the surface and rig, rather than adjusting only render parameters:

- Softened neck ruff and lowered the original shoulder spike, closed the snarling jaw, reshaped the coarse tail into a fuller curl, and cleaned up its root.
- Repaired split seams and oriented closed geometry before exact fusion. The voxel-fusion experiments were rejected.
- Redesigned face/chest/flank/leg paint and added fine ornamental ink scrolls. Eyes and nose are painted onto the existing surface.
- Reserved 42% of the coat atlas for the head, with an 8192px colour atlas and a portable tangent normal map for fur grain.
- Added independent hips, chest and neck articulation, plus a two-joint tail.
- Rebuilt the four-beat walk with over twice the former foreleg stride, longer reach, deeper elbow/hock bending, eased paw recovery and separately controlled soles. It remains an in-place studio loop; game movement must match its ground speed.

## Review files

The earlier milestone images `review/final-body.png`, `review/face.png`, `review/profile.png`, `review/before-after.png`, `review/walking.gif` and `review/walking.mp4` are actual model renders. `wolf.glb` contains the coat, rig and baked Idle/Walk/Run and action clips; `wolf.blend` is the editable authoring/presentation scene. Blender uses ink contours; game-side outlines still require renderer integration. Sunward loads `public/models/divine-wolf.glb` through `src/divine-wolf.js`; the untouched former adapter is `src/wolf.js`.

## Internal revisions

Nine internal passes were built and reviewed: separate mane layers; a connected ruff and lifted stock tail; voxel fusion; overlay cleanup; seam/normal repair; exact fusion; tail/paint refinement; final texture/animation rendering; and a tangent-normal seam correction. The disconnected, fragmented and overly flat variants were rejected. Only the selected final renders are published; draft screenshots are ignored.

## Reproduce and validate

These commands are for asset authoring with Blender 4.3 (Pillow and NumPy available in its Python), not for playing either game:

```sh
WOLF_DRAFT=0 WOLF_REVISION=final blender -b -t 6 --python wolf-art-rebuild/build.py
blender -b --python wolf-art-rebuild/add_secondary_motion.py
blender -b --python wolf-art-rebuild/validate.py
blender -b --python wolf-art-rebuild/render_review.py
```

Validation reimports the exported GLB and checks body volume, embedded assets, joint articulation, stance ankle height, animation clips and loop closure. `review/validation.json` records the final result.

## Attribution

This work is based on "Amaterasu the Japanese Fox God" (https://sketchfab.com/3d-models/amaterasu-the-japanese-fox-god-6d64c6b79c0942a086cad6d988e35712) by theamazingdonovan207 (https://sketchfab.com/theamazingdonovan207), licensed under CC-BY-4.0 (https://creativecommons.org/licenses/by/4.0/). Original uploaded files and licence are preserved in `source/`. This derivative changes geometry, materials, paint, rigging and animation. Visual references were the user's supplied Ōkami/Shiranui artwork and gameplay images.

## Flowing fur and combat integration

Eight weighted fur controls deform the existing neck, shoulder, foreleg and hindleg ornaments; they do not add detached particle streamers. Tail posture blends between gravity at rest, light walking sway and a higher trailing running pose. Walk and run have independently authored contacts, with ankle drift checked on the exported rig. Eighteen new action clips cover light combos, heavy return, charged attacks, aerial slam, jump/landing, dodge, charge and voice poses. Gameplay attack windows are faster while retaining hit-stop and input buffering.

The development browser test checks all eight attack poses for finite transforms, changing head/body positions and weapon clearance above the floor. The normal smoke suite exercises the complete playable town and combat loop.

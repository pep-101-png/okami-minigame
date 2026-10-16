# Jaw and face repair — pending user review

Browser comparison: https://pep-101-png.github.io/okami-minigame/compare.html?study=jaw

Individual review model: https://pep-101-png.github.io/okami-minigame/?version=jaw-repair

The left pane is the preceding, unapproved head study; the right is this separate candidate. Both use the same cameras, lighting and animation phase. Choose Painted or Neutral geometry, a close-up angle and any of the 22 original clips. The original default head study remains available; this does not replace an accepted model.

## Diagnosis and actual mesh repair

The lower cheek had a genuine transverse tunnel, not a missing boundary edge. Its connected, consistently oriented wall made an ordinary manifold-edge check pass. Side-directed rays identified an enclosed opening around native Y −3.86, Z 4.16. It was inherited from the source topology and survived the preceding sculpt. The previous validation was insufficient.

Removed 144 internal tunnel-wall triangles and joined 24 closure triangles to the existing cheek borders. Faired the surrounding skin and recomputed its normals. No native vertices were added. The GLTF has 28 additional UV seam vertices with identical positions and skin bindings; these are normal export seams on the connected surface, not separate patch objects. Their small UV islands contain matching ivory pigment and neutral tangent normals. The review skin uses front-face rendering, so double-sided rendering cannot hide a broken cheek.

## Facial changes

Lowered the supraorbital forehead and reduced its convexity. Moved the orbital skin approximately 0.09 native units toward the muzzle and 0.045 downward, carrying the established almond eyes and red framing with it. Refined the bed and rim, and limited the cheek-envelope adjustment after a stronger private candidate introduced intersections and was rejected. Shortened the extreme upper-muzzle tip slightly and lifted/flattened the lower chin while retaining the preceding mandible extension.

The approved neck, body, ornamental shoulder/ankle fur, tail, rig, all three skin bindings and all animation samples are preserved. This work does not modify or test the game.

## Validation and actual visual inspection

- No rest-pose nonadjacent facial-triangle intersections in the final native mesh; no local sculpt map inversions.
- 651 rays across the repaired aperture intersect skin on both sides.
- The 24 joined cheek faces remain non-degenerate and outward-facing in 32 phases of each of 22 clips (704 poses).
- Idle, Walk and Run checked at 96 phases each; four transitions sampled at 120 Hz. Protected body/neck probe discrepancy is below 0.00000004 world units.
- Inspected 88 actual Three.js frames: both sides of all 22 clips in painted and single-sided neutral shading at phase 0.45. These are shown in the six contact sheets. Also inspected 15 matched close-up before/after screenshots (Idle/Walk/Run × five angles).
- Production build succeeds. Browser checks cover matching cameras/lights, texture loading, material inspection, animation playback, orbit/zoom and rollback routes.

Visual limits: a shallow fold remains at the mouth corner, most evident under neutral lighting and in mouth-opening poses. This is not a through-hole. Eye expression, forehead balance and lip-corner shading still require the user's visual judgement. Existing mouth-opening animation style was deliberately not redesigned.

## Rollback and authoring

Approved neck: `?version=neck-approved`, immutable tag `wolf-neck-approved-2026-10-16`.
Previous head: `?version=head-study`, immutable tag `wolf-head-study-2026-10-16`.
Original accepted baseline: `?version=baseline-2ba1f2b`, immutable tag `wolf-original-baseline-2ba1f2b`.

The preserved native source is in `authoring/checkpoints/head-study/`. The new native study and companion corrective arrays are in `review/drafts/jaw-repair/`. The public review GLB is `public/models/jaw-repair.glb`; the existing `wolf.blend`, `head-surface.npz`, `wolf.glb`, neck checkpoint and accepted baseline were not replaced.

From the repository root, author with `blender -b -t 2 --python wolf-viewer/authoring/repair_jaw.py`, audit with `python wolf-viewer/authoring/validate_jaw_asset.py` and `blender -b -t 2 --python wolf-viewer/authoring/validate_jaw_native.py`, then build only the viewer with `npm run build --prefix wolf-viewer`. Visual review is also required; these checks do not establish acceptance.

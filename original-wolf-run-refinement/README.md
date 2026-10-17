# Amaterasu — refined Run

Open **Amaterasu-Run-Refined.blend** in Blender 4.3 or newer. Select
**RUN_REFINED** in the lower Action Editor and press **Space**.
See [OPEN-IN-BLENDER.txt](OPEN-IN-BLENDER.txt) for playback and export details.

The new Action retains **IDLE**, **WALK**, and the previous **RUN** unchanged.
The original animation project remains untouched on its original branch.
All source textures are packed; no add-ons are required.

## Diagnosis and repair

The rear-leg problem was a recovery-trajectory problem, rather than a pole flip:
the old IK targets overfolded the knees and raised them above the hip sockets,
collapsing the thigh/hip skin and its existing inward ink outline.
The revised recovery arc keeps the knees below the sockets and reduces excessive
joint compression. Contact trajectories retain their original travel speed.
No new bones, reweighting, remodeling, material changes or topology edits were needed.
Some inner-joint creasing remains at deep flexion; the revision does not claim
perfect skinning or replace the original weights.

The new gallop has coordinated pelvis tuck, lumbar rounding/extension, thoracic
counter-motion, staggered shoulder motion, forelimb landing compression,
stabilised gaze, and delayed neck/ear/tail motion. Periodic curve tangents match
at the loop boundary. It is a separate Action, not a replacement for RUN.

## Checks

`review/preservation.json` compares the source and delivered base meshes, UVs,
normals, weights, rest skeleton, materials, packed textures, original Action
curves and 18 evaluated old-animation poses.
`review/contacts.json` checks fractional-frame contacts and loop velocities.
The evaluated review checks IK, joint rotation continuity, bend limits and
full-mesh loop closure. Side and true rear frames are rendered for visual review.
Review results and previews are included alongside the downloadable project.

The project is an animation study for review, not an approval of this motion.
No actual game, browser viewer or other animation development is included.
The source model attribution and licence remain in LICENSE-SOURCE.txt.

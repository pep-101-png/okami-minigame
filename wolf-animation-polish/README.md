# Sunward · wolf animation polish

This is a separate wolf-only viewer. Sunward, Inkbound and the preceding viewer are unchanged. Extract this ZIP into a **new folder**, then double-click **START-VIEWER.cmd**. Node.js is required; the browser opens automatically. Keep the terminal open.

All 22 existing clips are selectable. Pause, scrub, slow playback, orbit, zoom, display the skeleton, and inspect side/front/three-quarter views. **Face** gives a closer frontal view for the eyes and painted markings.

## This review

- Idle animation and displayed skin bindings are preserved exactly. The browser test compares approved original vertices at four phases and reports zero positional difference.
- Walking has roughly half the earlier swing clearance and less paw curl.
- Continuous limb weights replace the boundaries that stretched ankle-fur edges almost 100 times during the old run. The running gait is retained with safer recovery and torso ranges.
- Jump starts with a squat. The head and shoulders lead, the front feet lift, then the body follows. Forelegs reach for landing, and the landing recovers to standing. Jump Rise/Fall and Land share these mechanics.
- Air Strike travels downward with a downward-facing head and forepaw-led impact compression.
- Bark lowers and braces the body and opens the existing lower lip with a jaw hinge.
- Remaining attack clips are deferred, as requested. Their authoring poses were not rewritten.
- The red spiral sits on the body; a baked surface mask excludes shoulder ornaments. Eyes are fitted to actual cheek surfaces, with surrounding red ink, a central forehead seal and faint grey brows.
- Neck, shoulder and ankle fur have sixteen additional weighted flow/tip joints. The tail has seven joints with delayed tip motion and additional vertices on its existing surface. The approved body rest shape is retained.

Ten distinct exports and review notes are recorded in `review/ten-revisions.json`. The final browser test checks the actual exported asset and viewer, including preserved idle, lower walking clearance, phased takeoff, downward slam, jaw opening, deformation bounds, fur/tail weights and controls. Intermediate drafts are retained locally and excluded from the download.

## Development

`npm ci`, `npm run dev`, `npm run build`, `npm run preview`. The launcher also finds portable Node folders on your Desktop and repairs a held esbuild installation script when needed.

Authoring uses Blender 4.3 with Pillow and NumPy. From the repository root, set WOLF_PASS from 1 through 10 and run `blender -b -t 6 --python wolf-animation-polish/authoring/revise.py`. The preceding approved scene is the preserved baseline. `authoring/wolf.blend` is the editable new scene.

Keep `src/idle-binding.js` when integrating this asset elsewhere: it blends approved idle bindings into the repaired movement bindings. Studio jump/air clips contain vertical root movement; game physics integration should use the authored poses while avoiding a duplicate height trajectory.

Browser test from repository root: `WOLF_POLISH_URL=http://127.0.0.1:5238 node tools/wolf-polish-test.mjs`.

Attribution: derivative of “Amaterasu the Japanese Fox God” by theamazingdonovan207, CC BY 4.0. See `public/credits.html` and the included licence.

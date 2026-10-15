# Sunward · Run repair R1

Extract into a new folder and double-click **START-VIEWER.cmd**. The viewer opens on **Run**. Its footer links to a synchronized before/after comparison with a shared stride slider and side/rear cameras. Node.js is required. Keep the terminal open.

## What changed

- Removed the detached ten-vertex rear plate under the tail.
- Reworked hip/thigh skin weights and added local topology across the bending surface.
- Revised run recovery to keep the thigh from folding deeply into the belly; the moving ground matches the shorter stride.
- Added 24 run-only corrective surface poses, rather than more bones. The ink outline shares these corrections.
- Preserved the approved idle and walk motion using separate embedded bindings. Other animation clips, including jump and bark, retain their previous motion. Existing games and viewers are unchanged.

These repairs substantially reduce the detected hip folds; they do not prove that every possible intersection has been eliminated. The review reports distinguish reductions from complete removal. This is a wolf-only review, not a new full-game build.

## Verification and authoring

`npm ci`, `npm run dev`, `npm run build`. All 22 clips are available. The comparison is also emitted in the production build. `review/browser-validation.json` records checks of the exported GLB, including actual folded area, preserved motion, removed plate, loop closure and corrective reset when changing clips.

The source model remains in `authoring/wolf.blend`, including the 24 corrective shape keys and the companion “Run surface correctives” action. In Blender, activate that companion shape-key action alongside the rig's Run action to inspect the corrected run. The GLB combines these automatically.

From the full repository, rebuild with these Blender scripts in order: `authoring/repair.py`, `authoring/run_motion.py`, `authoring/correct_surface.py`, `authoring/export_correctives.py`, using this folder's full relative path for each. Blender, NumPy and Pillow are authoring tools only; the viewer does not need them. The preserved prior source projects supply the baseline. Local intermediate files are under ignored `review/drafts`.

Keep `src/idle-binding.js` and the shared outline morph influences when integrating. Root-height jump clips need to be coordinated with game physics.

Model derivative: “Amaterasu the Japanese Fox God” by theamazingdonovan207, CC BY 4.0. See the included credits and licence.

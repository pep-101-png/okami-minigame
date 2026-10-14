# Sunward · full-tail motion refinement

A separate wolf-only viewer. Existing games and previous viewers remain untouched.
Extract into a new folder and double-click **START-VIEWER.cmd**. Keep its terminal open.

This revision adds eight weighted controls across all four tail segments (twelve tail joints total), four distributed back controls, targeted high-strain seam repairs, a higher front-led jump, a wider/lower bark stance with a stronger jaw opening, and deeper cool underfur with warm ivory highlights. The approved idle bindings remain exact; walking gait keys and foot timing are retained. All 22 existing clips remain selectable; the deferred attack clips have not been redesigned.

Use animation selection, pause, scrub, speed, camera views and skeleton display to inspect motion.

Development: `npm ci`, `npm run dev`, `npm run build`. Authoring needs Blender, Pillow and NumPy; the viewer needs only Node. The native scene is `authoring/wolf.blend`. In the full repository, rebuild with `WOLF_PASS=10 blender -b -t 4 --python wolf-motion-refinement/authoring/revise.py`. Preserved source projects provide the authoring baseline. Keep `src/idle-binding.js` when integrating the asset.

Jump clips include root height; do not add that trajectory twice through game physics.

Model: derivative of “Amaterasu the Japanese Fox God” by theamazingdonovan207, CC BY 4.0; attribution and licence included.

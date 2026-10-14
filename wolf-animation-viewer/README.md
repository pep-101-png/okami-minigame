# Sunward wolf animation viewer

This is a separate model viewer. It does not replace or modify Sunward or Inkbound. The approved rest-mesh anatomy is unchanged.

Extract the viewer ZIP into a new folder. Double-click **START-VIEWER.cmd**. The browser opens automatically; keep the terminal open. Node.js is required. The launcher also finds portable Node on your Desktop and repairs held esbuild installation scripts when needed.

Select any of the 22 current animations. Walking/running use moving ground matched to actual planted-paw speed. You can pause, slow playback, scrub, inspect from side/front/three-quarter views, orbit, zoom, and display the skeleton. Jump is a complete takeoff/flight/landing cycle; Jump Rise/Fall and Land remain available as individual clips.

Ten distinct cumulative exports were produced and recorded in `review/ten-revisions.json`. Intermediate models are kept locally; only the final model is distributed. Browser tests check the final exported GLB, foot speed, loops, tail motion, all eight fur controls and viewer controls.

The supplied YouTube reference was inaccessible in this cloud environment. This pass uses canine four-beat walking and paired gallop mechanics; it is not a frame-traced reproduction of that video. Visual references for eye/paint placement were the supplied Ōkami artwork.

Authoring requires Blender 4.3, Pillow and NumPy. From the repository root, set WOLF_PASS from 1 through 10 and run `blender -b -t 6 --python wolf-animation-viewer/authoring/revise.py`. Existing approved scene `wolf-art-rebuild/wolf.blend` supplies the preserved mesh; the final editable scene is `authoring/wolf.blend`.

For the web viewer: `npm ci`, then `npm run dev`. Production: `npm run build`, then `npm run preview`. Root-repository browser validation: `WOLF_VIEWER_URL=http://127.0.0.1:5192 node tools/wolf-viewer-test.mjs`.

Model attribution: derivative of “Amaterasu the Japanese Fox God” by theamazingdonovan207, CC BY 4.0. See `public/credits.html` and `public/licenses/uploaded-wolf-CC-BY-4.txt`.

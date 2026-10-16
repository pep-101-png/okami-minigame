# Sunward wolf viewer

**Permanent download name: sunward-wolf-viewer.zip. Permanent extracted folder: sunward-wolf-viewer.** Future updates replace this viewer using the same names and link. Close its old CMD window before replacing the files. Existing Sunward and Inkbound games are separate and unchanged.

Double-click **START-VIEWER.cmd**. Keep the terminal open. The footer opens a synchronized comparison with the previous build; choose Idle, Walk or Run, and inspect side, rear or tail-close-up views. The visible revision label is **Tail & run 02**. All 22 existing clips remain available.

## Tail and run revision

The tail uses a continuous weighted chain driven by passive inertia, gravity and air drag. It hangs at idle, trails mildly at walking speed, and lifts progressively under running airflow. The tip responds later than the base. It has no keyed sine-wave curl. This runs in every animation, including transitions. Pause freezes it; scrubbing reconstructs a settled pose.

The run was rebuilt after studying the user-supplied side-view dog GIF: gathered suspension, hind support and push, extended suspension, then front support. The torso compresses and lengthens, the lumbar back arches, shoulders glide with support, and a lower running neck/head carriage counteracts torso pitch. Stance feet retain their ground travel. Idle and walking body motion are retained; their tails deliberately change. Other attack, jump and bark poses are not redesigned in this revision.

Run-only corrective shapes protect the bending skin. The ink outline shares the same corrections. These are not substitutes for visual review; the review folder contains actual rendered comparisons and validation reports.

## Development and authoring

`npm ci`, `npm run dev`, `npm run build`. The production build includes both viewer and comparison pages.

The browser viewer requires no Blender. The local GLB embeds its textures. For integration, keep **src/tail-dynamics.js**, **src/fur-dynamics.js**, **src/ink-outlines.js**, the retained bindings module and shared outline morph influences. Tail physics is realtime; importing the GLB alone into another viewer will not reproduce that motion.

The native scene is **authoring/wolf.blend**. Run surface correctives are a companion shape-key action. From the full repository, rebuild with Blender 4.3, NumPy and Pillow by running `wolf-viewer/authoring/build_motion.py`, then `correct_surface.py`, then `export_correctives.py`. Preserved prior source projects supply the baseline. Intermediate files belong in ignored `review/drafts`. Never enable WOLF_RAW_PREVIEW for a release export.

Review both normal-speed and slow-motion frame sequences, side/rear silhouettes, idle/walk/run transitions, skin folds, foot contacts, head stability and tail kinks before publishing. Keep the fixed release filename, folder, branch and viewer entry point for subsequent revisions.

Model derivative: “Amaterasu the Japanese Fox God” by theamazingdonovan207, CC BY 4.0. See credits and licence. The uploaded dog reference remains outside the published project.

Shoulder-fur preview: `fur_weights.py` gives the loose upper tips a progressive attachment to their fur controls. For a full animation rebuild, use this order: `build_motion.py`, `fur_weights.py`, `correct_surface.py`, `surface_polish.py`, `repair_surface.py`, `fur_details.py`, `anchor_fur.py`, `fur_finish.py`, `export_correctives.py`. Surface polishing refines the original polygon topology and the 48 companion corrective shapes together. Surface repair closes inherited boolean gaps with a fine voxel surface, relaxes the surface and transfers skin weights and corrective offsets from the source triangles. These stages run once per coarse rebuild and reject repeated application. Colour and normal textures are then repainted onto the refined surface. `coat_material.py` uses a continuous ivory wash; form shadows come from lighting rather than polygon normals baked into the paint. The polished export omits the old baked occlusion, which recorded damaged surface creases. `fur_details.py` adds closed, tapered curl and plume layers over the repaired skin, with progressive flow weights. It preserves the approved body coordinates; retained leg skins also remain in place. Run it after repair; repeating it reloads its saved clean input instead of accumulating copies. `anchor_fur.py` projects their roots into the underlying coat and blends root skin weights into the attachment triangles. These details must not be voxel-remeshed afterwards. `FurWash` adds quiet cool underlayers and ivory ridges, and `FurGeometry` keeps flat body markings off the sculpted layers. The old flat shoulder and ankle scrolls are replaced by physical curls; tail ink remains. Both colour attributes are baked into the atlas, and vertex-colour export is disabled to avoid multiplying the wash twice. Preserve `src/fur-dynamics.js` for the anchored wind response. This preview updates the source and MP4; the downloadable viewer ZIP is intentionally unchanged at the user’s request.

Tail support acts only at the first segment. The remaining chain bends under gravity and drag, with gentle distributed curvature relaxation. The visible proximal tail now uses progressive plume weights in Idle and Walk as well as Run. The tail validation checks that the first three segments already fall at idle, caps the permitted joint bend and checks transitions and every clip for finite motion. `fur-dynamics.js` also drives the ankle and haunch layers; keep it with the model.

The GLB includes a `_FUR_DETAIL` attribute (loaded by Three.js as `_fur_detail`). `ink-outlines.js` uses it to separate the sculpted-fur contours from the full silhouette. The silhouette draws behind the skin without writing depth; the fur-only contour pass draws after the skin. This prevents interior backfaces from painting dark triangles over bent body skin while keeping the curls readable. Keep the floor before both passes and share the body’s morph influences with both outline meshes.

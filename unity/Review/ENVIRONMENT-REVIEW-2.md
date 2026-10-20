# Windflower environment review 2

This is an automatic overlay for the existing Unity project, not a new project or a wolf rebuild.

## Install

1. Close the Unity Editor. Unity Hub can stay open.
2. Extract `Sunward-Unity-Environment-Update.zip` into the existing `Sunward-Unity` folder containing `Assets`, `Packages` and `ProjectSettings`. Allow replacement of the listed update files. Do not delete the project or extract into its `Assets` subfolder.
3. Reopen the Windflower scene and let Unity finish importing. The Console should report **Environment review 2 saved**. Then press Play. No routine Sunward update-menu operation is required.

If migration reports an error, read the first Console error. The updater will not mark the migration complete. There is a recovery menu `Sunward > Apply Environment Review 2`; do not rebuild the wolf or reprocess animation clips.

## Changes

- Relocate the home crossing from Unity Z -12 to -8; shift source deck/rail geometry and native rail/deck colliders. Move the neighbouring lantern away from the approach, add low landing stones, update the walking-height/water guard and navigation rail coordinates. The distant crossing is retained.
- Filter the obsolete baked ink geometry at the old stone bounds, rather than disabling all shadows. Remove the detached old red/blue banners and old rope.
- Remove all three legacy arena lanterns, including the two within the trial area. Replace them with seven closed-roof lamps beyond the trial radius. Replace the thin brown rim strokes with 28 substantial cedar log segments and growth-ring end caps; leave the west entrance open.
- Clear intersecting trees along the full main market street and their matching navigation/collider obstacles.
- Five supported coloured festival spans, 35 ribbed lanterns with painted crests, 60 streamers, ten shadow-free festival lights, eight street displays, bounded motes and six ambient browsing residents. The seven named quest residents and their dialogue remain separate. Existing market audio is retained.
- Denser rounded stone meshes. Seven original surface sets: granite, cedar, end grain, earth, meadow, lime plaster and slate; 21 albedo/normal/AO-smoothness maps. World-space PBR surfaces and connected road masks, with UV-aligned timber grain. Material replacements also connect to the visible authored buildings/stalls, not merely the hidden source geometry.

These are original procedural materials, not photographic scans. This release does **not** establish hyperrealistic art quality.

## Verification and limits

- C# syntax and the existing save/combat/scale regression tests pass. This is not Unity API compilation.
- Actual exported geometry checked: 2.675m bridge-to-home-wall clearance; both rail offsets; updated water guard; 1,215 obsolete ink faces and 42 banner faces selected; log boundary outside 18.37m; closed 40-sided lantern roofs.
- 122 closed stone meshes: 58,560 foundation support samples, 360 pond rim checks and 2,560 terrain-triangle comparisons passed.
- 21 PNG maps decoded, normal vector/mask ranges checked. Original Amaterasu FBX SHA-256 is unchanged. No animation, game logic, save data or original Three.js files are included in this update.
- Neutral Blender bridge/house geometry inspected. `bridge-clearance-geometry-diagnostic.png` is explicitly a geometry diagnostic, not a Unity screenshot. The material sheet shows source maps, not final Unity rendering.
- **Unity Editor is unavailable in this environment.** Native shader compilation, migration execution, Play Mode, visual quality and frame rate are not verified. Shader compilation is checked by the updater before source geometry is edited. A successful numerical check is not visual approval.

## Rollback

Before migration, a timestamped folder is saved under `Review/LocalBackups/Environment-*` on your PC. It contains the existing scene and `ValleyMeshes.asset` (including its meta), since source-mesh indices change in this update.

To restore: close Unity, create the empty file `Review/DISABLE-ENVIRONMENT-REVIEW-2.txt` to pause automatic reapplication, then copy the saved scene into `Assets/Sunward/Scenes` and `ValleyMeshes.asset`/meta into `Assets/Sunward/Generated`. Keep all other project files. Reopen Unity. The original exported Valley data and wolf FBX remain unchanged.

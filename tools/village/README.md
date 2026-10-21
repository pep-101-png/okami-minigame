# Windflower: twelve-request village repair

Changes are saved into the real Windflower scene and native Unity assets. They
are ready to import; the PC does not need Blender, Python, an asset pack, a new
installer, a scene-building menu command or a new scheduled task.

| Request | Implemented change | Real Unity verification still needed |
| --- | --- | --- |
| Loud water / humming | Market ambience reduced from .15 to .035, music .12 to .055; global ambience .065 to .018. Replaced the continuous 160 Hz sine loop with quiet filtered air. Original wolf/effect recordings preserved. | Listen near the river, mill, market and home; confirm perceived level and whether any other hum remains. |
| Slow / bouncy movement | Controlled walk .57→1.1 m/s, normal travel 2.45→3.6, sprint 5.3→7.2; stronger acceleration/stopping; stable gait boundaries, phase-aware crossfades, smoothed playback rates and calmer grounded pelvis motion. | Check actual gait/foot contact, turning, landing, collision and stamina feel. Original 47 clips and wolf appearance assets unchanged. |
| Identical NPCs | Seven original costume meshes: gardener, elder, merchant, shrine maiden, samurai, chef and geisha. Facial features, headwear, clothing silhouettes and accessories differ. All seven named NPCs and six shoppers retain their own existing skeletons, routes and dialogue. | Inspect sleeve/robe deformation, seams, hat and sword clipping during movement. |
| Identical rocks | 122 existing rocks now use eight carved shapes in four families: layered sandstone, sharp granite, split basalt and weathered stone, with four new colour/relief paintings. | Check silhouettes, seating and lighting at player height. Existing bounds/base positions and physics proxies retained. |
| Trees | 21 original placements now use forked/tapered grooved trunks, roots, knot geometry and dimensional cherry/maple/evergreen crowns; original bark painting and gentle wind. | Check canopy density, branch contacts, wind and performance. |
| Black lantern artefacts | Removed 2,640 obsolete ink-outline triangles around existing lamps. Filtered legacy copies have finite recalculated normals. Existing unshadowed point-light policy retained. | Confirm the reported dark patches are gone; this is not a rendered approval. |
| Floating roofs | Supported closed roofs, continuous wall/eave beams and under-roof rafters. Home receives a connected roof/frieze while retaining its interior and cutaway behaviour. | Inspect joints from street level and enter/leave Ammy's home. |
| Toy-like houses | 14 village buildings receive connected framed façades, inset lattice windows, carved entries, foundations, real tile lips and curved eaves; shop curtains/crests and cladding vary. Fronts face the existing streets; existing collision footprints retained. | Judge artistic quality and camera readability; buildings are stylised, not photorealistic. |
| Following circle / line | Removed persistent movement wind-line aura. Earned body curls and short attack/jump/water effects remain. | This was the persistent movement-line system found in code. The exact user-visible circle is not conclusively identified; confirm it has disappeared. Editor selection/gizmo overlays are not gameplay footage. |
| Flat ground plants / bamboo | 540 shared-mesh planted patches and seven bamboo groups: curved ribbed leaves, cupped flowers, shaped stems and bamboo nodes. Root-anchored wind and procedural veins; avoid the road, arena and pond. | Check density, colour, root contact, wind and frame time. Small groundcover casts no individual shadows. |
| Transparent second bridge | Explicit opaque timber material bindings plus a closed plank deck following the existing walking arch. | Walk across both crossings and inspect underneath; navigation/collision surfaces preserved. |
| Trial stick and nearby lamp | Removed the old stick and adjacent lantern at (12,0)/(13,-1), their visual pieces and obsolete obstacle/capsule proxies. Added a joined timber bell entrance, bronze bell and rope at the existing interaction point. E rings the bell and enters the existing trial. | Test E, bell sound, entrance clearance and unchanged trial progression. |

No automatic merge, installed-task change, Git sync modification, API key or paid
API service is included. Existing saving, quests, combat, weapons, home interior,
wolf model/materials/importer and original animation files are preserved.

## Evidence and limits

The newest available uploaded feedback remained run
`20261021T092745607Z-9936e8`, source `aefd595771e933a3313ecb4170251764c94ab1e3`.
Its 12 screenshots and samples from all 14 MP4s were inspected. All clips had full
frame counts but incomplete movement coverage; the wolf was largely stationary.
There was no newer feedback when this change was prepared.

New native geometry was rendered in Blender and inspected. Corrections included
inverted tube winding, rafters protruding through roofs, overly rounded rock shapes
and pointed flower petals. Files in `previews/` are **Blender asset previews with
vertex colours**, not Unity screenshots or proof of final shader/texture appearance.

Cloud checks cover native buffers/indices/normals/bone weights/bind poses, scene
reference preservation, all 13 live NPC rigs, texture colour spaces, closed-solid
winding, movement tuning and C# syntax. Unity is not installed here. Actual Unity
import/compilation, audio, movement quality, final scene renders and frame time
have not been verified. Shared meshes/materials limit duplication; the new foliage
still needs a real PC performance measurement.

The recording camera now constrains bad imported edit-mode wolf bounds. The video
driver routes its synthetic gamepad to an unfocused editor Game View, restores those
settings afterwards, and reports an explicit error if input does not reach gameplay.
This targets the observed idle recordings; only a new Windows run can prove it fixes
the failure. Existing publishing, installed runner copies and tasks are unchanged.

`WindflowerDiagnostics.Connections` recognises the new authored bark/rock folder
and checks all renderers in the loaded scene, including new independently rooted
models. Its existing five-family, river, weapon, home and 47-clip checks remain.

## Updating on Windows

1. Review and merge this PR into `sunward-minigame`.
2. Close Unity so it cannot save an older scene over the update.
3. Let the existing Git sync retrieve the merged update, or use the safe one-line
   Windows+R command supplied with the PR. It fetches, then fast-forwards only;
   conflicts/local edits stop it. Never reset/discard local work.
4. Open the existing `Sunward-Unity` project in Unity 6000.6.6f1 and wait for imports.
   Open Windflower. No migration menu or reconstruction is required.
5. Let the existing validator publish fresh screenshots/recordings. In an active
   Codex subscription task those can be fetched directly from GitHub, without
   asking the user to copy or upload files. This cloud session cannot start a task
   on the PC or automatically awaken an idle Codex conversation.

A successful Git update proves the files arrived; it does not prove the game is
visually correct. The seven new outfits, bell entrance and street-facing façades
are clear landmarks to check in the actual game.

## Reproducible authoring and checks

Cloud authoring requires Python 3 with NumPy/Pillow. Run `build.py` only against the
pre-pass scene at integration commit `a6b9d4d89c43acccfcca17a8d86bb3f32182b486`;
it refuses an already-authored scene. This script is not an updater for the PC.
It preserves the original scene nodes and creates typed prefab overrides instead
of editing the large original mesh archive. Superseded original visuals remain
recoverable but inactive. Do not rerun old world builders on top of this scene.

```sh
python tools/village/build.py
python tools/village/check_village.py
pwsh -NoProfile -File tools/village/Test-Movement.ps1
blender -b -t 4 -P tools/village/render_previews.py
```

The movement rule file deliberately uses C# 5-compatible syntax for Windows
PowerShell 5.1 Add-Type. The Unity-only runtime/driver code uses Unity's compiler.
Python and Blender are optional authoring tools, not game/runtime dependencies.

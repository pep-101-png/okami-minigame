# Actual Sunward remaster — implementation progress, not completion

27 October 2026. **The existing Windflower scene has been changed. The full remaster is still unfinished.** Ammy's native animations and the complete Solar Flare replacement remain outstanding. Unity compilation, actual gameplay and Unity screenshots cannot be verified in this environment because Unity is unavailable.

This report supersedes the earlier separate-review-scene delivery. That earlier delivery did not fulfil the requested game overhaul. Its historical report remains in `audit/stage1-review-report.md`; it must not be read as the status of the current implementation.

## Actual scenes and prefabs modified

**Modified:** `Sunward-Unity/Assets/Sunward/Scenes/Windflower.unity` — the existing gameplay scene and unchanged startup/build scene. This is the scene containing the established village, player, NPCs, markets, home, river, arena and progression systems.

**Existing prefab files modified: none.** The Editor-only `Assets/Editor/WindflowerDiagnostics.cs` was updated for recovered painting paths, the new river shader name and assigned remaster shader error checks.

The existing TownV3 instance has controlled visual/material overrides in Windflower; the TownV3 prefab asset remains intact. The old house/rock/bridge visual objects remain serialized for rollback, with selected renderers disabled and replacement visual children attached to their established transforms. Amaterasu, Sundial, Spear, NPC and enemy prefab files are unchanged.

**New live assets:** `Assets/OkamiRemaster/Windflower`, containing saved native Unity meshes, material clones, recovered painting crops, the ambient-animal component and its layout. These are already referenced by Windflower. No authoring script or special review menu is required to apply them.

The separate VillageDemo scene, review menus, demo scripts, large packed demo world and inactive Ammy/Solar Flare research objects were moved **outside Assets** to `tools/remaster/reference`. They are retained as source/provenance, not used as a replacement world or another playable demonstration. Shared textures, shaders and animal resources used by the actual scene remain in Assets. The active Unity project now contains only the original Windflower scene.

## Implemented in the playable world's saved scene

| Area | Actual implementation | Provenance and limits |
| --- | --- | --- |
| Houses | 14 existing exterior placements receive finished Willow/Carp/community-hall geometry, fitted to their established building footprints and headings. Old overlapping exteriors/contours are disabled. | Successful reference-village composite/authored house models and painted artwork. These are not all directly extracted complete original Ōkami houses. Ammy's functional home/interior/cutaway is retained. |
| Markets | Both existing market stalls receive recovered painted canopy geometry; existing counters, goods, lanterns, merchant roles and interaction objects remain. | Reference-village canopy mesh 82 and its painted atlas bindings, not a claim that the whole stall is an extracted original market. |
| Bridges | Both existing crossings receive the original ST2 bridge geometry and textures, plus recovered authored plank/ink detail. Source deck arch is adapted to Sunward's existing bridge-height function and walking width. | ST2 `r200.dat/3.SCR`. Old rails/deck overlays are hidden; both existing physics meshes and water/traversal contracts remain unchanged. |
| Trial entrance | The existing functional bell entrance receives the original torii frame/plaque/footings. The working bell and pull remain. Two new post proxies leave a checked 1.71 m central approach. | ST2 `r200.dat/35.SCR`, fitted to the existing bell position. Bell action, arena entry and progression code are unchanged. |
| Rocks | **122 existing rock placements** receive ten standalone original boulder shapes extracted from disconnected components of the ST2 garden-rock division. Existing bases, transforms/scales and physical proxies are retained. | ST2 `r200.dat/6.SCR`, division bound to the weathered-rock artwork. Each source island has 74 triangles; no triangle simplification was used. Existing contour shader supplies outlines. |
| Cherry trees | Eleven existing cherry placements receive the reference village's painted core trunk/crown geometry. Existing bases and trunk colliders remain. Distinct pines/olive trees are preserved. | Reference/composite tree meshes 94–100, not a newly identified original tree archive. Dense extra decorative flower overlays are not part of this core replacement. |
| Bamboo | Seven existing groups keep their working geometry/placement and receive recovered leaf-panel painting with existing wind parameters. | Painted reference-village artwork; no standalone original bamboo model has been verified. |
| Grass | 360 existing grass patches receive recovered botanical artwork, retaining their current shaped blades, positions and wind. | Texture integration, not an original grass-model replacement. |
| Decorative flowers | 180 existing patches have stems and petals separated; petal surfaces use the recovered original petal painting while preserving the existing wind parameters and placement. | The quest/pickup flowers are not altered. This is painted-art integration into existing geometry, not replacement by an identified original flower model. |
| Broader surfaces | 177 environment material clones bind recovered timber, roofing, stone, bark, grass, earth and plaster/reference paintings. Existing definitions remain available. | Material/artwork integration across existing props, home details, rocks/cliffs and surfaces. Some source atlas artwork is authored reference material; per-source paths/hashes/crops are recorded. No original cliff/lantern/fence model is falsely claimed. |
| River | Existing river flow/depth-contact geometry and a new shader clone blend the recovered water painting into the visible surface. The live TownV3 renderer material override is explicitly bound, not left as an unused asset. | Artwork replacement; the entire original native water-effect dispatcher has not been reconstructed. |
| Garden pond | The existing recessed pond has a shader/material clone sampling the recovered water painting, while its basin, depth/refraction logic and physical surface remain. | Native painting integration; no claim of original native effect timing. |
| Animals | A component in Windflower is configured to spawn **13 ambient actors across nine types** on deliberate village/home/meadow/woodland routes, using recovered native rigs/textures and converted native idle/walk pose data. | Cow, pig, piglet, rooster, rabbit, panda-rabbit, dog, cat, boar. The original data is shared, not copied into another farm scene. Spawn/playback is implemented but has not been observed in Unity. |

The ambient animals sample Sunward's own ground height, avoid the river through its existing guard, pause for the player/UI, and probe existing world collision while walking. They add no solid obstacles to NPC/player routes and take no interaction key from GameFlow. Their paths pass static building/obstacle/arena/pond clearance checks. There is no claim that live AI, collision or animation playback has passed a play test.

Mesh/material reuse and instancing support are provided for repeated assets. Unreferenced vertices and redundant opaque indexed faces are removed without changing the surviving visible geometry/UVs. Invalid source normals are repaired in converted meshes where needed. The scene still needs actual CPU/GPU, memory/load-time and build-size profiling; no FPS result is claimed.

## Original Ōkami assets actually integrated versus research only

The confirmed ST2-origin bridge, torii and ten boulder components now have saved live Windflower renderer bindings and their recovered texture/UV assignments. Original animal rigs, skins and converted native pose data are loaded by the live Windflower animal component. Original petal/water and other recovered painted surfaces are bound into actual scene materials.

The reference houses, reference cherry model, market canopy and some atlas panels are authored/composite work from the successful village, used as secondary standards. They are explicitly not catalogued as wholly original extracted game models. `live/authoring-report.json` records every new object, source mesh group, material change, texture source/crop, rock-island face list, building fit and bridge conversion.

The full source audit remains in `audit/replacement-matrix.csv` (1,838 asset rows), `audit/project-inventory.json`, `audit/pl-source` and `audit/wp-source`. Exact equivalents are still unresolved for some assets, including the 387 originally unclassified rows. The matrix is an audit/candidate ledger, not proof that every candidate was replaced.

## Amaterasu animations — not replaced yet

**Zero Ammy gameplay animation clips have been replaced.** The working 74-bone player rig, 47 existing clips, controllers and WolfMotor/WolfAnimation connections remain active.

Recovered sources contain 98 distinct shared Ammy PL motions and 67 additional distinct WP Ammy motions: **165 total, 162 changing and three static**. Original default Ammy skin/geometry and its 38-bone native hierarchy are available. Those source bytes are preserved under `tools/remaster/reference/NativeSources`; archived/imported/review files are not counted as gameplay integration.

The native 38-bone hierarchy is incompatible with a direct clip swap onto Sunward's 74-bone rig. A native visual-rig adapter or verified retarget is required, including root-motion separation from WolfMotor, scale/axis calibration, action mapping, foot contacts and transitions. The public MD Studio importer provides a 30 FPS/XYZ reference and normalized tangent interpretation; that does not by itself validate an entire Sunward animation port. Walking/running candidates are recognizable in offline motion previews, but unverified jump/dodge/action assignments must not be passed off as a finished controller.

Replacing working movement with guessed state mappings or double-applied jump/root motion would violate the request to preserve gameplay. Native movement/combat integration remains required work, not a completed checkbox.

## Solar Flare — not replaced yet

**The live Sundial weapon has not been replaced.** Its prefab, equipment/save ID, strike definitions, attack windows, damage, switching and current working visuals/effects remain active.

The original Solar Flare `wp24` and paired `wp34` model/texture/rig/motion resources are recovered. Each model has 16 bones, 743 stored vertices, 517 triangles and six material divisions using three texture slots. Reflector-family Ammy motions are also present. There are 98 retained Solar Flare component records with verified byte hashes.

What remains unresolved is the native EST/SEQ effect interpretation and runtime choreography: emitter/texture/blend flags, flame attachment and activation, attack-trail timing, impact spawning, weapon/body-motion synchronization and correct attachment to Ammy. WP contains no verified accompanying sound bank. These are conversion/interpretation gaps, not a claim that the available source files were never found.

A static textured model is not a complete Solar Flare replacement. Once the full visual adapter is verified, it must switch the model and disable the old custom disc/flame effects together, preserving gameplay and avoiding duplicate effects. That has not happened yet.

## What is protected and what was checked

Protected baseline: `00fd8695363df01de80b012d68feb20c9961e8a9`. Work branch: `remaster/okami-native-integration`. Rollback branch: `backup/sunward-pre-native-remaster-20261027`.

The hydrated rollback archive was verified by re-reading every member, including the recovered original LFS idle clip. Archive SHA-256: `5d5e1cb0cf2b6d90567cf988e25042bc94619391e3ad7f9009963fe7c84d064b`. Original archive details and every baseline file hash are recorded in `audit/backup-receipt.json` and `audit/baseline-file-manifest.json`.

Current offline checks pass:

- **3,729 other baseline project files are byte-identical**. The changed existing files are Windflower.unity and the Editor-only WindflowerDiagnostics.cs. Diagnostics now recognises recovered art/shader paths and checks assigned remaster shaders for import errors; no existing runtime/gameplay script was changed. New live assets are additive.
- No existing serialized object was deleted or moved. Permitted changes are visual renderer/material bindings, child lists and controlled prefab renderer/material overrides.
- All **192 existing gameplay components**, **208 existing skinned renderers**, **63 box colliders**, **125 capsule colliders**, **two mesh colliders**, the player character controller, animator and camera remain byte-identical in the scene. The two torii post colliders are new additions.
- NPC rigs/dialogue/navigation/roles, player/weapon data, arena/waves/bosses, progression/save code and existing settings/pipeline/build scene are preserved.
- New scene/material GUIDs resolve without duplicate asset GUIDs. New mesh buffers have finite positions, valid indices and unit used normals.
- 14 live house replacements, two market roofs, two bridge replacements, 122 rocks, eleven cherry trees, seven bamboo groups, 360 grass patches and 180 decorative flower patches are recorded and checked.
- The 13 animal placements avoid checked building/obstacle/arena/pond footprints; native motion/source component hashes remain intact.
- **78 active C# files pass syntax parsing**. This is not Unity semantic/API compilation.

The latest published Unity feedback remains the older 21 October run from `aefd595771e933a3313ecb4170251764c94ab1e3`; all 14 clips have incomplete action coverage. It cannot validate this branch. No Windows tasks, installed runners, paid APIs or syncing were enabled or changed.

## Images and missing runtime proof

The before/after images in `live/previews` are generated from the **actual saved Windflower scene**, with matching cameras and the original scene used as the before snapshot. They show the real scene's layout/asset substitutions, not the separate demo. They are permanently labelled **BLENDER — NOT UNITY**.

These are geometry/layout checks. They do not reproduce Unity's full renderer, moving animals, native gameplay animations, audio, physics or performance. The preview's native ink clipping was corrected without modifying the game to compensate for a Blender-only artifact.

**No current-build Unity screenshot, successful Unity compile, Windows build or successful play-session evidence is available.** The requested running-game screenshots and compile/play evidence remain outstanding; Blender images and file checks are not substitutes.

## Remaining work and real blockers

1. Obtain actual Unity 6000.6.6f1 import/C# and shader results for this changed Windflower scene; fix failures and inspect play-mode footage. This environment has neither Unity nor access to control the user's PC.
2. Implement and verify the native Ammy rig/animation adapter, including confirmed locomotion/jump/landing/dodge/combat states, original timing, root motion and transitions.
3. Complete Solar Flare's EST/SEQ/effect/attachment interpretation and synchronized animation adapter, then replace the live model/effects as one controlled change.
4. Identify verified original replacements for remaining cliff, lantern/fence and other vegetation/prop meshes. Existing working models remain where only painting/reference artwork is integrated.
5. Verify live navigation, animal grounding/loops, house/market clearances, bridges, river, NPC interactions, home, every arena wave/boss, equipment/attacks, UI, upgrades, collectibles and save/load. Profile the exact build.

The environment implementation is concrete and reviewable, but the **overall remaster remains open and incomplete**. The PR stays a draft pending these gates; it is not being presented as a finished game update.

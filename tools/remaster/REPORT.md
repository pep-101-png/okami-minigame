# Actual Sunward remaster — implementation progress, not completion

28 October 2026. **The existing Windflower scene has been changed, and native Ammy/Solar Flare visual adapters are now installed in that game. The full remaster is still unfinished.** Solar Flare's complete particle dispatcher and actual Unity import/play verification remain outstanding. This environment has no Unity Editor or access to control the user's PC.

This report supersedes the earlier separate-review-scene delivery. That earlier delivery did not fulfil the requested game overhaul. Its historical report remains in `audit/stage1-review-report.md`; it must not be read as the status of the current implementation.

## Actual scenes and prefabs modified

**Modified:** `Sunward-Unity/Assets/Sunward/Scenes/Windflower.unity` — the existing gameplay scene and unchanged startup/build scene. This is the scene containing the established village, player, NPCs, markets, home, river, arena and progression systems.

**Existing prefab modified:** `Assets/Sunward/Generated/Sundial.prefab` — one native Solar Flare visual component added; all original object/mesh/material blocks retained for fallback. The existing `Amaterasu.prefab` remains intact; the native body component is attached to its existing player instance in Windflower.

**Existing scripts modified:** `WolfAnimation.cs` forwards visual state changes/rates/clip lengths; `WolfCombat.cs` calibrates native head/back sockets in Start; `DivineGrowth.cs` attaches existing earned power curls to native shoulder/paw/hock bones with the correct visual scale. All combat methods from Equip onward, including Update, damage, attack windows, weapon switching and save calls, remain byte-identical. The Editor-only `WindflowerDiagnostics.cs` recognises recovered art/shaders.

The existing TownV3 instance has controlled visual/material overrides in Windflower; the TownV3 prefab asset remains intact. Old environment objects remain serialized for rollback. Amaterasu, Spear, NPC and enemy prefab assets are unchanged. Sundial retains its original objects beneath the added visual adapter.

**New live assets:** `Assets/OkamiRemaster/Windflower`, containing saved native Unity meshes, material clones, recovered painting crops, the ambient-animal component and its layout. These are already referenced by Windflower. No authoring script or special review menu is required to apply them.

`Assets/OkamiRemaster/Player` now contains the original native body/weapon models, original paints, converted motion banks, action bindings and four runtime visual-adapter scripts. These load in normal gameplay. The old 74-bone FBX/controller remains an automatic fallback if native resources cannot load; it is hidden only after successful native initialization.

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

## Amaterasu animations — native adapter installed, Unity playback unverified

The live player is now configured to build **the original pl00 default skin, 2,969 stored vertices and original 38-bone rig**, with original painted textures and the original inward-facing ink shells. It plays original native motion on that hierarchy instead of attempting an incompatible swap onto the old 74-bone FBX.

All **47 existing controller states** have native bindings, using **34 distinct original Ammy motion payloads**. The bindings file has 48 entries because it also selects a separate glaive-family air attack for the spear. Reusing one genuine motion for several Sunward variants does not create distinct original animations.

| Sunward action | Original native motion selected |
| --- | --- |
| Idle | `pl00_000` |
| Walk / run / sprint | `pl00_010` / `011` / `012`; existing turn variants share their gait while the motor turns |
| Standing / moving / sprint jump | `020→021` / `024→025` / `027→029`; double jump `031`; falling `022` |
| Soft / heavy landing | Both use `02d`, fitted to the existing landing duration |
| Forward / backward / side dodge | `017` / `018` / `019`; the opposite side mirrors the native bone transforms |
| Sleep down / loop / wake | `003→005` / `004` / `006` |
| Bark | `04e` |
| Reflector light chain / heavy / charged / air | `500,501,502` / `503` / `504` / `505`; ready/charging `511` |
| Spear's adapted glaive-family combat | `520–525`; some Sunward charged variants reuse these original actions |

The exact mapping and provenance notes are in `Assets/OkamiRemaster/Player/Resources/NativePlayer/Bindings.json`. Action names are Sunward adaptations selected from inspected poses and source weapon families, not a recovered native-engine action-name table. Foot contacts, speed matching, transitions, jump staging, mirrored dodge direction and attack/weapon attachment still require actual play verification.

The converter bakes 30 FPS native Hermite/XYZ motion at 60 Hz, preserving deform-bone positions, rotations and scales. Only virtual scene-root translation is removed so WolfMotor keeps ownership of movement/gravity/jumps/lunges. Native +Z facing is preserved while X is reflected to convert handedness. Visual transitions blend poses; the original controller and gameplay logic remain available for fallback.

All 165 original Ammy payloads were converted into the runtime bank, but only the 34 selected payloads are counted as bound gameplay actions. **No old `.anim` files were overwritten**, and no actual Unity animation playback has been observed here. This is implemented runtime integration awaiting Unity acceptance, not a claim that 47 distinct original animations have passed.

## Solar Flare — original model and animated flame geometry installed; effects incomplete

`Sundial.prefab` now loads original `wp24` **16-bone, 743-vertex, 517-triangle geometry**, all three original texture slots and original skeletal motion **`wp24_000`**, including deforming flame ribbons and curl geometry. It disables its old custom mesh renderers only after native initialization succeeds. This also applies to normal prefab instances such as the home display. The equipped native weapon uses a socket following the original body's dorsal attachment; weapon meshes avoid inheriting the body's squash/stretch scale.

The retained `sundial` equipment/save ID, costs, unlocks, strike definitions, hit windows, damage, switching, audio cues and attack transforms are unchanged. Reflector-family Ammy combat is selected through the native body adapter. `wp24_001` and paired `wp34` model/motion are converted and available but not selected as additional verified gameplay animations.

**This is not the complete Solar Flare effects replacement.** The native EST particle emitter/texture/blend semantics, SEQ event opcodes, original attack-trail/impact dispatch and complete weapon/body choreography remain unresolved. The source includes 28 EST records across wp24/wp34 (13 distinct payloads) with 752-byte particle records, plus six SEQ records. Their raw structures/hashes are recorded in `live/solar-effect-audit.json`; this is an audit, not an implemented emitter decoder. WP contains no verified weapon sound bank.

The existing `PaintedEffects.SundialOrbit`, impact renderer and Sunward's attack transform path remain active. They must not be called original native effects. The original animated flame geometry is now integrated; the separate native particle dispatcher is not. The full replacement therefore remains **partial**, with actual in-game alignment/appearance still unverified.

## What is protected and what was checked

Protected baseline: `00fd8695363df01de80b012d68feb20c9961e8a9`. Work branch: `remaster/okami-native-integration`. Rollback branch: `backup/sunward-pre-native-remaster-20261027`.

The hydrated rollback archive was verified by re-reading every member, including the recovered original LFS idle clip. Archive SHA-256: `5d5e1cb0cf2b6d90567cf988e25042bc94619391e3ad7f9009963fe7c84d064b`. Original archive details and every baseline file hash are recorded in `audit/backup-receipt.json` and `audit/baseline-file-manifest.json`.

Current offline checks pass:

- **3,725 other baseline project files are byte-identical**. The six changed existing files are Windflower.unity, Sundial.prefab, WolfAnimation.cs, WolfCombat.cs, DivineGrowth.cs and WindflowerDiagnostics.cs. The new adapters are additive; all existing combat methods from Equip onward remain exact.
- No existing serialized object was deleted or moved. Permitted changes are visual renderer/material bindings, child lists and controlled prefab renderer/material overrides.
- All **192 existing gameplay components**, **208 existing skinned renderers**, **63 box colliders**, **125 capsule colliders**, **two mesh colliders**, the player character controller, animator and camera remain byte-identical in the scene. The two torii post colliders are new additions.
- NPC rigs/dialogue/navigation/roles, player/weapon data, arena/waves/bosses, progression/save code and existing settings/pipeline/build scene are preserved.
- New scene/material GUIDs resolve without duplicate asset GUIDs. New mesh buffers have finite positions, valid indices and unit used normals.
- 14 live house replacements, two market roofs, two bridge replacements, 122 rocks, eleven cherry trees, seven bamboo groups, 360 grass patches and 180 decorative flower patches are recorded and checked.
- The 13 animal placements avoid checked building/obstacle/arena/pond footprints; native motion/source component hashes remain intact.
- **82 active C# files pass syntax parsing**. This is not Unity semantic/API compilation.
- All 183 exported motion payloads (165 Ammy, 16 wp24 and two wp34) have checked pose-bank hashes, finite data, normalized quaternions and zero virtual-root translation.
- **71,256 skinned vertex positions** from eight original motions at three sampled times agree with the earlier independent archive-inspection decoder within **0.000000512 metres**. This compares conversion math and skinning; it does not prove Unity behavior or native-engine-perfect timing.
- The old Sundial prefab blocks are exact after removing the one added component reference. Source models, animations, controller/settings and working fallback payloads remain retained.

The latest published Unity feedback remains the older 21 October run from `aefd595771e933a3313ecb4170251764c94ab1e3`; all 14 clips have incomplete action coverage. It cannot validate this branch. No Windows tasks, installed runners, paid APIs or syncing were enabled or changed.

## Images and missing runtime proof

The environment before/after images in `live/previews` were generated from the **actual saved Windflower environment**, with matching cameras. Their metadata records the earlier environment snapshot; the later native-adapter addition changes the scene hash but does not change those environment meshes. They are permanently labelled **BLENDER — NOT UNITY**.

Nine additional labelled `native-*.jpg` images show the exact converted native pose-bank skinning for idle, walk, run, sprint, jump, landing, dodge, reflector combat and Solar Flare's native flame geometry. Their metadata records the exact pose-bank/model/image hashes. These are isolated Blender pose diagnostics, not running-game captures or Unity shader/attachment checks.

These are geometry/layout checks. They do not reproduce Unity's full renderer, moving animals, native gameplay animations, audio, physics or performance. The preview's native ink clipping was corrected without modifying the game to compensate for a Blender-only artifact.

**No current-build Unity screenshot, successful Unity compile, Windows build or successful play-session evidence is available.** The requested running-game screenshots and compile/play evidence remain outstanding; Blender images and file checks are not substitutes.

## Remaining work and real blockers

1. Obtain actual Unity 6000.6.6f1 import/C# and shader results for this changed Windflower scene; fix failures and inspect play-mode footage. This environment has neither Unity nor access to control the user's PC.
2. Verify the installed native Ammy adapter in actual gameplay, including contacts/speed matching, jump stages, dodge direction, scale, rest transitions and weapon/body alignment; correct action adaptations against original-game evidence where available.
3. Decode and implement Solar Flare's EST/SEQ particle dispatcher, trails/impacts and full choreography. Native model/paint/skeletal flames are installed, but those separate effects and full original attack path are not.
4. Identify verified original replacements for remaining cliff, lantern/fence and other vegetation/prop meshes. Existing working models remain where only painting/reference artwork is integrated.
5. Verify live navigation, animal grounding/loops, house/market clearances, bridges, river, NPC interactions, home, every arena wave/boss, equipment/attacks, UI, upgrades, collectibles and save/load. Profile the exact build.

The environment implementation is concrete and reviewable, but the **overall remaster remains open and incomplete**. The PR stays a draft pending these gates; it is not being presented as a finished game update.

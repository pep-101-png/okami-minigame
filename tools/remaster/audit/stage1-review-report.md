# Sunward native Ōkami remaster — audit and first integration stage

27 October 2026. **The complete remaster is not finished or validated.** This delivery protects the existing game, inventories its assets, and prepares the village and original player/weapon data for Unity review. It does not replace the live town, player or Sundial Flame.

Integration target: `sunward-minigame` in `pep-101-png/okami-minigame`.
Baseline: `00fd8695363df01de80b012d68feb20c9961e8a9`.
Work branch: `remaster/okami-native-integration`.
Rollback branch: `backup/sunward-pre-native-remaster-20261027`.

## Protection and recovery

A local compressed rollback archive was created **before adding remaster assets**. Every member was re-read and compared against its recorded SHA-256, including Unity metadata. It contains 3,731 project files, 1,536,040,197 uncompressed bytes, and no unresolved LFS pointers. Compressed archive: 217,258,466 bytes; SHA-256 `5d5e1cb0cf2b6d90567cf988e25042bc94619391e3ad7f9009963fe7c84d064b`.

The existing `Idle_Natural.anim` was initially a 134-byte LFS pointer. Its exact original 159,951,318-byte payload was fetched and checked against LFS SHA-256 `ec366136a5252c2354ae11403097d4d43fb2e18d6ef0bc477c79e9fc36ca8375`. This is restoration of the baseline, not a new animation. Some historical binary assets are ordinary Git blobs despite older LFS patterns; they were not renormalized.

The exact baseline commit is preserved remotely on the rollback branch. The full local archive is a separate recovery copy, not a published downloadable backup. A Git checkout needs the original LFS payload; a source ZIP containing its pointer is not an equivalent hydrated backup. `audit/baseline-file-manifest.json` records every protected file. The final offline check confirms **all 3,731 baseline files still have their original bytes**. New work is confined to `Assets/OkamiRemaster` and `tools/remaster`.

## Current Sunward project

Unity version: **6000.6.6f1**. URP: **17.6.0**. Input System: **1.20.0**, with the newer input backend selected. Cinemachine: **3.1.7**.

The inventory covers all project files under Assets, Packages and ProjectSettings, with **1,838 non-metadata asset rows**. A serialized GUID graph reaches 1,392 assets from Windflower. This graph does not resolve code-built objects or package dependencies automatically. There are 191 external/unresolved GUIDs, including package shaders and volume scripts; this number is **not a missing-assets count**.

`audit/replacement-matrix.csv` provides one row per asset, including its current path/name/hash, category, references, reverse references, scene reachability, source candidates, availability, conversion requirements, direct-integration status, gameplay risk and retention decision. Category candidates are not verified one-to-one replacements. **387 assets remain in the unclassified category**; they are explicitly retained. A file inventory is complete; asset-by-asset semantic equivalence is not.

| Current area | What exists | Remaster implication |
| --- | --- | --- |
| Main world | Windflower scene, 3,618 serialized GameObjects, generated town and environment review assets | Preserve placements, gameplay coordinates and collision contracts; stage visual changes selectively. |
| Player | Amaterasu prefab, current 74-bone rig, 47 animation clips, two controllers | Native 38-bone clips cannot be assigned directly to this hierarchy. |
| Architecture | TownV3 and House_A/House_B prefabs; authored village repair geometry, materials and painted maps | Use recovered demo architecture as source candidates, preserving entrances and routes. |
| NPCs | Seven named NPC prefabs plus scene shoppers; resident rigs, routes, dialogue, quests and shop functions | No verified original role-matched NPC replacements; retain all. |
| Combat | WolfCombat, WeaponDefinition, six enemy prefabs including boss, four waves | Visual adapters must retain attack schedules, hit detection, damage and spawning. |
| Weapons | Spear and Sundial prefabs/definitions; procedural disc positioning and effects | Preserve save IDs `spear` and `sundial`; replace only when native visuals and attachment/effects are verified together. |
| Terrain/water | Valley terrain sampler, bridge heights, river guard/depth, mill, water/effects | Preserve these APIs and physics; environment artwork cannot dictate gameplay heights. |
| Progression/save | GameFlow, SaveStore, upgrades, collectibles, flower quest, home/rest, mirror and shop | Keep `Sunward-Unity-v1.json`, revision handling, verified temporary writes and backup recovery. |
| Presentation | Existing UI/menus, camera, ink shaders, nine audio assets | Preserve bindings and recorded sounds; no verified Ammy audio replacement exists in these uploads. |

Protected gameplay includes movement, dodges, jumping, double jumping, equipment switching, light/heavy/charged/air attacks, interactions, arena entry, waves, Kurogane, rewards, permanent progression, save/load, home and all existing menus. Their source, scenes, definitions and serialized references are unchanged. **Runtime regression testing is still pending.**

The authored project includes Blender-generated prototype geometry and source tools under `tools/village`, `tools/ink-world` and `tools/source`. The prior village repair report records 15 houses, 21 trees, seven bamboo groups, 122 rocks and 540 groundcover placements; these are authored Sunward assets, not automatically original Ōkami geometry. Existing house preview images and exporter/source scripts are available. Standalone second-round house `.blend` files were not found in the mounted workspace; their exported demo geometry is available. Their unavailable source files have not been claimed as inspected.

## Original player library: pl.zip

The decoded library contains 16 packages, `pl00`–`pl0f`, with original MD geometry, DDS textures, native skeletons and MOT animation data. Full source inventories and research records are in `audit/pl-source`.

- `pl00`: default Ammy, **38 native bones**, four model sections, nine material divisions, 2,969 stored vertices and 2,183 triangles including ink components. Four texture slots are used by its geometry; the package also contains palette/auxiliary and dummy texture entries.
- `pl07`–`pl0f`: nine alternate forms using the same 38-bone hierarchy and byte-identical shared motion bank. `pl0c` is the realistic wolf, `pl0d` Shiranui, `pl0e` plain white and `pl0f` the green statue. File order is not a confirmed Karmic Transformer menu order.
- `pl01`: additional head model, 16 bones, no MOT bank.
- `pl02`, `pl03`, `pl06`: small/detailed/alternate Issun-related models with their own rigs and short motion banks.
- `pl04` and `pl05`: two humanoid models with 29-bone rigs; identities are unconfirmed. They are not approved village NPC replacements.
- 176 DDS images plus three ICO images, **179 images / 60 distinct pixel payloads** in the prior texture audit.
- Two duplicated sound banks contain the same seven very short Issun voice samples. No Ammy movement/combat sound bank was recovered here.

Default Ammy has **98 distinct shared MOT payloads**, all changing, repeated across ten compatible forms. Across all PL characters there are 999 MOT entries and 113 distinct payloads. These are real rig animation data, not weapon-only transforms. Numeric animation IDs do not supply reliable English action names by themselves. Walking/running/jumping/combat role mapping and native interpolation/timing still need verification against actual playback.

## Original weapon library: wp.zip

The final corrected audit covers **92 packages**. Missing numbers in the `wp00`–`wp5f` range are `08`, `0a`, `2f`, `5c`; gaps alone do not prove required files are missing.

| Primary / paired package | Weapon |
| --- | --- |
| wp20 / wp30 | Divine Retribution |
| wp21 / wp31 | Snarling Beast |
| wp22 / wp32 | Infinity Judge |
| wp23 / wp33 | Trinity Mirror |
| wp24 / wp34 | **Solar Flare** |
| wp25 / wp35 | Tsumugari |
| wp26 / wp36 | Seven Strike |
| wp27 / wp37 | Blade of Kusanagi |
| wp28 / wp38 | Eighth Wonder |
| wp29 / wp39 | Thunder Edge |
| wp2a / wp3a | Devout Beads |
| wp2b / wp3b | Life Beads |
| wp2c / wp3c | Exorcism Beads |
| wp2d / wp3d | Resurrection Beads |
| wp2e / wp3e | Tundra Beads |

The archive also includes auxiliary weapon/effect pieces and enemy-labelled motion banks. Every package is recorded in `audit/wp-source/catalog.json` with uncertain identifications kept uncertain.

- 92 MD entries / 78 distinct payloads; four additional duplicate embedded MD sets in large EMD containers.
- 154 DDS textures / **107 distinct** payloads, mostly 128–256 pixels, maximum 512.
- Of 861 entries labelled MOT, **839 are genuine mtb3 motion files**, 349 distinct. 327 distinct files change and 22 are static/constant. The other 22 MOT-labelled `_dummy` entries contain SEQ-like data, not animation.
- 440 explicit SEQ entries, 37 EFF, 74 TBL and **691 EST records / 192 distinct**. The corrected scan includes sparse TBL entries missed by the initial preliminary count.
- 37 EMD entries: 33 small header-only records and four identical large containers with native SCR and BRRES content. Not every EMD is a model.
- Four CAM copies contain one distinct sampled camera sequence.
- No verified audio samples were found in WP.

**Combat animation answer:** WP contains 274 genuine Ammy-labelled entries, **67 distinct**, with no payload overlap with PL's 98. Of those 67, 64 change and three are static. Reflector motions include `pl00_500`–`505` and secondary `510`–`516`; glaive and rosary families have their own ranges. These move Ammy's body, not just a weapon mesh. Combined PL+WP has **165 distinct Ammy MOT payloads: 162 changing and three static**. A preliminary count of 72 WP payloads included five distinct dummy sequences and is superseded by the verified 67.

Enemy-labelled data includes 220 entries / 164 distinct motions, but matching complete enemy replacement rigs are not verified. Weapon-labelled entries include many placeholders; they are not all independent combat actions.

## Solar Flare readiness

`wp24` and `wp34` each supply a 16-bone skinned weapon, 743 stored vertices and 517 triangles, six material divisions using three texture slots. Their geometry matches; artwork/usage variants differ. Source textures, weapon motions, Ammy reflector motions and nested effect/sequence data are available.

The native EST/SEQ effect dispatcher is **not fully mapped**. Flame emission rules, attachment/socket offsets, activation/attack/impact sequencing and complete trails are not yet verified. There is no recovered sound bank here. A textured static weapon is not a complete authentic Solar Flare replacement.

Therefore the current Sundial remains active. Its save ID, name, strike definitions, damage, durations, hit windows, ranges, arcs, lunges and equipment switching are untouched. Once a full replacement is verified, the adapter must switch the visual and disable the old SundialOrbit/custom disc effects together, preventing duplicate effects. The current combat code attaches visuals via the existing head socket; native back/weapon bones need a measured attachment adapter, not an assumed offset.

## Village integration prepared

Source: Village Breeze prototype commit `53b468f48ba0f91d46eb0f80d609713e7667a295`, derived from the separate Village Life project. Its source directory contained 548 copied asset/metadata files. Source GUIDs are retained, with **no collisions** against Sunward. The combined project has 206 Resources keys, also without collisions.

The review assets are under `Assets/OkamiRemaster/Village`. The original demo's Editor build scripts and ProjectSettings were excluded. Windflower remains the sole startup/build scene; input settings, packages, physics and global renderer settings were not changed.

The review scene can be opened with **Sunward → Remaster → Open Village Review Scene**, or directly at `Assets/OkamiRemaster/Village/Demo/Scenes/VillageDemo.unity`. The explicit menu protects unsaved scenes and refuses a scene switch during Play Mode. This is an additional Editor testing area, not an activated live-world remaster.

Changes made for compatibility:

- Ported all eight demo shaders to URP: painted surfaces, ground blending, water, foam, physical ink hulls, animals, petals and petting hearts. Preserved texture/UV mapping, source alpha artwork, flow/ripple/breeze math and ink hull normal/view clipping. Lit shaders use URP main-light/shadow functions; relevant cutout/deformed shadows have explicit URP passes. This is a source port awaiting shader compilation and visual review.
- Replaced legacy input calls in exploration, doors and petting with a null-safe Input System adapter. Kept keyboard/mouse actions, with explicit mouse pixel/wheel scaling. Sensitivity still requires an actual play test.
- Added explicit Editor asset validation, writing `Library/SunwardRemaster/village-asset-validation.json`. It checks imported shaders/materials and required resources; it does not call a gameplay test a pass.
- Kept the packed scene geometry, painted textures, door/stair/collision data, farm paths, animal animation bundle, blossom data and chime byte-for-byte identical to the recovered demo.

The village has **659 mesh batches, 2,877,511 stored vertices and 6,081,995 source triangles**. Inspection found 1,878,957 redundant indexed opaque triangles. The loader now removes repeated vertex triplets only for explicitly known opaque Cull Off review shaders, leaving every vertex, UV, color, material, transparent triangle and physics mesh unchanged. Independent triangle-set comparison predicts **4,203,038 submitted triangles**, a 30.9% reduction. This is not a measured frame-rate improvement or rendered equivalence approval. The remaining density and 659 batches still need profiling, visibility/LOD work and memory measurement before live-town adoption. Resources assets can also increase player build size even when the review scene is outside Build Settings.

Source provenance is mixed, deliberately recorded rather than labelled wholly original:

- Recovered ST2 bridge, torii, tower roofs, pavilion, rocks/pool and painted surface bindings are documented by source file/division in `Demo/ST2SurfaceBindings.json`.
- The original recovered tower had incomplete walls; Breeze adds five enclosed authored tiers around original roof geometry.
- The bridge retains recovered structural geometry and adds 27 authored, individually varied painted planks and stronger ink detail.
- Finished demo houses/hall/barn and furniture contain reconstructed/authored components using recovered artwork; they are not all directly extracted complete Ōkami buildings.
- Water uses recovered paintings and authored Unity flow/foam/splash/steam behavior; it is not a recovered native effect dispatcher.
- The quiet 0.48-second petting chime, heart art and some timber/steam artwork are locally authored, not original Ōkami audio/effects.

The farm includes **13 actors in nine asset types**: cow, pig, piglet, rooster, rabbit, panda-rabbit, dog, cat and boar. Native models/textures/rig data and converted idle/walk poses are included, with the demo's existing looping/grounding adaptation and authored patrol/petting behavior. This does not establish additional bird, fish, feeding or running assets. It does not populate Windflower yet. Doorways, petting reach/line-of-sight, stairs, rooms, bridge walking and animal grounding must be checked in the ported Unity scene.

## Native player/weapon review assets prepared

`Assets/OkamiRemaster/NativeReview` includes three `.okamimodel` diagnostic assets: default `pl00`, Solar Flare `wp24` and paired `wp34`. A reproducible exporter reads decoded MD/DDS files and preserves original positions, indices, texture slots, palette artwork, vertex colors, bone hierarchy and all three skin influences. The Editor importer creates skinned review objects and materials without binding to the live player. Native scale/orientation, source material flags, outline treatment and game-ready pose remain subject to review. Source MD files contain no normals; diagnostic lighting normals are derived from geometry.

The review shader is a painted diagnostic shader, not a verified reconstruction of the original MD renderer/material flags. These assets are not faithful final screenshots or approved replacements. No Animator, root-motion mapping, motor binding or combat adapter is automatically installed.

All **165 distinct Ammy MOT payloads** are copied intact under MotionSources, with hashes, numeric names, package aliases, frame counts and native loop flags in `motion-source-index.json`. They remain original source bytes, **not playable `.anim` clips**. 98 Solar Flare component records are also preserved with byte hashes; filenames include a digest to distinguish nested files with the same local index/name. No source effect records were silently overwritten.

Native curve interpolation, Euler order, source FPS, root motion, action mapping, weapon attachment and transition blending require verification before these motions can drive gameplay. Existing native preview evaluators are research tools, not an approved exact-timing Unity animation conversion. No generic motions were substituted for native files.

## Verification and limits

Offline checks passed:

- All 3,731 baseline file hashes unchanged, including scene, save/combat/movement code, NPCs, prefabs, controllers, clips and settings.
- New metadata and serialized references resolve; no GUID/Resources collisions.
- All 548 copied village files accounted for; exactly 12 have deliberate compatibility/loader source changes, with the rest unchanged.
- Packed geometry fully decoded; finite vertex/UV streams, valid triangle indices and material keys.
- Redundant-face analysis preserves the same indexed triangle coverage; collision and transparency streams retained.
- All original motion/component byte hashes verified; all three model streams validated, including independent bind-pose skinning cancellation. Geometry/rig/UV/skin arrays also match the prior independent parser, and converted PNG pixels match its decoded source textures.
- **90 C# files pass syntax parsing**, including the existing project. This is not C# semantic compilation.
- Eight shaders pass source-level URP/built-in-API checks. This is not shader compilation or platform variant coverage.

Unity is not installed in this environment. **No new Unity import/compilation, rendering, animation playback, gameplay, save/load regression, Windows build or performance test was executed.** The first review-stage runtime gate is therefore still blocked. New scripts/importers can affect project compilation even when their scene is unopened; the branch must stay a draft until real Unity results are available.

The latest published feedback inspected is run `20261021T092745607Z-9936e8`, commit `aefd595771e933a3313ecb4170251764c94ab1e3`, which predates this baseline. Its compilation report only proves the execute method was reached, not all shader variants. Its 12 screenshots and frame sequences from all 14 clips were reviewed. Every clip reports `frames_captured_coverage_incomplete`; the wolf is largely stationary, several screenshot cameras frame the whole world or obstructing rocks. None validates current motion or this remaster. Exact statuses are retained in `audit/feedback/review-index.json`.

No Windows tasks, installed runner copies, paid APIs, keys, automated receivers or PC syncing were changed or started.

## Remaining integration gates

1. Obtain real Unity 6000.6.6f1 import/compiler and shader results for this branch; fix failures before replacing live assets.
2. Verify the review scene's lighting, ink, transparency, controls, doors/stairs/bridge, animals, water and audio. Profile frame time, allocation, load time and build size.
3. Resolve exact architecture/vegetation/terrain matches from the matrix, including the 387 unclassified assets. Adapt a small Windflower visual batch while preserving all collision/navigation and quest positions; validate it before expanding.
4. Verify native MOT decoding against native playback/reference, assign confirmed action names/FPS, and build a 38-bone visual adapter compatible with WolfMotor/WolfAnimation/combat. Check feet, neck, tail, speeds, jumps, landings, dodges and transitions.
5. Complete Solar Flare EST/SEQ rules and attachment/action mapping; compare activation, flames, trails and impacts. Only then replace the live Sundial visual/effects as one recoverable change.
6. Bring proven animal/environment components into deliberate Windflower placements. Retain all current NPCs, roles, dialogue and navigation.
7. Validate arena visuals without touching wave/spawn/boss logic; run the complete movement/combat/NPC/progression/save/UI regression checklist on the exact final build.

No phase after the first Unity runtime gate is marked complete. The final game remaster remains open.

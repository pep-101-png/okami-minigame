# Windflower — visual asset remake

Target: Unity 6.6 / 6000.6.6f1. Previous project checkpoint: `bf27e8b`.

## Install this update

1. Keep a copy of your working Sunward-Unity folder. Close the Unity **Editor**; Hub can stay open.
2. Extract **Sunward-Unity-Restoration-Update.zip** into the existing project folder containing **Assets**, **Packages** and **ProjectSettings**. Allow replacement. Do not extract inside Assets.
3. Reopen Unity, wait for import/compilation, open **Assets/Sunward/Scenes/Windflower**.
4. Select **Sunward → Apply Visual Remake to Windflower** once. This is the NEW visual-only command. Do not rebuild Amaterasu or use an animation repair command for this update.
5. Check Console for the completion line, then **Sunward → Validate Visual Remake Connections**. Press Play and walk from home across the bridge to the market.

A newly extracted complete Sunward-Unity project applies the remake during initial scene generation. Existing scenes require step 4. The native scene cannot be serialized here because Unity Editor is not installed.

## Six requests — implemented changes and exact scene scope

| Request | Changes |
| --- | --- |
| Home and spear | Accepted bed/mirror/shelf/weapon-wall layout retained. Added a bamboo scroll, north-wall storage cabinet, celadon keepsakes, woven cushions and warm alcove light. Disabled ONLY old baked town spear material sections **Valley-743 through Valley-750**, separate from the wall rack and equipped weapon. |
| Floating rocks | Replaced eligible actual source stone islands with four original eroded rock meshes. Connectivity ignores dormant material-buffer vertices and welds UV seams for measurement. A real-data census finds **121 candidate stones, including 56 near the river**. Each foundation samples its own terrain/bed footprint and embeds its actual mesh bottom; no shared vertical offset. Architectural stone/lanterns/bridge fittings are excluded by source provenance. Full in-Unity inspection is still needed to establish that no floating stones remain. |
| Waterwheel | Existing wheel radius increased **15%**, raised by the same radius delta to retain immersion. Shaft, gears, spindle, upper/lower millstones and raised bearing supports move together. Added bronze rim fasteners, paddle shoes, bearing caps, timber braces and grinding pedestal. Existing rotation, transmission and spray remain connected. Wakes are added to the new water shader. |
| Hanging decorations | Replaced the old festival line with three properly supported sagging spans over open market paving. Five coordinated cloth/paper colours, seigaiha patterns, varied lengths, ink seals, cords and tassels. Wind pivots and capped, fading atmospheric particles. |
| Marketplace | Replaced the previous two-stall rendering with **four separately authored merchandise meshes**: flowers, produce, ceramics, textiles/craft tools. New joinery, braced posts, folded fabric canopies, scalloped valances, counters, shelves, lamps and shop pennants. Existing two merchants placed behind counters; two existing villagers browse shop-front routes. Original pentatonic music, market Foley and resident footsteps reused. Dialogue, shop identities and progression retained. |
| Actual world assets | Two original timber/shoji/tiled-roof house variants replace 14 matching village building groups at their existing footprints. The accepted accessible home stays intact. Four new branching tree variants replace 28 source trees with individual leaves/blossoms, four eroded rocks, bent grass and wildflower patches, and three new clothed resident appearances (all seven NPCs use the existing locomotion rig). Twelve original 2048px surface paintings and twelve linear normal-data maps. Actual terrain vertex relief shares its height function with movement. River shader rewritten for layered downstream normals, depth absorption, refraction, environment highlights, shoreline foam and bounded rock/wheel wakes. |

## What is connected

The migration operates on actual `Valley-*` renderers beneath **V3 · preserved painted valley**, hides the corresponding old building/tree/rock rendering, and writes native materials/prefabs under **Generated/Remake**.

New scene roots:

- **Windflower · visual remake**: replacement buildings, trees, vegetation, marketplace, festival spans, home detailing, mill supports and river-contact data.
- **Windflower · individually seated replacement rocks**: retained across repeated applications so filtering source stone triangles never loses replacement positions.
- Each NPC retains its identity/root, dialogue and **ResidentLocomotion**, with new skinned visuals beneath **Resident · articulated skeleton**.
- Existing **Windflower · village renovation** remains for the accepted home layout, equipment display, connected mill and original audio graph. Superseded stall/decorative renderers and colliders are disabled.

**VisualRemakeBuilder** is also called by initial scene generation, so this is not an unused asset pack. It saves a local pre-migration scene copy under `Review/LocalBackups`; use a complete previous project/Git checkpoint to roll back changed generated mesh assets as well as the scene.

## Assets and scripts

- Static library: `Assets/Sunward/Models/Remake/WindflowerRemake.fbx` — **19 assets**, independently named roots, facing datums, material sections; no wolf, skeletons or animation actions.
- Surface paintings: `Textures/Remake/{Oak,Bark,Plaster,Roof,Stone,Earth,Meadow,Indigo,Vermilion,Jade,Paper,Skin}` with matching normal data. Original generated artwork; no outside licensing dependency.
- New editor integration: `VisualRemakeBuilder`, `SurfaceIslands`, `RockSeating`.
- Existing editor changes: `EnvironmentGrounding`, `ResidentRigAuthoring`, `SunwardImportPolicy`, initial scene builder and legacy-spear exclusion in `WindflowerRenovation`.
- Runtime additions: `TerrainRelief`, `RiverSurfaceDetail`, `MillVisualDatum`. Valley/terrain data gains an opt-in relief flag.
- Shader changes: **Surface Pigment** supports uncoloured FBX meshes and new grass wind; **Brush River** has the new depth/current/wake shading.

## Checks and honest limits

Completed: portable C# syntax checks and gameplay/save regressions; actual source-stone connectivity/foundation census; numerical terrain/nav/bridge checks; Blender export/reimport checks for the new static FBX, material-section order, finite coordinates, UVs and absent animation/armatures; artwork integrity and package-content checks. Original wolf GLB, Blender project, Unity FBX/textures, animation processors and Three.js files are unchanged by this pass.

`remake-library-diagnostic.png` is an inspected **Blender asset-library render**, not a Unity screenshot or proof of the final scene's appearance. Roof gaps and sparse foliage found in its first version were revised before packaging.

**Not run:** Unity API compilation, shader compilation, scene generation/serialization, Play Mode, navigation/physics around new stalls, resident deformation and final visual review. Test those locally before treating this as an accepted game build. The source contains explicit connection/provenance checks that fail rather than silently omitting missing replacements.

**Remaining artistic limitations:** the new residents are original procedural stylised characters, not production-sculpted AAA humans. Full voice chatter, bespoke mocap trading interactions, screen-space reflections, tessellated terrain and a production hand-painted art pass are not included. The existing URP lighting/post-process setup is retained; no claim of a new global-illumination system or hardware-verified performance. Native visual approval is still needed for the terrain, rocks, wheel immersion and materials.

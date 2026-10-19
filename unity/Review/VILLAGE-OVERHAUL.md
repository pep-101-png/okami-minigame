# Windflower — village, locomotion and environment pass

Target: Unity **6000.6.6f1**, existing `Windflower` scene. Prior Unity version `6cae09b` remains in Git. This delivery changes only `unity/`; original Three.js and original wolf assets are not re-exported or replaced.

**Not a verified Unity build.** Unity Editor is unavailable here. Native API/shader compilation, generated scene execution, actual rendering, CharacterController physics, gameplay and FPS remain **REQUIRES LOCAL UNITY TESTING**. The implementation below is connected to the scene-generation/update pipeline; no completed visual acceptance is claimed merely because source exists.

## Apply to your current project

1. Close Unity. Back up your current project folder, including the locally generated scene/assets.
2. Extract **Sunward-Unity-Restoration-Update.zip** into that same folder containing **Assets, Packages, ProjectSettings**. Replace matching files. Do not extract inside Assets. This overlay includes the new audio and editor/runtime dependencies; the FBX and its importer metadata remain untouched.
3. Open with Unity **6000.6.6f1** and allow compilation/import to finish.
4. Open **Assets/Sunward/Scenes/Windflower**, outside Play Mode. Choose **Sunward → Apply Windflower Repair and Artwork Update**.
5. This revises the existing scene and generated assets; it does not create another town. It preserves source mesh data in `Data/Valley.bytes`, disables/replaces targeted old props, reconstructs only the owned renovation root and regenerates native clips. Your folder backup is the rollback for local scene changes.
6. The command saves world changes before the scale check, then runs scale/transition, imported-project, scene-connection, bounds and new village checks. If it stops with a red error, the Console tells you which check failed; later checks have not passed. Do not continue assuming success.
7. If checks pass, press Play and use the checklist below. There is no need for a full **Create or Rebuild V3 Scene** on an existing project.

A fresh full-project ZIP generates the same renovation on first import. This is a Unity project, not a Windows executable.

## The eleven issues

| Issue | Status | Actual implementation and remaining review |
|---|---|---|
| 1. Sleep | **PARTIALLY IMPLEMENTED / REQUIRES LOCAL UNITY TESTING** | `SleepClipAuthoring` now bakes `Sleep_Down`, `Sleep_Loop`, `Sleep_Up` in Unity space using fixed rest-length limbs, original paw/toe clearance, bounded elbow/knee floor contact, body lowering, distributed neck rotation, tail positioning and breathing. Three old imported sleep actions/legacy archives and FBX remain untouched. A read-only Blender clay rehearsal exposed raised elbows; the solve was revised to lower/extend them. Bone lengths/scales are constrained, but original skin-weight limitations, clipping and final natural appearance still require Unity inspection. Not described as a fully approved sleep repair. |
| 2. NPC walking | **IMPLEMENTED / REQUIRES LOCAL UNITY TESTING** | Original exported NPCs were static meshes. `ResidentRigAuthoring` creates actual 13-bone skinned copies of their existing surfaces, preserving originals disabled for rollback. `ResidentLocomotion` uses distance-driven gait, world-anchored stance feet, two-link leg solving, foot orientation hold, arm swing, torso/head idles and trading gestures. Two stallkeepers stay behind counters; Yui and the elder receive market routes. `VillageResident` retains dialogue/avoidance and checks new colliders. This is procedural skeletal locomotion, not authored imported NPC clips. Skin weights/robe deformation, turning and foot contact need real review. |
| 3. Home | **IMPLEMENTED / REQUIRES LOCAL UNITY TESTING** | Old combined interior is disabled and inner furniture triangles removed from generated copies. New west-side futon; unobstructed east-side mirror; separate west-wall spear hooks and disc cradle; east-wall collectible shelves; tatami and warm light. `HomeLayout` drives both visuals and interaction/sleep destinations. Weapons use original models/materials, measured/centred/scaled to mounts. Existing town/arena equipment state remains. Placement is designed, but final model bounds and walking clearances need native review. |
| 4. Wall clipping | **IMPLEMENTED / REQUIRES LOCAL UNITY TESTING** | `WolfBodyCollision` adds a horizontal body/head capsule sweep and guarded rotation around the existing upright CharacterController. `WolfMotor` routes ordinary/dodge/combat pushes through it and derives locomotion speed from actual displacement. Existing building/home wall and doorway colliders retained. Camera obstruction minimum reduced and near plane adjusted. Physics, tight turns, doorways, slopes and camera behaviour cannot be certified here. |
| 5. Floating rocks | **PARTIALLY IMPLEMENTED / REQUIRES LOCAL UNITY TESTING** | `EnvironmentGrounding` now welds coincident UV-seam vertices before whole-component placement and includes river rocks, instead of skipping all wet positions. Terrain grounding reports 193 moved decoration components in the actual source data. Architecture/bridge exclusions remain. This is not proof that every visible rock is now grounded; native riverbank sweep and any exceptional large/architectural component need inspection. |
| 6. Waterwheel | **IMPLEMENTED / REQUIRES LOCAL UNITY TESTING** | Frozen old wheel/awkward aqueduct beam are removed from visible generated geometry; its obsolete blocker is disabled. New double-rim bucket wheel follows the actual river curve, with submerged paddles, spokes, short axle, braced bearings, perpendicular 1:1 crown/peg transmission, vertical spindle, rotating upper/fixed lower millstone and small roofed mill annex. `WaterMillMotion` drives all linked axes from one phase; splash system connected. Mechanical mesh clearances, paddle contact, rotation direction and appearance need Play Mode inspection. This is purpose-built procedural geometry, not a purchased production asset. |
| 7. Tree wind | **IMPLEMENTED / REQUIRES LOCAL UNITY TESTING** | Existing actual tree groups identified by foliage materials. Per-renderer saved material copies set root height, independent phase and branch/leaf strengths in `Pigment.shader`. Height weighting anchors lower trunks; upper branches/crowns move with varied gusts. New road-edge flowers/grass also move lightly. Final amplitudes need native review; the borrowed shadow/depth passes do not reproduce every vertex wind offset. |
| 8. Hanging decorations | **IMPLEMENTED / REQUIRES LOCAL UNITY TESTING** | Old unsupported rope is disabled, old floating banners filtered. New market line has two grounded cedar posts, braces, explicit pendant cords and sagging rope clear of the central road. Tied paper/lantern ornaments move around their attachment pivots through `HangingWind`. Check old banner removal and roof clearance in Unity. |
| 9. Stone lanterns | **IMPLEMENTED / REQUIRES LOCAL UNITY TESTING** | Twelve source lantern locations receive rebuilt pedestals, solid chambers/recessed paper windows and properly closed 32-sided roof caps. Old open surfaces are filtered only in those small fixture volumes, excluding terrain/water. `RevolvedGeometry` shares poles/seams and makes real caps; no double-sided material workaround. New roof passes actual topology edge-closure tests. Warm local lights and weathered stone painting connected. All final views/shadows need native checking. |
| 10. Marketplace | **IMPLEMENTED / REQUIRES LOCAL UNITY TESTING** | Replaced old stalled geometry at both actual stall sites with counters, plank tops, braces, curved thick cloth canopies, valances, attached crest signs/lanterns, trays, produce, celadon vessels, baskets and shelves. Original new 48-second pentatonic synthetic plucked/flute-like music, 24-second Foley ambience, footsteps and distance/arena audio fade are included and referenced. No borrowed music or simulated claim of recorded crowd chatter. Stallkeepers and browsing routes connected. Balance, animation quality, navigation and audio mix need testing. |
| 11. Visual overhaul | **PARTIALLY IMPLEMENTED / REQUIRES LOCAL UNITY TESTING** | Actual targeted prop geometry, home/market composition, new plant clumps, caps, mechanical mill, lights and wind replace visible source fixtures. The prior real 1024px wood/roof/stone/plaster/meadow/path/water paintings and relief remain bound. No major terrain resculpt, wholesale building/tree replacement, baked GI, new 4K artwork, AAA asset quality or measured GPU improvement is claimed. A convincing high-end final look still needs a real Unity art/performance review. |

## Scale regression guard

The fresh-native-clip processor from the scale follow-up remains: explicit `.34` Animator-wrapper / `1` WOLF_RIG scale curves, original imported clips retained, no per-frame scale clamp. All non-sleep animation curves are checked for exact key preservation; only the three active sleep actions intentionally receive new deformation curves. Sleep limb local scales stay constant. `Validate Amaterasu Scale and Transitions` still checks all 47 actions and representative blends, including sleep and attacks. It has **not** been executed in this cloud; no guarantee that the user-observed native startup error is resolved is claimed without that check.

## Real available evidence

- C# syntax parsing and the 33 existing portable scale/combat/progression/save checks pass. These do not compile against Unity APIs.
- Actual shared `LimbArc` code passes 5,000 positive/unreachable-target length-invariant cases; rejects nonfinite input. No bone stretching is needed to reach targets.
- Actual `RevolvedGeometry` lantern-cap output passes finite/index checks and has exactly two incident faces at every edge, including pole and periodic seam. `lantern-roof-audit.obj` is that test output, not a game scene.
- Actual navigation/terrain code: seven safe source NPC positions, 30 river escapes, 10,001 finite bridge samples, obstacle checks and 193 grounded components. Physics is not simulated by the numerical shim.
- `sleep-solve-rehearsal.json` and the clay PNG are a **Blender-only geometric rehearsal**, not Unity renders, native animation testing or final material appearance. The rehearsal prompted a real revision; it still does not approve the skin deformation in Unity.
- New WAVs are real generated PCM files; durations/hashes/license are in `market-audio.json`. They are synthesized placeholders, not recordings of traditional instruments.
- Original FBX, GLB, Blender and wolf texture hashes checked unchanged. All new dependencies are packaged; ZIP CRC/byte inclusion checked before publication.

## Actual changed assets and integration

- Scene updater: `Assets/Editor/SunwardProjectBuilder.cs` invokes `WindflowerRenovation.Apply` for first-import and the existing-scene update. Existing Generated/Paint-* materials/Valley mesh IDs remain referenced; procedural replacements live under **Windflower · village renovation**.
- New editor authoring: `ResidentRigAuthoring.cs`, `SleepClipAuthoring.cs`, `WindflowerRenovation.cs`, `VillageOverhaulValidation.cs`; modified `WolfClipProcessor.cs`, `EnvironmentGrounding.cs`.
- New runtime: `WolfBodyCollision.cs`, `ResidentLocomotion.cs`, `WaterMillMotion.cs`, `MarketSoundscape.cs`, `HangingWind.cs`, `HomeLayout.cs`, shared `LimbArc.cs`, `RevolvedGeometry.cs`, plus `VillageWorldSolid.cs` registering the actual new prop collision bounds for navigation/recovery.
- Modified runtime: `WolfMotor.cs`, `VillageResident.cs`, `HomeRest.cs`, `GameFlow.cs`, `OrbitCamera.cs`; actual shader: `Shaders/Pigment.shader`.
- Actual new media: `Audio/market-pentatonic.wav`, `market-ambience.wav`, `resident-footstep.wav` and metadata. Prior art maps reused, not falsely relabelled as newly painted this pass.
- Local Unity creates native sleep `.anim` assets and `Generated/Renovation` mesh/material assets, resident skeletons/weights, world props and scene references. These cannot be serialized/tested without its Editor; the project delivers their full authoring pipeline/dependencies.
- New audits, tools and test reports are included; `overhaul-changed-files.txt` lists the exact delivery paths. No original Three.js/Blender source paths are changed in this pass.

## Local acceptance checklist

1. Run Apply, confirm no compile/shader errors and all native validators pass. If scale still becomes 100, stop and report its first error; do not shrink the model manually or disable animations to declare success.
2. Sleep/wake three times. Orbit both sides: unchanged paws/leg size, no bent-through torso, no hidden legs, futon contact and smooth recovery. Review especially the original skin weights at deep bends.
3. Watch every NPC's feet while moving, turning, pausing and trading; check robes/arms do not tear. Speak to all seven and use Taro's shop.
4. Walk/dodge into walls and turn near corners; enter/leave the home doorway, approach mirror/bed/shelves. Orbit camera against walls. Confirm neither invisible barriers nor body penetration.
5. View home displays from multiple angles, enter/exit the arena, switch both owned weapons and test light/heavy/charge/air attacks. Verify mouth empty back in town and save/progression preserved.
6. Inspect both riverbanks for remaining floating stones; test repeated water recovery and bridges. Watch mill full rotations for gear/paddle intersections and plausible spray.
7. Check tree bases remain still, crowns vary, every festival cord has a support and lantern roofs are opaque from above/below.
8. Browse market in daylight, hear the original audio near it, confirm fade at distance/in arena; inspect NPC routes around stalls.
9. Use F3 and Unity Profiler on your PC. New meshes are shared where appropriate; static objects are flagged for batching, materials enable instancing, particles are capped. Actual draw calls/FPS are unmeasured.

Keep your backed-up project until these checks are satisfactory. This pass delivers meaningful integrated changes, not a claim of final polish or native visual approval.

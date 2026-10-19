# Windflower — Animator scale repair and connected artwork update

Target: **Unity 6000.6.6f1**. This update follows `4b71188`; keep a copy of your existing Unity folder before applying it. `bc7306c` and the original Three.js source remain recoverable in Git. All changes in this delivery are under `unity/`.

**Unity Editor is unavailable here.** Native C# API compilation, shader compilation, generated-scene reference checks, Play Mode, visual quality and performance have NOT been verified. Implemented source/assets below are ready for local verification, not a claim of a fully repaired, visually approved build.

## Install into your existing project

1. Close Unity. Copy your current project folder as a backup, including its locally generated scene/assets.
2. Extract **Sunward-Unity-Restoration-Update.zip** into the existing project folder containing **Assets**, **Packages** and **ProjectSettings**. Allow file replacement. The overlay contains those folders' contents directly; do not extract into Assets or create a second nested project.
3. Open the same project with Unity **6000.6.6f1** and allow compilation/import to finish. The overlay does **not** replace `Amaterasu.fbx` or its `.meta` import settings.
4. Open **Assets → Sunward → Scenes → Windflower**, stop Play Mode, then choose the top menu **Sunward → Apply Windflower Repair and Artwork Update**.
5. This updates the existing scene/material/mesh asset references in place. It does not rebuild the town. It creates native animation copies and preserves the old controller once as **Amaterasu-SourceClips.controller**.
6. Read the Console result. The update invokes scale/transition validation, reference validation and bounds diagnostics. If it stops with a red error, use that first error; do not assume the rest completed.
7. Press Play. Check normal wolf size with Animator enabled, movement/jumps/dodges/heavy attacks, sleep/wake, river recovery, NPCs and arena entry/exit. Visually inspect the new timber, roofs, ground/path, river and noren panels.

For a fresh full-project ZIP, first-import generation builds Windflower with the same repairs/artwork. Use the in-place command above for an existing project; **Create or Rebuild V3 Scene** remains a deliberate full rebuild and is not required for this overlay.

## What caused the scale fault

The **raw binary FBX** contains 47 animation stacks and **141 WOLF_RIG scale curves, all constant 100**. The model's raw container also carries FBX unit-conversion scale. Blender's importer compensates those object curves back to 1, which is why prior bone-focused Blender checks missed the values that matched your Unity observation. This confirms a source of the reported fault; exact Unity binding behaviour still requires the native check.

`WolfClipProcessor` copies all 47 imported clips into native `.anim` assets. It removes **only Transform local-scale bindings on the Animator container or named WOLF_RIG container**. Deform/control-bone scales, positions, rotations, timing and clip settings are retained. The controller references the copies; the FBX/imported clips remain untouched. Reimport schedules the same processing again. No runtime script resets scale every frame. A one-time Editor-only reset handles an accidentally saved scale of 100, and a disabled scene Animator is re-enabled after validation.

**Sunward → Validate Amaterasu Scale and Transitions** samples all 47 actions at 13 phases plus representative transitions, against the authored `.34` visual-wrapper / `1` rig scale. This native checker was provided but **not run here**. It catches container size changes, not every skinning/visual defect.

## Feature status

“IMPLEMENTED” means source/assets connected through the existing builder/update path. All runtime/visual rows also **REQUIRE LOCAL UNITY TESTING**.

| Requested feature | Status | Delivered work / remaining limit |
|---|---|---|
| Animator-driven giant wolf | IMPLEMENTED; REQUIRES LOCAL UNITY TESTING | Non-destructive native clip processor, controller rollback, reimport handling and native scale/transition checker. Raw 141×100 channels diagnosed. |
| Original wolf and all 47 clips | IMPLEMENTED; REQUIRES LOCAL UNITY TESTING | FBX, original GLB, original Blender file and original wolf texture files unchanged. No mesh/skin/material redesign. Native copies created locally by Unity. |
| Terrain materials | IMPLEMENTED; REQUIRES LOCAL UNITY TESTING | New real 1024px meadow/path painting and RGB normal-data maps, world-space mapping and vertex-colour path blending on existing terrain materials. |
| Terrain shapes/environmental depth | PARTIALLY IMPLEMENTED | Existing shaped V3 terrain retained. Existing fog/lighting retained; no new terrain sculpt or landscape expansion. |
| Japanese building surfaces/details | IMPLEMENTED; REQUIRES LOCAL UNITY TESTING | New timber, tiled-roof and plaster paintings/relief on actual town material IDs. 18 gently moving noren panels and nine lintels at existing buildings; new timber on home mounts. No wholesale architecture replacement. |
| Rocks | PARTIALLY IMPLEMENTED; REQUIRES LOCAL UNITY TESTING | In-place terrain grounding (192 decoration components in numerical check), stone painting/relief. Rock topology not redesigned; each contact still needs visual inspection. |
| Trees, leaves, grass and flowers | PARTIALLY IMPLEMENTED | Ground painting and existing leaf/grass wind retained. No new tree/flower meshes or full vegetation asset overhaul. |
| River visuals | IMPLEMENTED; REQUIRES LOCAL UNITY TESTING | Painted current colour/normal maps, animated highlights integrated into existing depth/shore/refraction shader. Native rendering unverified. |
| URP lighting, shadows, AA, grading, particles | PARTIALLY IMPLEMENTED; REQUIRES LOCAL UNITY TESTING | Existing configured soft sun, SSAO/depth, AA, grading, fog, home light and petal drift retained. New painted relief/ink surface response. No baked GI, native profiling or 4K-art claim. |
| Both weapons, switching, light/heavy/charge/air | IMPLEMENTED; REQUIRES LOCAL UNITY TESTING | Existing original weapon prefabs and clip definitions preserved/reconnected; native clip copies cover heavy attacks too. Eight actual attack-chain tests pass. Sundial keeps its existing 110-coin unlock. Attachment, damage, appearance need Play Mode. |
| Home wall mounts and arena-only combat | IMPLEMENTED; REQUIRES LOCAL UNITY TESTING | Existing state-driven HomeWeaponRack/Combat systems retained; in-place command recreates the two original weapon displays and references. Town mouth empty/combat disabled; equipment appears in trials. Verify entry/exit and unlock behaviour. |
| Sleep repair | PARTIALLY IMPLEMENTED; REQUIRES LOCAL UNITY TESTING | Previous three revised FK sleep actions plus three legacy archives retained. All now pass through scale processing. **No further sleep reauthoring this pass**; leg deformation improvement cannot be claimed without native visual inspection. |
| River trapping | IMPLEMENTED; REQUIRES LOCAL UNITY TESTING | Existing shallow-water guard and timed safe-bank recovery retained, now also handles nonfinite XYZ via safe fallback. 30 numerical bank escapes pass; no swimming added. Repeated CharacterController escape/camera test outstanding. |
| NPC wall collisions/navigation | IMPLEMENTED; REQUIRES LOCAL UNITY TESTING | Existing safe spawn/steering; in-place command repositions residents and connects kinematic movement. Seven safe spawn tests pass. Dialogue retained. NPCs still lack skeletal walking. |
| Remaining unnamed NaN mesh error | PARTIALLY IMPLEMENTED | Prior bridge NaN source repair retained; named mesh input guards added to decoder/colliders/arena and effect inputs. A hierarchy/asset bounds diagnostic identifies invalid loaded objects. **Your current transient unnamed error was not reproduced, so its exact source is unresolved.** Scale 100 is finite and not automatically blamed. |
| Connected to playable Windflower | IMPLEMENTED; REQUIRES LOCAL UNITY TESTING | Builder/update modifies existing Generated/Paint-* materials and existing Valley mesh subassets, preserving GUIDs/file IDs. Numerical source mapping finds 160 actual TownV3 material IDs in five art families. Native menu checks live renderer maps, river maps, 47 clips and weapon/socket/display references. No disconnected demo scene. |
| Full high-fidelity artistic target | PARTIALLY IMPLEMENTED | Actual artwork and connected details delivered. Overall beauty/visual improvement has not been confirmed in a Unity render; broader asset sculpting/vegetation/lighting work remains. |
| Playable Windows executable / 60 FPS proof | NOT IMPLEMENTED; REQUIRES LOCAL UNITY TESTING | Project/overlay ZIPs supplied, not a tested Windows executable. No Unity or Windows Build Support available here. |

## Checks actually executed

- Raw binary FBX inspection: 47 stacks, 141 constant-100 rig-container scale curves. See `raw-fbx-scale-audit.json`.
- Roslyn syntax parsing for Assets C#; **not** Unity API compilation. Portable scale-binding, combat-chain and progression/save checks execute real pure C# rules (33 cases).
- Numerical world tests execute actual navigation/grounding code against actual V3 data: seven safe NPC spawns, 30 riverbank escape locations, 10,001 finite bridge-height samples, obstacle checks, 192 decoration components grounded. These are **not Unity physics tests**.
- Binary integrity: 1,110 source meshes, valid finite vertices/indices; 47 actions/catalog; original material bindings; original PNGs and 15 new 1024×1024 PNGs verified.
- Source hashes confirm original GLB/Blender/Unity FBX unchanged. No animation render or Unity screenshot is fabricated. Prior Blender round-trip reports remain historical evidence for the unchanged FBX, not a new Unity test.
- ZIP CRC/inclusion checks and source-file matching performed before publishing. `changed-files.txt` lists this delivery's actual Unity paths, including new art.

## Rollback

Your pre-update folder backup restores scene/material changes. The processor also preserves `Generated/Amaterasu-SourceClips.controller` and all original imported clips, but that old controller can reproduce the 100× fault: use it for inspection/rollback only. Existing Git history remains unchanged; no force-push or merge into the original game branch.

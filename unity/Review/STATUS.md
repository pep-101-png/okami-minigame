# Unity port — first implementation, pending real Editor verification

Branch: `sunward-unity-port`, based on the preserved V3 game `b55b1bd`.
Unity target supplied by the user: **6000.6.6f1**.
All port changes are confined to `unity/`. No existing game/viewer file is changed.

## Implemented source/assets

- Converted original Amaterasu FBX, 11 skinned meshes, six original texture maps
  and all 44 existing animation clips. No remodelling or replacement wolf.
- Automatic first-import Unity scene, prefab, Generic Animator, URP and data-asset
  construction. The scene requires Unity serialization, so the real `.unity`
  scene and generated assets are created by the user's Editor on first import.
- Native C# movement, Input System keyboard/gamepad bindings, Cinemachine camera,
  acceleration, turning, jump/double jump, falling, landing and dodge.
- Existing V3 town geometry/maps, physical terrain, riverbed and arched crossings,
  source colliders/NPC locations, home cutaway and windflower visibility groups.
- Custom URP surface-pigment, downstream water and calligraphic arena-energy
  shaders, soft-shadow configuration, fog, quality settings and runtime profiler.
- Spear/Sundial weapon data and visuals, light/heavy/charged/air attacks, damage
  windows, enemy hit reactions, bark stun, invulnerability and hit pause.
- Six enemy definitions, approaching/ranged/heavy patterns, readable windups,
  charges/slams/fans, three waves, two boss phases, rewards, victory/defeat/retreat.
- NPC dialogues, shop/equipping, permanent progression, windflower offering,
  resource recovery, sleep/wake, mirror save/load/browser-JSON import, future shelf
  registry, separate power-based curls and spectral trails.
- Existing legal wolf audio plus procedural action/ambient placeholders.

## Executed checks

- Converted environment binary: finite vertices, valid indices/submesh ranges,
  required assets/maps, home cutaway and all three flower groups.
- Blender FBX reimport: all 44 clips retained, original durations retained,
  valid geometry; maximum rest-surface vertex deviation about 0.0000011 Blender
  units. This is format round-trip evidence, not Unity visual approval.
- Roslyn syntax parsing of the Unity C# files. Portable progression and SaveStore
  code compiled and executed with .NET 8. The save tests use a test-only
  System.Text.Json adapter outside Assets, not Unity's JsonUtility runtime.
- Tests: purchase affordability/cost/caps, weapon unlocking/equipping, movement
  unlock, defeat retention, XP/power growth, verified file writes, backup loading,
  corrupted-current recovery, failed-import preservation and browser-shaped import.
- Official URP 17.6 metadata, Input System 1.20.0 tag and Cinemachine 3.1.7 changelog
  checked. The Unity registry itself is inaccessible in this cloud environment.

See asset-validation.json, fbx-validation.json and portable-tests.txt.

## NOT executed — necessary before claiming a verified playable Unity build

- Unity Package Manager resolution.
- Unity C# compilation against the actual Unity/URP/Input System/Cinemachine APIs.
- Shader compilation on Unity graphics backends.
- First-import scene/prefab/Animator generation in a real Unity Editor.
- End-to-end Play Mode checks, visual inspection, gamepad/device testing.
- Real GPU profiling or a 60 FPS measurement.
- Windows executable build. Unity/Windows Build Support are not installed here.

No screenshot from Three.js or Blender is represented as a Unity screenshot.
No Windows executable or visually approved Unity result is claimed.

## Still unfinished

- Real Unity verification and any fixes it reveals are the first priority.
- Joint-level procedural enemy/NPC animation has not been transferred. Original
  visual assets are reused with whole-visual motion, tells, hit/death reactions;
  this needs proper limb animation before calling enemies polished.
- Native slope-aware paw IK, stationary turn steps and more exact jump/air-action
  phase synchronisation need Play Mode/animation work. Existing clips are reused;
  the Unity state transitions are a first implementation.
- The source geometry is preserved, but exact material mapping, attachment
  orientation/scale, eyelid/rest pose, camera occlusion, collision placement and
  shader appearance need actual Unity visual review. The head/tail animation
  quality is inherited from the accepted library, not newly approved in Unity.
- River water is recreated in a lightweight custom shader with logical depth and
  bridge collision. Underwater plants/spray, nuanced wading audio and detailed
  shore polish remain unfinished; swimming is not supported.
- Source NPC/architecture/prop artwork is reused, not replaced by bespoke new
  high-quality Unity art. Improved visual quality over V3 has not been established.
- Mirror reflections are stylised source geometry/materials, not a real-time
  reflection system. Source save semantics are ported to an independent Unity file;
  browser progress is imported explicitly, never silently synchronised.
- No new background music composition, LOD authoring, occlusion bake, advanced VFX
  Graph or new combat/boss choreography. Audio/graphics presets are initial versions.
- Sleep, mirror, shops, arena completion, balance and long sessions all need real
  player/Editor tests. Do not describe these as verified runtime features yet.

## Local acceptance checklist

1. Open in Unity Hub with 6000.6.6f1, let packages/assets compile/import and allow
   first-import builder to finish. Resolve the first Console error if any.
2. Run **Sunward > Validate Imported Project**. Press Play, run it again. No pink
   materials, missing maps/bones or null references should appear.
3. Inspect the wolf in Idle/Walk/Jog/Sprint and turns. Orbit/zoom. Check paws,
   silhouettes and all weapon attachment orientations against the original.
4. Follow a curved village route, cross both bridges, approach river banks, wade
   shallow edges and verify deep water blocks entry. Inspect collision/grounding.
5. Enter home, sleep and wake. Check folded limbs/head, roof cutaway and weapons.
   Save, buy an upgrade, save again, stop/restart Play and reload the mirror.
6. Talk to NPCs, buy/equip Sundial Flame, collect flowers and offer at the shrine.
   Check double-jump unlock, power curls/trails and failed-purchase behaviour.
7. Enter trial; test light/heavy/charge/air attacks, bark, dodge, damage and tells.
   Clear three waves, both boss phases, victory and return home. Test defeat and
   retreat separately; earned progression must remain. Repeat difficulty increases.
8. Check gamepad movement/combat/menu navigation. Toggle F3 and both quality
   settings, profile on the actual Windows GPU, then build Windows via the menu.

Do not accept the visual quality or performance solely because technical checks pass.

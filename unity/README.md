# Sunward — Amaterasu Unity port

**Current targeted correction:** [Review/WATERSIDE-REPAIR.md](Review/WATERSIDE-REPAIR.md). Back up the project, close Unity Editor (Hub can stay open), extract **Sunward-Unity-Waterside-Fix.zip** into the existing project root and reopen **Windflower**. The rocks/pond/spear/market-tree correction applies and saves automatically once; **no Sunward update-menu step is required**. The broader visual-remake report remains available at [Review/VISUAL-REMAKE.md](Review/VISUAL-REMAKE.md). **Unity compilation/rendering/Play Mode remain unverified in this cloud.**

**Target: Unity 6.6 (6000.6.6f1), Windows. Separate project and branch.**

This is the first implementation of the Unity port. It includes real converted V3
assets and C# gameplay systems. **Unity is not installed in the cloud workspace:**
Editor compilation, shader compilation, Play Mode, visuals and Windows building
have NOT been verified. Do not treat this as an approved or finished Unity build.
The Three.js game and the standalone wolf viewer are unchanged.
Blender and npm are not needed to open or play the converted Unity project.

## Open and play

1. Extract **Sunward-Unity.zip** to a normal writable folder, such as
   `C:\Users\giuse\Desktop\Sunward-Unity`. Do not open it inside the ZIP.
2. In **Unity Hub → Projects → Add → Add project from disk**, select that
   **Sunward-Unity** folder (it contains Assets, Packages and ProjectSettings).
3. Open with **6000.6.6f1**. Let Unity resolve URP, Input System and Cinemachine,
   import the FBX/textures and finish compiling. Internet is required for packages.
   If Unity asks to enable the new Input System/restart, choose Yes.
4. A first-import Editor builder automatically creates the URP assets, materials,
   prefabs, Animator Controller, data assets and **Windflower** scene, then opens it.
   You do not assemble the project or wire components manually.
5. Use **Sunward → Validate Imported Project**, then press **Play**, and select
   **ENTER WINDFLOWER**. If scene generation did not run, use
   **Sunward → Create or Rebuild V3 Scene** once and read any first Console error.

The generated scene is `Assets/Sunward/Scenes/Windflower.unity`. It is generated
locally because a genuine Unity Editor is needed to serialize Unity assets.
The automatic builder does not overwrite a scene that already exists. The explicit
Rebuild menu regenerates the Unity scene/prefabs/controller; save your own edited
scene under a different name before using it. It never edits the Three.js project.

If compilation fails, copy the **first red Console error** with its file and line.
Do not delete your previous game or Blender files.

## Controls

- WASD / gamepad left stick: camera-relative movement.
- Shift / left-stick press: sprint. Ctrl / LT: slow walk.
- Space / A: jump. Second jump unlocks with movement upgrade level 2.
- K / B: directional dodge.
- LMB / RB: light combo. RMB / RT: heavy combo. Hold/release to charge.
- B / LB: bark stun. Q / D-pad right: switch owned weapons.
- E / X: talk, shop, sleep/wake, use mirror, collect windflowers or enter arena.
- Middle-drag / right stick: camera orbit. Mouse wheel: zoom.
- Tab / Select: upgrade journal between trials. Escape / Start: pause/close menu.
- Gamepad D-pad or left stick navigates scroll menus; A selects a button.
- F3: runtime FPS, main-thread time and draw-call display.

The home is on the west bank. Cross a bridge to Taro and the market; the trial
entrance is on the east road. Defeat three waves and Kurogane, return home, spend
permanent rewards and challenge the next tier. Defeat/retreat keeps earned progress.

## Saves

Unity saves to `Application.persistentDataPath/Sunward-Unity-v1.json`, normally
`%USERPROFILE%\AppData\LocalLow\Sunward\Sunward - Amaterasu\` on Windows. The mirror
shows the exact path. A verified temporary write and backup protect progress;
loading prefers the highest valid revision. Unity does not read browser storage.

Optional migration: open the old Three.js game in its usual browser/address,
open its browser developer Console and run:

```js
copy(localStorage.getItem('sunward.rpg.v2'))
```

At the Unity mirror choose **IMPORT THREE.JS SAVE JSON**, paste, then validate/import.
This imports known currency, XP, upgrades, equipment, ownership, windflowers,
collectible IDs and the three supported milestones. The old browser save is not
modified. Unity and browser saves do not synchronise automatically.

## What is implemented in code

- Native CharacterController, Input System keyboard/gamepad bindings, acceleration,
  jump/double jump, dodge invulnerability and Cinemachine camera output.
- The existing wolf converted to FBX, its six original texture maps, Generic rig,
  all 44 Actions, crossfades and speed-dependent playback. The source GLB/Blender
  files are untouched; no wolf geometry was authored or recoloured for this port.
- Actual V3 scene meshes/maps: sculpted terrain, curved paths, architecture, home,
  bridges, riverbed, gardens and distant scenery. No older rectangular town rebuild.
- Custom URP surface pigment, moving downstream brush water and calligraphic energy
  shaders; native soft shadows, fog, quality presets and runtime profiling display.
- Six enemy types with approaches, tells, charges/slams/ink projectiles, hit reactions,
  two boss phases, three waves, persistent rewards and return-home/victory/defeat.
- Spear and back-mounted Sundial Flame, weapon data assets, light/heavy combos,
  charging, air strike, damage windows, hit pause, knockback, bark and collision.
- Seven NPC assets/dialogues, shop, permanent upgrades, weapon ownership/equipping,
  windflower offering, resource recovery and progressive separate divine curls/trails.
- Rigged sleep/lower/wake Actions, mirror save/load/import and a six-slot future
  collectible shelf registry. Original wolf geometry remains intact at every power.
- Existing legal wolf vocal samples and generated placeholder action/ambient audio.

These are implementation contents, **not a statement that Unity runtime tests passed**.

## What still needs work

See [Review/STATUS.md](Review/STATUS.md). Most critically: first real Unity import,
C# API/shader compilation and end-to-end play testing. Visual quality has not been
reviewed in Unity and is not asserted to surpass the Three.js version yet. Native
slope-aware paw IK, polished joint-level enemy/NPC animation, bespoke new artwork,
real GPU performance profiling, balance and additional audio/music remain unfinished.

## Windows build

After local import/validation and play testing, use **Sunward → Build Windows x64**.
Output: `Builds/Windows/Sunward.exe` plus its adjacent data files. Share the whole
Windows folder. Install **Windows Build Support** for this Editor in Unity Hub if
that module is missing. No Windows executable was produced in the cloud.

## Organisation and developer checks

- `Assets/Sunward/Scripts`: independent movement, combat, AI, world, save, UI, home,
  audio and effect components. All MonoBehaviours have matching filenames.
- `Assets/Editor`: automatic project builder and imported-project validation menu.
- `Assets/Sunward/Models`, `Textures`, `Audio`, `Data`: converted local source assets.
- `Assets/Sunward/Generated`: Editor-generated prefab/material/Animator/data assets.
- `Tools`: repeatable read-only asset exporters, binary validation and portable tests.
- `Review`: evidence and explicit unverified/unfinished work.

Optional .NET 8+ portable checks, from this project folder:

```sh
dotnet run --project Tools/PortableTests
python Tools/validate-assets.py
```

Portable tests compile and run progression/file-save logic using a **test-only JSON
adapter**, and parse all C# syntax. They do not compile Unity APIs or run Unity.
For real Unity checks use the validation menu and the play checklist.

URP 17.6.0 follows the Unity 6.6 package family. Input System 1.20.0 and Cinemachine
3.1.7 are pinned stable releases. Official source metadata was checked; the Unity
package registry is blocked in the cloud, so actual package resolution remains
unverified. Do not remove package dependencies merely to hide import errors.

Original attribution: [Original credits](Original-credits.html) and
[third-party notices](THIRD_PARTY.md). No copyrighted Ōkami music was added.

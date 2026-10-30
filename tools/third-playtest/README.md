# Existing Sunward playtest repairs — 31 October 2026

This changes the existing Windflower scene and gameplay prefabs. It is a repair candidate for another playtest, not a verified finished remaster. Only original Ōkami media are used; code controls placement, visibility, scheduling and audio gain.

## Changes in this candidate

- **Rooster/global noise:** removed the two globally looping ST102 samples previously guessed to be wind/river. Those numeric samples were never identified as ambience. Actual rooster calls are positional, hard-cut beyond 3 metres, much quieter, and retain long animal cooldowns. Other animal calls remain positional. This removes two likely global animal broadcasters rather than merely lowering the farm rooster.
- **Footsteps:** lowered step playback gain from .60 to .045, about 22.5 dB quieter. No synthetic replacement audio was introduced. The previous original ADX decoding/clipping repairs remain intact; all 42 derivative audio files still match their audited hashes.
- **Music:** the 123-second original track heard by the user as battle music is now bound to arena battle playback only. The 7.65-second cleansing/result cue is no longer the arena loop. Unidentified outside/pub music is deliberately stopped. **Village and food-house background music are unfinished and currently silent**, pending positive identification of the original tracks. Duration alone is not treated as track identification.
- **Home:** HomeWeaponRack can no longer independently re-enable its generated weapon displays while outside. Static furnishing roots also follow the cutaway state. Tightened the inside bounds to exclude the porch/outside approach.
- **Dojo:** relocated the original offering shrine from inside the new hall to the outdoor path, and moved its interaction target with it. Kept the working NPC2/dialogue but relocated the old man outside the wall. Disabled the freestanding VT62 door marker and removed it from the list that could re-enable it. Existing venue entry/exit interaction remains.
- **Food house:** floor is level at Y=.40, just above the highest local terrain (about .35); actors, props, player floor, entry and sitting mat now agree. Floor surfaces hide when outside. Outdoor NPC navigation excludes both venue footprints so roaming residents do not appear through walls or underneath room floors. Replaced the prior cross-rig seated adapters in use with each actor's own original seated 003 action and its own arm rotations. Diners face the tables. The musician uses original arm gestures at the native instrument; **a dedicated original koto finger-playing action is still unidentified**.
- **Enemies:** actual prefab bindings changed: wisp uses em00_131, reed uses em00_132, boss uses em65_021. Rejected em00_133 after viewing it: it is a tumble, unsuitable as an attack. Heavy/ranged/elite retain their original 130 motions. Attack state durations now allow the native clip sections to finish rather than compressing them into a very short strike. Existing damage, health, reach, rewards and projectile counts remain; capped charge travel at its original .32/.65-second movement window even when the visible strike lasts longer. Longer native attack scheduling intentionally changes attack cadence. Exact original combat event markers/move-specific dispatch remain incomplete.
- **Swimming:** changed both swim bindings from the previous 01d/01e candidates to native pl00_013, with the existing deeper immersion and stroke timing. This is a different source motion, not another retiming-only change. Offline poses show a horizontal alternating paw cycle, but **its original action name and convincing swimming in Unity are unconfirmed**. This item must not be called verified fixed.
- **Shiranui:** doubled the existing approved body-surface Spirit/Glow emission rates (24→48 and 12→24). Kept the body-surface effect; no belly smoke/fire emitter was restored. Full original EST/SEQ effect dispatch remains incomplete.
- **Waterwheel:** selected intact VT6A group 1 instead of broken group 0 and bound actual full-turn native vt6a_001. Corrected precise MOT channels from the erroneous 50-based offset to native 0x30 (48). The original raw property 51 is rotation X, not position Y. Regression checks show a complete quaternion turn with constant bind Y. Scanning active bank source names found precise channels only in vt6a_000/001, so this decoder correction does **not** explain every character animation complaint.
- **Markets:** larger 6.4×4.4×5.2 original stalls, facing the approach; merchant roots centred at X=±7, Z=1.1 behind goods, using their own seated motions. VillageResident now honours those stations before its normal safe-spawn search, which previously pushed stallkeepers away from their own stalls. Shop approach targets moved with the stalls; existing purchase/progression systems remain.

## Files actually changed

- Scene: `Sunward-Unity/Assets/Sunward/Scenes/Windflower.unity`.
- Prefabs: `Generated/NPC-0.prefab`, `NPC-1.prefab`, `Enemy-wisp.prefab`, `Enemy-reed.prefab`, `Enemy-boss.prefab`.
- Native resources: HM00/01/05/09/29 seated motion banks; EM00/01 attack banks; VT6A intact model selection and rebuilt wheel bank; NativeAudio routing; NativePlayer swimming bindings.
- Runtime adapters: ValleyAudio, HomeCutaway/HomeWeaponRack, VillageResident/Navigation, GameFlow, EnemyBrain, OriginalActor/NativeVenueActor, NativePoseBank, VillageServices and OriginalAtmosphere.
- Source decoder and offline preview helper updated to reflect actual candidate data.

## Validation and limits

`verification.json` records 159 model resources, 43 finite normalized pose banks, 22 saved actor bindings, all saved references/Transform ordering, unchanged 353 existing collider components, 42 original-audio derivative hashes and syntax checks for 94 C# files. Saving, progression, player motor, world data, build scenes and enemy stat definitions are unchanged against rollback source `045e48e7f07054b81876c58fe5975cb4616c3139`. Root transforms, navigation exclusions and animation cadence are intentional changes.

Previews are **Blender diagnostics of the saved scene**, not Unity screenshots or play recordings. They cannot verify particle playback, audio, controller physics, compile/API compatibility or actual shop/door operation. Dedicated native koto action, original swimming identity, town/pub track identification and full native combat/effect dispatch remain open. C# syntax parsing is not Unity compilation.

Latest available PC feedback remains the older 21 October build, source aefd595…, with incomplete 14-clip coverage. It is not validation of this candidate. No Unity editor or access to the user's PC is available here. **Unity compilation, playability and audible balance are unverified**; please test these specific repairs in the existing game.

## Install and rollback

Close Unity and back up the working project. Merge the download's Assets into the existing Sunward Unity project, replacing matching files and keeping the rest. Do not delete or replace the whole Assets folder. Open the existing Windflower scene; no review/demo scene is required. The ZIP is cumulative against integration source `00fd8695363df01de80b012d68feb20c9961e8a9` and includes the previous remake/repair dependencies.

Source rollback point is `backup/before-third-playtest-20261031` at `045e48e7f07054b81876c58fe5975cb4616c3139`. Keep the project backup for local rollback; previous save format is preserved.

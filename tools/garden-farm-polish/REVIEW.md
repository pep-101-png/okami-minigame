# Garden, farm, UI and selected-bark update

Source baseline: `31c4e9213efb55549ac05cb2d06d26c970713fa1`, the preceding Desktop-project update.

## Implemented for play-testing

- User-selected PL00-41 from the original player bank is copied byte-for-byte from the listening pack, uniquely assigned to bark, with existing bounded gain and cooldown. Rejected puppy sounds are not routed to bark. No pitch synthesis or guessed replacement.
- Spirit race has thirteen original-effect checkpoints instead of six, with a 95-second limit. Reward prices increased from three tokens each to nine/twelve/fifteen; previously owned rewards remain owned.
- Pause/shop/HUD lettering uses the original glyph atlas. Original scroll body and roller artwork is assembled from its atlas rather than stretching the complete atlas. Generic visible label/button rendering removed; save-import text entry retains the existing input widget.
- Larger dialogue cloud and larger original lettering.
- Spa: original seated pose retained; cloth-raising arm layer removed, separate ornament excluded. A recovered original head track supplies gentle movement. This is not claimed to be a dedicated original bathing animation.
- Four identified leftover outdoor furniture colliders at Ammy's house disabled. Exterior walls, measured door corridor and isolated interior remain intact.
- Farm: VT4e weapon racks replaced by original r102/saku fence division. Complete original canopy proportions restored for stable/coops/hutch. Entire farmer camp and sleep route moved to the northeast farm, away from the arena. Repeated round beds replaced with one continuous original geometry bed and original earth/grass paintings feathered in world space, matching terrain lighting.
- Fifteen weapon catalogue pages: original-model portraits, handling descriptions, short lore summaries, ownership/purchase/equip actions. Summaries are newly written, not falsely attributed original item quotations.
- Upper arena extended from three to five regular-enemy waves. The victory cinematic shows the shaft reveal and fragment fall, original dust and adapted existing original landing feedback. This does not claim an identified native floor-collapse event sound. Skipping still opens access and restores control.
- River-mouth waterfall uses original r114 waterfall geometry/paint. The terrain and flat river painting open at the mouth; original cliff rocks and warp mesh give the drop depth. A short falling camera transition takes the player through the portal.
- New large isolated garden assembled from original grass-painted geometry, cloud dome, ponds, torii, ritual platform, shrine, vegetation and three original human skins. Two visitors use recovered original walking clips. Keeper explains established Shiranui/Nagi/Orochi lore and Sunward's new quest. Safe floor probing, local movement boundaries, river recovery exclusion and a return portal are implemented.
- Altar growth requirements: level 15 and thirty total upgrade ranks. The future guardian boss is explicitly pending and cannot be falsely completed. P remains available as the user requested for testing. Existing saves and level/stamina rules are preserved.

## Trailer — not an exported or verified video

An Editor-only 30-second sequence drives the real player input/actions: village day walk, farm dig, night festival, upper combat, weapon/strength purchase, Shiranui transformation, final-form boss combat/victory and original howl beneath an original moon mesh. Preview is available in Pause or Sunward > Trailer > Preview 30 seconds. Recording requests 3840×2160, sixty fps, 1,800 frames with high-quality MP4/audio through the existing capability-checked Unity Recorder adapter. It explicitly fails if Recorder/audio capture is unavailable, rather than reporting a file as completed.

Preview snapshots the profile/player/crops, suppresses disk save writes, and restores progress and input/camera settings. It refuses an active trial, festival, carrying/resting or cinematic activity. It does not alter a current game save to stage trailer combat.

There is **no Unity executable in this environment**. No MP4 has been rendered, exported, watched or probed, and no claim of AAA visual quality or smooth 4K/60 playback is made. Actual recording requires Unity and Unity Recorder on the rendering machine. No Recorder package was silently added to the working project.

## Validation

- Selected whole runtime drivers, including garden passage and visitor behavior, compile against explicit engine doubles: zero errors. Tests cover 915 boss/native checks, thirteen festival reward/time contracts, twenty-three prior village contracts and twenty-eight new garden/altar/race/collapse timing/skip checks.
- 310 extracted-method/native regressions pass for return/teleport/audio/camera/charge behavior.
- 371 farm/audio resource contracts; 398 previous native voice/UI/skin contracts; 250 new source/identity/content checks; 120 doorway contracts; 2,850 scene/resource/metadata checks.
- Actual island triangles cover the spawn, return portal, altar, visitor and pond positions, plus seventy-two points around the guarded perimeter, in offline geometry probes.
- C# syntax and duplicate-GUID audit run before packaging. These do not replace Unity Editor compilation.
- Original fence/canopy/waterfall and skin/pose diagnostic sheets inspected. These are original-asset previews, not screenshots of current gameplay.
- Latest GitHub feedback still references historical `aefd595...`; all fourteen capture entries are incomplete coverage. It does not validate this update.

The game ZIP contains changed `Assets/` files only. This review and source provenance are excluded from it.

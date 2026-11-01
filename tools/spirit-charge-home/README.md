# Held charges, boss exits and Shiranui cinematic

Source: the user-tested Desktop Tundra repair `72181d822f38cceed28650acf75ef95a0f7eb57e`, descended from actual Desktop upload `4dd2e730df2bc3fed3bf7d7998c81bca395c6fbe`. The user's clarification is that the charge freeze happens **while holding**, so released-cast pairings/timing are preserved.

Changes:

- `NativeCharge_tundra` now uses animated original PL542 instead of static PL540. `HoldChargePose` keeps Tundra's rate running; other weapon families retain their existing behaviour.
- Dedicated original WP2e swing/ice channels bound overlapping playback, use the same swing on normal/heavy strikes, and emit one contact accent per strike. Charged casts do not stack their own sound twice. Generic heavy-impact playback is removed from Tundra hits; enemy vocal gain is reduced. The source instrument recordings are unchanged.
- Finishing a trial and returning home no longer reload weapon assets before presenting results or teleporting. It cancels rest/cinematic routines, clears enemies/trial state, transfers to a surface point outside Ammy's home, closes the lower chamber, restores health/resources/time/control and resets the camera. Teleport resets falling/dodge/jump/velocity state and synchronizes physics. The lower mirror uses horizontal reach with a vertical floor guard rather than distance to an elevated decorative pivot. Result-screen exploration text now reflects the current chamber.
- P starts a 3.2-second skippable transformation on dry ground, using original PL04e raised-head animation, PL0d appearance, original Spirit/SpiritGlow/Spark/Leaf artwork, a player-bank vocal and WP2e burst cue. It pauses combat and ordinary UI, drives native animation/particles with unscaled time, reveals the form exactly once, and restores camera/lens/brain timing/control on completion, Escape or interruption. The existing Shiranui power multipliers and persistent spirit effects remain in place. Camera choreography and particle adapters are new Sunward code, not a recovered original cutscene.

## Validation and limits

`python tools/spirit-charge-home/run_tests.py` (.NET 8) passes 189 assertions. It compiles the actual NativeAmaterasu driver, native sampler and transformation timeline against explicit engine doubles. Exact current Finish, ReturnHome, Teleport, mirror condition, camera restoration and dedicated audio method bodies are extracted into controlled fixtures. Coverage includes both held inputs, 30/60/120 fps, normal/double attack speed, release, cinematic animation at zero world time, form switching, pause/result/death return states, raised mirror pivots, single audio voices, skipping, cancellation and re-entry. These tests do not run Unity physics, the camera renderer, audio output or the complete GameFlow/MonoBehaviour lifecycle.

The existing Tundra suite passes 4,147 assertions including unchanged definitions for fourteen other weapons. All 105 project C# files pass syntax parsing. New resource/GUID bindings and PCM peaks are checked. The new original player-bank recording has no output clipping; its exact named original event / howl classification has not been independently confirmed (see audio-provenance.json). No imported non-Okami wolf howl is used.

No current Unity editor/PC capture access exists here. The latest published feedback remains the 21 October source `aefd595771e933a3313ecb4170251764c94ab1e3`; all fourteen clips have incomplete coverage and cannot verify this build. Current Unity compilation, live collisions, subjective sound quality, arena escape and cinematic playback require play-testing. Do not call them Unity-verified.

## Trailer

`trailer/render_cinematic.py` renders the actual saved Windflower scene and original pose banks with Blender. `trailer/compose.py` assembles exactly 360 frames at 24 fps / 1280x720, original music and original sound cues into a 15-second MP4. Both the film caption and metadata identify it as a **cinematic preview**, not recorded Unity gameplay. The choreography is staged offline and cannot serve as gameplay or regression evidence. The source scene/animations/paintings are not edited. Helpers adapted from the existing project inspection/render tools are included for reproducibility. The output requires Git LFS media to be hydrated, Blender with NumPy/Pillow, FFmpeg with libx264, and the existing DejaVu fonts used by the editing script.

The user download contains Assets only, with no report, README, tool folder, scene replacement or save data. Its cumulative baseline is 4dd2e73 so it also includes the preceding tested Tundra repair.

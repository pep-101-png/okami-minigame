# Tundra Beads repair

Baseline: actual Desktop Windflower upload `4dd2e730df2bc3fed3bf7d7998c81bca395c6fbe`. The older Documents backup is not the source for this patch. No scenes, saves, native banks, models, paintings or audio files are replaced.

The original primary animations pair PL `544..54b` with WP `001..008`, each 0.96666664 s. PL `540` is a static ready pose; the previous chain incorrectly used it as a strike and skipped alternating body clips. Tundra now has its own eight-stage mapping. Heavy uses the eighth strike, airborne uses PL `54f`/WP `00f`, and charged casts use the six authored beads of WP `00c`, a complete number of PL `542` loops and PL `543` recovery. The last six beads are hidden during the six-bead cast and restored at rest.

A shared combat phase drives body and beads. The weapon samples after body sockets, blends from displayed poses on entry/cancellation/return, and pauses with the game. Air attacks cancel on landing. Leaving combat areas, swimming or locking the controller releases Tundra's action clock. Combo input has an early single-press buffer. Swept bead contacts replace Tundra's old broad radial damage check, with one hit per target per strike and the existing wall test. The original Tundra SES cues start with the swing, and impacts use existing original Spark/SpiritGlow artwork with a cold tint. This does not reconstruct original EST/SEQ effect events.

## Available verification

`python tools/tundra-beads/run_tests.py` requires .NET 8 and the baseline Git commit above. It compiles the actual catalogue, sequence, rules, pose sampler and weapon-view controller against explicit Unity math/resource/renderer test doubles. It covers all action mappings, dynamic body poses, native durations, 30/60/120 fps, normal/double attack speed, charged recovery, pause, return, interrupted cast bead restoration and unchanged definitions for the other fourteen weapons. It does **not** compile WolfCombat/NativeAmaterasu against Unity assemblies or simulate Unity physics/rendering/audio.

The run passed 4,147 assertions. All 103 project C# files passed a syntax parse; `git diff --check` passed. Offline original-pose sheets were rendered and inspected for all eight body strikes and primary/cast/air bead formations. Native near-ground bead samples exist for all eight strikes. These are diagnostic geometry checks, not Unity visual approval.

The latest available Unity feedback remains from 21 October, source `aefd595771e933a3313ecb4170251764c94ab1e3`; its fourteen clips have incomplete coverage and are unrelated to this Desktop baseline. Historical combat contact frames were inspected but cannot validate this update. No Unity editor or current PC recording is accessible here. Unity import/compilation, live collisions, target hit feel, interruption behaviour, Shiranui switching, audio and final visual polish require testing in the working Desktop project. Do not call this perfect or Unity-verified.

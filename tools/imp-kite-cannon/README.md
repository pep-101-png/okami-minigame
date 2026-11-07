# Imp kite and cannon follow-up — 7 November 2026

User feedback on the first imp update: the purple kite sits inverted in its owner; the Yellow barrel monkey lacks its proper ranged shot/explosion and attack variety. This follow-up covers all five imps. Only original Ōkami models, motions, paintings and recordings are used.

## Changes

- Purple/Red: native kite stance 180, movement/reaction 188, defeat 182 and three kite-specific combat motions 184/18a/18b. Generic instrument stances 000/010/020/032 are excluded from its installed bank; those fold the kite down through the torso/ground. Native mesh geometry, texture/UVs, attachment hierarchy and skin weights remain unchanged.
- Yellow: native preparation 150, short aim 151, fire/recoil 152, recovery 154. Bone 21's barrel mouth emits after this frame's pose is sampled. Bone 25 remains the hinged lid, not a projectile. The muzzle offset lies beyond the lid's bind-space face. Native 155/156 are close-range kicks. Inactive 164–166 are upright drumming motions and are not substituted for firing.
- The adapted explosive shell has a dodgeable locked aim, ballistic trajectory, swept collision, one impact/damage event, original fire/smoke paintings, muzzle flash and a separate impact blast. It respects pause, trial exit and the game's projectile cleanup. The generic boss projectile is unchanged.
- Native SEQ 152's sound ID 0x1cf maps to local SES cue 207, sample 7, ADX stream 2. The impact uses local cue 203/sample 3/stream 2, also authored in the barrel enemy's native sequence 167. Their original cue pitch ranges are -400..0 and -1000..-700 cents respectively; the player uses their midpoint pitches. This is a deliberate, documented impact adaptation, not a claim to run the original game's full enemy AI/EST engine.
- Green uses native 082/083, Blue 052/051 and Black 194/191. Twelve selectable combat actions in total. Existing native root height, instrument rigs, original pigments, frozen pose hold and interrupted-attack protections remain.

## Source provenance

`install.py` rebuilds installed banks from SHA-checked original MOT/SEQ/SES/DDS recovery caches. `provenance.json` records SEQ → SES cue → sample → ADX identities, waveform hashes/decoding and authored pitch ranges. CannonCore/Fire/Smoke are unchanged pixels from original fire_00/fire_15/smoke_00. The first two are whole paintings; only smoke_00 is a 2x2 atlas. Already delivered, now-unused recordings remain on disk to preserve cumulative Assets-only installation without deletions.

## Review and limits

`runtime.py` compiles the real game drivers with explicit API doubles, reconstructs the installed native skeletons, and captures their actual output. `review.py` renders those captured poses, actual shell trajectories and exact C# billboard mesh vertices/UVs/colours. Its 24-second, 30 fps preview includes scheduled Yellow audio with recorded pitch, gain and distance falloff. The review video stays outside Assets and is not an in-game trailer.

Reviewed encoded frames and 12 attack phase strips, plus front/side/rear kite movement, attacks, stagger and native defeat. The kite remains attached by its hand grips without the old generic inverted stance. The Yellow muzzle, opening lid, fiery flight, impact burst and both kicks are visible. The other three retain their body/instrument skinning while using distinct recovered motions. Frozen holds, interrupted attacks and defeat cleanup are included in the capture. A separate fixture exercises swept collision and one-hit explosions at 15/30/60/120 fps, pause and the actual production cleanup method. Conservation checks compare every installed pose to the recovery cache and every original pigment to its DDS. Broader existing gameplay regression checks remain successful.

This is an offline native-asset render of real driver output, **not Unity Play Mode footage**. Collisions use a flat test floor and an approximate player capsule; PC Unity rendering, scene collision, spatial-audio mixing and final subjective sound audition are not verified here. Latest available published Unity feedback is still from 21 October, source aefd595771e933a3313ecb4170251764c94ab1e3, with all 14 clip statuses marked `frames_captured_coverage_incomplete`; it does not validate this build. No Windows tasks were dispatched.

Run with the existing workspace caches:

```
python tools/spirit-charge-home/compile/check.py --dotnet /workspace/work/tundra-beads/dotnet/dotnet --dump-doubles /workspace/work/imp-kite-cannon/Doubles.cs
python tools/imp-kite-cannon/runtime.py
PYTHONPATH=/workspace/work/trailer30/deps python tools/imp-kite-cannon/verify.py
PYTHONPATH=/workspace/work/trailer30/deps python tools/imp-kite-cannon/review.py
```

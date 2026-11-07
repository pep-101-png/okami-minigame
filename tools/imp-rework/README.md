# Imp rework

This update targets the five imp variants, without changing Crimson Helm, player weapons, transformation ribbons or village art.

## Root cause and repairs

The old `[0,3]` mesh selection displayed rigid, simplified bodies. EM00/01/03/04 group 1 contains the articulated limbs, group 2 their matching ink shell, and group 3 the instrument. EM02 uses group 2 for its articulated body, group 1 for its outline, group 3 for its drum and group 6 for its animated drumsticks. The other bodies/instrument copies remain hidden. Original MD geometry, weights, UVs and DDS pixels are conserved.

The pose banks now retain original virtual-root **vertical** motion. Attack X/Z motion is consumed through the enemy CharacterController; the painted rig does not apply it twice. The jumping collider follows the visual root. Drum recoil respects the combat distance and arena boundary. Approach cadence follows the native walk distance, rather than repeatedly using the somersault clip as a run. Melee imps finish their native recovery before turning again.

Each instrument has its own native attack timing. Red uses its complete `184` paper sweep, replacing the long stationary tail in `181`. Yellow uses its recovered `150 -> 152 -> 154` preparation/shot/recovery sequence. Projectile release occurs at the source shot event. The others play continuous portions of their full native swing/kick, with damage at the corresponding contact. They enter actual attack distance first. Accepted hits cancel pending attacks into the recovered `020` reaction, with brief stagger immunity. Freeze holds the current pose exactly. Defeat uses `032`, then holds the fallen pose; the old `040` returned the imp upright.

## Original audio

`audio-provenance.json` records the SEQ sound ID, owning SES bank, cue entry, sample entry, ADX stream and hashes. Common imp events resolve through original `eb00.ses`; instrument events resolve through their own `em00`–`em04` banks. These replace the guessed short vocal and generic player-weapon swing on imp actions. Original ADX type-8 scales are decrypted before resampling; waveforms receive attenuation/DC removal/edge fades, without synthesis or pitch/time changes. These are source event bindings, not a claim to reproduce the complete original game's mixer or effect interpreter.

## Verification and limits

Run `recover.py`, then `install.py` against the existing SHA-checked original archive cache to rebuild the derived resources. The common enemy bank is the preserved `data_pc/se/eb/eb00.ses` from the user's `okami-hd-assets` repository; its source SHA is recorded with each dependent waveform.

`runtime.py` compiles the actual Init/state/pose/audio drivers. The test API simulates immediate prefab Awake, parent transforms, quaternion sampling, a flat floor and an approximate player capsule. It records 60 Hz sequences through approach, contact, recovery, freeze, interrupted attacks and defeat. A receipt ties captures to the source and assets; failed runs remove previous trace receipts. `verify.py` independently checks native DDS pixels, unchanged geometry/UV/pigment, articulated bone coverage, source pose data and recorded transitions. The broader existing regression harness covers related boss/player/progression behavior.

`review.py` renders the **captured C# bone poses**, rather than substitute animation choreography, into a moving review plus phase strips and encoded-frame samples. The review is an offline native-asset render. It cannot establish Unity shader appearance, actual Unity physics, performance or how audio sounds on the user's speakers. No current-source Unity Play Mode feedback is available; the latest published feedback is the older October 21 source, with all 14 motion captures marked coverage incomplete.

ZIP delivery contains only cumulative `Assets/...` payloads. Review video, receipts and tooling stay outside Assets and outside the game.

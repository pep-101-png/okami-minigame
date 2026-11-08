# Continuous spiral-to-curl handoff

The outgoing spiral eased to a stop before the folded curl began. The selected original MOT postures also carry different rigid torso facings, producing a visible reverse turn when blended directly.

Only `NativeAmaterasu.cs` changes in the game. Fold blending and the cinematic roll now overlap the last part of the rise from 1.6 seconds. The outgoing native torso frame aligns the postures while their original articulation blends, keeping the visible turn continuous. Alignment fades out at release. No source model, animation archive, sound, damage or blast timing changes.

## Review

`review.py` renders the actual C# driver outputs with original assets, the recorded main camera, and a fixed-world inset. The preview is normal speed, 30 fps, 7.4 seconds, with the existing audio. Inspected the handoff frame sequence and encoded preview frames. `verify.py` measures continuous projected rotation through 1.65–2.65 seconds and checks the early rise, approved release/landing, damage and audio timing against the previous capture. Actual-driver runtime assertions and awakening/combat regressions also succeeded.

This is offline rendering using Unity API doubles, not Unity Play Mode or verification on the user's PC. Latest available Unity feedback remains the older October 21 source build; its incomplete clip coverage does not validate this change.

## Delivery

`package.py` publishes the cumulative Assets-only ZIP from baseline `1ad16ca739d2a1f2ac3be3faabdedd9e8e00912d`, with the MP4 separately under Downloads. Neither review tools nor video enter Assets.

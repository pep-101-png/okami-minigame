# Approved charge sequence — 8 November 2026

The user selected: keep the current spiral ascent, then folded curl (option 3) rolling forward into airborne tuck (option 2), continuing forward during the final sun charge.

Only NativeAmaterasu's cinematic pose override changes in Assets. The approved rise is retained through 2.1 seconds. The displayed posture blends into original PL00_018 at 25% over 0.42 seconds, then into original PL00_021 near 65% from 3.05 to 3.65 seconds. A continuous eased forward carrier turns twice between 2.1 and 4.4 seconds while the source postures blend. This deliberately uses the selected posture from the backward-dodge clip without running its backward action. A small source-phase movement keeps the final tuck alive. The torso remains pinned to the sun centre; release unfolds to idle and restores the stored rig orientation.

The approved sun, light, camera, sound, explosion, damage timing, third-form requirement, once-per-arena rule, skip/cancel and Eighth Wonder are unchanged.

Fresh actual-source captures were generated using tools/solar-ultimate/runtime.py. The existing semantic and cinematic state tests succeeded, including 15/30/60/120 fps, centring, damage/skip/cancel and control restoration. verify.py compares the captured folded/tucked bone data to the original samples, independently unwraps the relative rig rotation to check two monotonic forward turns without jumps, checks unchanged ascent orientation, and verifies exact player restoration.

Reviewed the new encoded motion frames and complete original-asset sequence. The separate 7.4-second 30 fps preview includes a side-view inset of the exact captured body, plus unchanged scheduled audio. This is an offline native-asset render with API doubles, not Unity Play Mode; current PC rendering, collision and audio playback remain unverified. Latest available Unity feedback is still the October 21 source aefd595771e933a3313ecb4170251764c94ab1e3, with all 14 clips marked frames_captured_coverage_incomplete.

Reproduce after generating /workspace/work/solar-ultimate/Doubles.cs with the existing semantic harness:

```
python tools/solar-ultimate/runtime.py
PYTHONPATH=/workspace/work/trailer30/deps python tools/solar-ultimate/review.py
PYTHONPATH=/workspace/work/trailer30/deps python tools/ultimate-curl-tuck/verify.py
PYTHONPATH=/workspace/work/trailer30/deps python tools/ultimate-curl-tuck/review.py
```

# Ultimate release polish — 8 November 2026

The approved rise and folded-curl → forward airborne-tuck charge are preserved. The previous release blended the tuck straight to idle while floating down and unwound the player heading 300 degrees backwards.

This update unfolds the tuck into the original PL00_025 leap pose at the flash, then animates an inspected early segment of PL00_022 as the paws reach down. The late overhead stretch in that source fall is excluded. A short recoil leads into an accelerating descent, touching down at 5.95 seconds. Original PL00_02d supplies the landing compression before blending to idle and returning control at the existing 6.8-second endpoint. The heading finishes sixty degrees forward. The camera holds the big blast, then moves closer for the descent and landing.

Airborne poses remain centred; the final descent hands the visual root back to ground contact. A paw-joint floor guard prevents the transition from sinking, and fades away with the native landing/idle blend. The original quiet landing cue plays once. The explosion art/sound, flash damage time, third-form requirement, once-per-fight rule, skip/cancel, exact position/facing restoration and Crimson phase handling remain.

Fresh actual-source C# captures and offline original-asset footage were inspected, including encoded release, descent, compression and recovery frames. Iteration caught and corrected a sinking landing blend. verify.py compares all 139 pre-flash charge frames with the previously approved capture, checks the unchanged damage time, forward heading, landing cue, paw/root transforms and restored control. The prior chosen-posture/forward-roll audit, semantic regression checks and awakening/Crimson skip/cancel checks remain successful. All existing assets/audio bindings are preserved; no new external media is added.

The separate 7.4-second, 30 fps preview includes an actual-pose side-view inset, the recorded camera/effect output and scheduled original audio. It is an offline render using explicit API doubles and a flat test floor, not Unity Play Mode. PC scene collisions, dynamic lighting/tendrils, rendering performance and final speaker playback remain unverified. Latest published Unity feedback is still source aefd595771e933a3313ecb4170251764c94ab1e3 from October 21; all 14 clip statuses are frames_captured_coverage_incomplete. No Windows task was dispatched.

Reproduce with the existing workspace caches:

```
python tools/solar-ultimate/runtime.py
PYTHONPATH=/workspace/work/trailer30/deps python tools/solar-ultimate/review.py
PYTHONPATH=/workspace/work/trailer30/deps python tools/ultimate-release/review.py
PYTHONPATH=/workspace/work/trailer30/deps python tools/ultimate-release/verify.py
```

The preservation comparison uses /workspace/work/ultimate-release/approved-charge.json, copied from the actual accepted previous capture before changing the release.

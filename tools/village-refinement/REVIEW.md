# Village, brush and festival update

Baseline: `4f97a3f7bba4c92cfbba64aa6a3a99232f46a82f` (the preceding Desktop-project update).
The downloadable game patch contains only changed `Assets/` files and preserves prior updates.

## Requested behavior

1. Rejected AN05 bark removed from both routing and manifest. Three original AN05 samples remain unassigned listening candidates. No replacement has been positively identified; this request is unfinished.
2. Larger original noticeboard with original lantern, warm light and spirit marker.
3. Original dialogue bubble artwork, original Latin glyph atlas, progressive text and pagination replace generic NPC rectangles. Existing gameplay dialogue APIs retained.
4. Seven resident NPCs and the farmer now resolve dedicated original `hmXXv` voice bundles, instead of general action sound banks. Fifty-six short original syllables have source/output provenance, conservative gain, cooldown and spatial range. Identity is supported by bundle metadata; perceptual sound quality has not been heard here.
5. Welcome modal removed, replaced by original-logo title painting and any-button entry.
6. Persistent bottom instruction panel and trial/boss explanatory modals removed. Native glyph hints use translucent original ink artwork; boss reward and exit-mirror mechanics retained.
7. Three distinct original puppy packages AN05/AN22/AN25, each its own rig, poses and measured approximately 0.6m height.
8. Level and stamina rules unchanged: each level adds 4 maximum HP and 4.5 percentage points to base damage multiplier. Stamina pays for sprint and dodge, with upgrades adding capacity and recovery.
9. Cherry Bomb loop-with-fuse gesture, 25 ink, original ET07 model, timed radial blast and existing original effect sprites. The exact original explosion sound is unidentified and deliberately unassigned. This is a Sunward gameplay adapter, not a recovered original effect-script interpreter.
10. Original HM16 seated guest retains original seated pelvis/legs and layers the same rig's recovered `hm05_001` arm rotations. Previous `hm05_000` clip was confirmed static. This is not claimed to be a dedicated bathing clip.
11. Pond interaction uses original player sitting, green original spirit sprites and existing gradual 3 HP/s resting. Temporary maximum HP +25 lasts five minutes after standing; nonstacking, expires safely and clears on death.
12. Original intact VT4e pen rails, complete original r102 canopy sections, original wooden tubs/buckets/fodder replace broken cottage fragments and black basin/vegetation. Original rounded VT28 earth geometry and original earth paint form overlapping layered beds. Farmer gets an open canopy hut, futon, campfire, table and tea, with bedtime route. Incorrect static native-renderer bounds corrected.
13. Shaft requires victory in the current upper trial. Saved wins and peaceful walking never open it; current loss and leaving close it.
14. Festival intro/victory camera sequences, original effects, quiet existing original music passage, and floating spirit checkpoints with original collection cue. Countdown pauses during cinematic; control/camera and effects clean up on exit/skip. Rewards preserved.
15. Actual original logo/painting title screen, soft existing original music passage, keyboard/mouse/gamepad entry with input grace.

## Validation and limits

- Selected whole runtime scripts compile against engine doubles: 0 errors; 915 boss/native checks, 12 festival contracts and 23 village/brush/presentation contracts pass.
- 310 extracted-method regression checks; 4,155 Tundra checks; 120 doorway/source contracts.
- 2,732 scene/resource/metadata contracts; 370 farm/audio-resource contracts; 398 new voice/glyph/skin/motion/source contracts.
- Offline original-asset farm, title, bubble and spa-motion previews inspected. These are diagnostic renders, not Unity screenshots.
- No Unity Editor is installed here. Unity compilation, physics, final rendering, controller feel and audio listening are not verified. Historical feedback belongs to an older source build and does not validate this patch.
- Bark identity and exact Cherry Bomb explosion audio remain unresolved. No rejected or guessed replacement was assigned.

Provenance: `voice-provenance.json`, `ui-provenance.json`; source metadata remains in original model/pose payloads. The report and research are excluded from the game ZIP.

# Village and heaven update — source review

This branch is **unfinished and not an installable release**. Original gong,
thunder and room-music candidates have been decoded and presented to the user;
their identities/selections are unresolved. All media comes from original Ōkami
archives. No outside recordings or replacement drawings/models were introduced.

`review.json` records all sixteen requests and the remaining work. Do not package
or merge this branch as complete while its audio choices remain unresolved.

Implemented source covers the torii walk-through portal, original ET90 memory
mirror and celestial seal, four backed-up manual save slots, timed home blessings,
one cycling floating weapon display, original painted lightning, held-blade skull
clearance, the final-boss victory/howl sequence, continuous river gorge and entry
camera, orphan wall removal, house removal/rotation, separate room-music sources
and four-second house fade, the real-time day/night clock, skippable sky shots,
and own-rig native sleep loops for residents in their assigned houses.

The original ET90 effect curtain is hidden after bounds normalization so it does
not obscure the actual frame and stone circle. `OriginalSaveSeal` is the intact
天 cell from the original `kanji_kami` atlas. Thunder art is `kaninari4p_2` and
`biri_00`; timing is Sunward choreography, not a recovered native effect dispatcher.

## Verification

- Existing semantic suite plus actual clock, buff, victory and skip paths passes
  with C# engine doubles. It also exercises the actual room audio routing/fades.
- Actual WolfCombat hold/release/interrupt tests pass at 15/30/60/120 fps.
- Real SaveStore I/O tests pass in an isolated temporary directory, including
  slot independence, overwritten-slot backups, corruption recovery and old saves.
  JsonUtility uses a .NET adapter for these tests.
- `verify.py` checks actual scene world transforms, retired colliders, native asset
  preservation, audio importers, metadata uniqueness and native pose preservation.
- `blade_audit.py` samples original player/weapon geometry through the held pose.
- `render_scene.py` and `menu_preview.py` produce **offline diagnostic renders**,
  not Unity screenshots. The river diagnostic approximates native paint/masking;
  it does not reproduce Unity refraction, lighting or particle playback.
- No current-build Unity run or Windows play-test has been retrieved. Compilation
  against engine doubles does not establish Unity import or visual correctness.

## Rebuild cautions

`scene.py` starts from the base scene and is not an incremental repeat command.
The house rotation must act on its world-positioned parent, not rotate local
child positions around a world point. `terrain.py` reads base terrain heights
before sculpting and preserves current unrelated world boxes. Native archive
extraction scripts require the existing inspection workspace/cache.

Use `tools/spirit-charge-home/compile/check.py` to generate the engine doubles,
then `check_saves.py` and `tools/heaven-palace/check_combat.py` with those doubles.
Set DOTNET_CLI_HOME to a writable directory when running in the cloud sandbox.

# First playable scope and verification

Created on 13 October 2026 (Sydney). No existing game files were changed. The branch adds only `inkbound-2d/`.

The first chapter implements an original illustrated divine wolf, articulated locomotion and attack poses, a continuous side-scrolling riverbank, camera look-ahead, sprint/dodge/jump buffering, an unlockable double jump, a three-hit light chain, heavy/running/aerial attacks, three mechanically distinct weapon styles, six enemy roles including a two-phase boss, five drawn brush gestures, a water-and-Bloom gate puzzle, guarded seals, a breakable wall, nature restoration, optional high-terrace treasure, sun pearls, health/ink UI, pause/retry/victory, and locally generated original sound/music.

Revisions made after actual browser checks:

- Replaced rounded ellipse-only blossom clumps with irregular silhouettes and scattered small blossoms.
- Re-anchored Bloom recognition to the illustrated tree crown.
- Retained action inputs during hit-stop and allowed early combo buffering.
- Fixed walking out of the low riverbank so the wolf cannot fall through the higher connected bank.
- Locked enemy attack facing during tells/attacks so charges do not reverse to track the wolf mid-strike.
- Returned melee enemies to pursuit after recovery and aimed ledge archers at a grounded target.
- Kept controller held buttons separate from keyboard state.
- Added a compiled download launcher that uses only built-in Node modules, avoiding another npm setup for the player.

`validation.json` records focused browser checks on the compiled launcher. `playthrough.json` records a separate real-input route from the title to victory without position, health, unlock or enemy-state edits. Individual integration tests use fixtures; the full route does not. Browser tests include virtual controller input, not physical hardware testing.

The Windows batch launcher itself cannot be executed on this Linux machine. Its compiled static server is tested in Linux. The art remains a first-playable original Canvas illustration and has not been accepted by the user as final. There is no save-game system or additional chapter.

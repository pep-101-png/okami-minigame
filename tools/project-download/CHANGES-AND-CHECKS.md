# River & Lanterns — Windflower update

This pass improves the existing Unity game. It preserves Amaterasu's model,
materials, existing 47 animation clips, controller, progression and Windows sync.
Delivery is a complete project ZIP. A separate download branch packages it on
GitHub; the integration branch, PC syncing and installed tasks are unchanged.

## Implemented requests

1. All 13 original NPCs: rebuilt seven Japanese costume/face silhouettes; retained
   rigs, blended knee/elbow weights, bounded planted feet and gentler walking.
2. Both bridge decks: 54 separate coloured, grained, nailed boards each. Existing
   red rails, gold crests and their outlines are byte-for-byte preserved.
3. Added explicit ink shells to NPCs, new rooms/stalls, bridge decks, arena timber,
   bamboo and all six enemy families; completed the home shell outlines.
4. Swimming: buoyant dog paddling on the existing skeleton, including beneath
   bridges. Deep-water rejection and timed shore ejection removed. Collision,
   world limits and invalid-position recovery remain.
5. Double jump available without buying an upgrade, including a second jump after
   leaping out of water. Third jumps rejected.
6. Four patterned, orderly market stalls; paired shoppers with gestures and quiet
   spatial wordless chatter.
7. Wicker market dog bed: E rests and changes between morning and evening.
8. Twenty-minute day/night cycle, moon/stars, glowing lantern paper and eight
   bounded coloured lights. New lights have no realtime shadow cost.
9. Enterable enlarged Windflower training shrine, straw dummies and two samurai
   students with timed sword practice and quiet wooden impacts.
10. All 28 arena logs: grooved bark, knots, irregular profiles and cut growth rings.
11. Six spirit models with articulated limbs/ink contours, committed windups,
    pounces, sweeps, slams, projectile fans and wall-aware attacks.
12. Sundial attaches to the animated back instead of the head. Corrected centred
    spins and six pooled spectral flame ribbons; visible while equipped in the
    village. Home display stays intact.
13. Home shell outlines follow the existing indoor roof cutaway.
14. Existing wheel drives visible rice pounding and falling grain; the specific
    boulder intersecting its pillar is removed.
15. Waterfall moved to the actual river head, with a source cleft/feeder and flowing
    layered shader, replacing stationary offset cards.
16. Seven different seeded bamboo clumps, varied culm heights and many leaf fans.
17. Permanent bottom instructions/buttons removed. Health/level remain. Controls,
    interaction help and retreat are in the pause menu.
18. Enlarged enterable food hall, diner traffic through its real doorway, eating
    guests, a bowing violin performer, tables/tableware and an Ammy listening mat.
    Music is an original synthesized bowed-string approximation, not a recorded
    violin performance. E on the listening mat uses an authored seated pose.
19. Quiet noise-based paw takeoff replaces the jump ding; source jump timing fits
    the physical arc, with a rest-relative gathered-paw skeletal pose.
20. Checks and limitations are recorded below; gameplay success is not assumed.

## Evidence and limitations

- All project C# passed Roslyn syntax parsing in Editor and Player configurations.
  This does not replace Unity API/assembly compilation.
- Checked native vertex/index/normal/bounds/skin streams, local/GUID references and
  new runtime component bindings. Existing bridge sides and animation clips kept.
- Seven saved skins and 720 leg IK samples passed. Thirteen swim/jump policy cases
  and three-minute buoyancy simulations at 30/60/144 FPS passed.
- Room openings, floor boundaries, stalls, bed size, environment assets and enemy
  prefab identities passed the focused authoring checks.
- Blender stills of NPC costumes/weighted walk phases, wolf poses, spirits,
  environment details, rooms and stalls were rendered and visually inspected.
  They are asset previews, not Unity screenshots or continuous motion tests.
- Unity 6000.6.6f1 is unavailable here. Unity import/shader compilation, controller
  collisions, room traffic, continuous animation, sound quality, final lighting
  and hardware performance remain unverified. Recordings were left alone at the
  user's request. No claim of a completed autonomous visual validation loop.

## Reproduction for development

`python tools/living-world/build.py` explicitly authors the existing scene from
its reviewed artwork base, then applies environment, places, residents and combat.
It is not a runtime builder. Do not execute the older whole-project scene builder
to install this update: the delivered scene already contains the work.

Checks: `check_update.py`, `check_places.py`, `check_environment.py`,
`check_combat.py`, `test_residents.py`, `Check-CSharp.ps1`, and
`movement/Test-WaterMovement.ps1`. Shader contract checks are not GPU compilation.
No commands or authoring steps are required for the ZIP recipient.

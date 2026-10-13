# Sunward development to-do list

This is the persistent plan for future work. Update the checkboxes and notes as work is completed and reviewed. Passing technical checks does not mean the art or animation has been accepted.

## Agreed direction

- 2.5D: a controlled camera with a 3D town to walk around in.
- Aim for the supplied Ōkami reference: watercolor washes, visible paper grain, painted surface detail, irregular ink lines, simple low-poly forms, warm wooden architecture, green terrain, and saturated blue skies.
- Use original or suitably licensed assets. A local custom model and animation files are allowed; the earlier procedural-only restriction has been lifted.
- The wolf must look lean and canine, with fluid walking, running, and fighting. Rounded blobs, disconnected primitive shapes, rigid limbs, and mechanical movement have been rejected.
- Keep the long spear with a perpendicular side handle held in the wolf's mouth.
- Keep development modular so the world, NPCs, and combat can expand.

## Current state

- The published `sunward-minigame` game version has a village, four NPCs, dialogue, a fixed camera, an eastern combat grove, and a three-hit combo.
- The user considers the town version an improvement, but has rejected the wolf's shape and animations, including the later custom Blender draft.
- The rejected formula-built wolf was archived. This run replaces it with a licensed artist-rigged canine foundation and adapted painted wolf interpretation. Technical checks do not establish that the user likes its visual style.
- `wolf-design-review` contains screenshots and a motion preview of the rejected draft, not an approved design.
- This chat interface does not display outgoing screenshots reliably and does not provide usable project downloads. Use GitHub browser previews for review.

## Priority order

Work through these seven priorities in the user's order. The user authorized autonomous revisions, testing and publishing without further approval for this run. Later feedback still determines artistic acceptance.

## 1. Wolf animations and style

- [ ] Choose a well-designed rigged wolf with a verified walk/run animation demo; no replacement asset has been approved yet.
- [ ] Verify anatomy, proportions, skeleton, animation quality, format, cost, and permission to redistribute the asset with this GitHub project.
- [ ] Resolve access to the authoritative asset page; previous model-site requests were blocked.
- [ ] Show the candidate model and motion demo to the user before integration, and record the chosen source and feedback here.
- [ ] Create a lean canine silhouette: defined chest, tucked waist, shaped shoulders and hips, tapered muzzle, pointed ears, long legs, bent rear hocks, and a flowing tail.
- [ ] Apply painted ivory fur, expressive ink features, and red brush markings that follow the surface.
- [ ] Remove primitive seams, floating markings, distorted skinning, and texture/shadow artifacts.
- [ ] Create fluid idle, walk, run/gallop, turn, stop, jump, land, and dodge animations with planted paws and coordinated spine, shoulder, hip, head, and tail motion.
- [ ] Blend movement states smoothly and check them from the gameplay camera and a close side view.

## 2. Combat animations

- [ ] Give the opening thrust a readable windup, deliberate step, contact, and recovery.
- [ ] Give the second attack a planted pivot and sweeping strike with a distinct arc.
- [ ] Give the finisher a committed windup, whole-body lunge, impact, landing, and recoil.
- [ ] Keep the perpendicular spear handle held naturally in the mouth throughout every pose.
- [ ] Tune input buffering, combo links, movement during attacks, and dodge cancellation so the attacks flow together.
- [ ] Match hit timing, range, direction, and damage to the visible weapon motion.

## 3. Enemy animations

- [ ] Improve enemy idle and movement with believable steps and weight shifts.
- [ ] Add distinct anticipation, attack, and recovery poses so attacks can be read and avoided.
- [ ] Add directional hit reactions, stagger, and knockback that respond to the wolf's strikes.
- [ ] Add a defeat animation before the enemy disappears.
- [ ] Blend enemy states smoothly and keep their animation timing consistent with hit detection and AI.

## 4. Special effects and sound

- [ ] Add enemy death effects with a painted spirit release or ink dissolution, timed to the defeat animation.
- [ ] Add spear trails, impact marks, particles, and brief impact pauses that make successful hits clear.
- [ ] Add weapon swing/air sounds and distinct hit, heavy-hit, and enemy-defeat sounds.
- [ ] Add footsteps, jump/landing, and dodge sounds that match the animations and surface contact.
- [ ] Add suitable town ambience and simple volume/mute controls.
- [ ] Keep effects readable, avoid excessive screen shake or visual clutter, and test overlapping sounds.
- [ ] Start browser audio after a user interaction; use original or appropriately licensed sound assets.

## 5. General town tidy-up

- [ ] Improve house proportions, curved roofs, painted timber details, streets, greenery, and landmarks using the supplied reference.
- [ ] Replace repetitive or awkward placements with a more intentional village layout.
- [ ] Improve NPC designs, walking/idle behavior, dialogue presentation, and readable name labels.
- [ ] Fix clipping, blocked camera views, floating objects, awkward collisions, and unclear routes.
- [ ] Keep the village safe, the eastern combat grove easy to find, and exploration available after victory.

## 6. More watercolor paint style

- [ ] Put watercolor washes, pigment variation, and brush detail on the surfaces themselves.
- [ ] Use visible paper grain and irregular ink lines while keeping important shapes readable.
- [ ] Match the reference's warm architecture, green terrain, saturated blue sky, and strong painted silhouettes.
- [ ] Make the wolf, enemies, NPCs, buildings, terrain, and effects look consistent with one another.
- [ ] Reduce the dull washed-out look and avoid using screen filters as the only source of painted detail.

## 7. More things to do

- [ ] Agree on the first additional activities after the wolf, combat, enemies, effects, town, and art direction have improved.
- [ ] Consider NPC side quests, discoveries/collectibles, town interactions, and optional combat challenges; these are candidates, not committed features yet.
- [ ] Add clear goals, useful rewards, and feedback for the selected activities.
- [ ] Keep new systems modular and preserve the existing exploration and combat loop.

## Review, validation, and delivery

- [ ] Capture actual in-engine screenshots and a looping motion preview for each significant visual or animation revision.
- [ ] Upload review media separately so the user can inspect it on GitHub without downloading or installing the game.
- [ ] Collect feedback and revise; do not mark a rejected draft as an accepted improvement.
- [ ] Verify dependency installation, production build, local asset loading, and browser rendering.
- [ ] Verify movement, jumping/landing, dodge, NPC dialogue, collisions, combo timing/damage, enemy attacks/reactions, effects/audio, win/loss, restart, and continued exploration after winning.
- [ ] Publish the autonomously authorized update after meaningful validation; provide review media and keep subjective visual acceptance distinct.
- [ ] Provide the branch/download link and short Windows setup instructions, including the known Node path and esbuild script approval if npm requires it.

## Delivery notes

- Game branch: `sunward-minigame`.
- Review-media branch: `wolf-design-review`.
- Local project: `/workspace/okami-minigame`.
- User's Node folder: `C:\Users\giuse\Desktop\node-v24.21.0-win-x64`.
- Keep the user's working download until a replacement has been tested successfully.
- Save changes to this list without accidentally committing the unapproved local wolf/game drafts.

## Autonomous run implementation notes

The latest run implements movement/action blending, 3-stage combat windows and cancels, articulated enemy attacks and staged deaths, original sound/painted effects, richer town surfaces/NPCs, and a flower/shrine activity. See the build log and validation report for what was actually checked. These notes do not mark all visual goals as artistically accepted.

## Wolf-focused feature pass

Implemented for testing: visible animated eyes; growl/soft-bark/howl options and damage whimper; B bark stun; flowers/leaves during running; hold/release charged normal and heavy attacks; distinct right-click heavy animation; aerial dive; rise/fall/landing poses; sparse animated silk fur. Player feedback still determines the next anatomy/style and animation polish.

## Player review: wolf revision checklist (13 October 2026)

The previous nine-feature build was rejected for insufficient visual/animation quality. This revision is implemented for playtesting; subjective acceptance remains pending.

1. Refine visible eyes: narrower lids, restrained iris/highlight and painted brows.
2. Replace artificial vocals with local recorded bark/growl/cry cues; prevent the initial bark from disappearing during decoding.
3. Vary flower scale/color and soften leaf flutter.
4. Charged normal: low coil into a forepaw-raised pounce, separate windup and recovery.
5. Heavy: vertical overhead cleaver; charged heavy: deeper ground-breaking version.
6. Aerial: brief tuck/hang, nose-down spear spike, radial landing impact, dedicated slam audio and shockwaves.
7. Keep authored knee/hock bends; tuck paws at apex, reach on descent, absorb landing.
8. Broaden muzzle/shoulders, narrow loin, shorten fox ears, add painted spiral shoulder emblems.
9. Replace tiny wisps with a substantial layered, ink-edged mane, shoulder/ankle/tail tufts and varied flowing tips, guided by the user's Shiranui reference.
10. Leaf-shaped spectral spear blade, metal collars, wrapped grip, animated tassels, attack-specific pitch and pale spectral trails.

## Next-build feedback pass: connected combat and integrated wolf

Approved and retained: eyes, sound effects, item 10 spear artwork/spectral effects. Reopened numbers 1 and 2 now refer to combat, not eyes/audio.

1. Three-hit normal combo: stepping crosscut, counter-sweep, springing diagonal vault; larger shoulder/hip/leg participation, anticipation and recovery.
2. Two-hit heavy combo: overhead cleaver into rising return, buffered and recovery-window continuation; stop after two hits; dodge clears its state.
3. Running trail: sprouting green sprigs, elevated blossoms, ground flowers and wind-drifting petals/leaves.
4. Heavy penetration: soften the downward body pose, support the posed skin above ground and limit the weapon angle at the mouth pivot.
5. Charged polish: recoil/counterbalance and safe floor contact.
6. Aerial polish: reduced entry tuck, existing distinct spike/landing recovery and once-only slam.
7. Jump: gradual moderate leg flex, continuous apex pose, progressively reaching paws on descent.
8. Model/markings: sculpt rounded torso/shoulders; weld source triangles for actual smooth normals; replace atlas bands/badges with tapered curved markings projected onto the actual mesh UVs.
9. Fur: embedded, fading skin-triangle roots; neck/chest layers; correlated spatial wind and turning lag instead of independently oscillating fixed ornaments.

These are revisions for the next playtest. Visual acceptance remains pending.

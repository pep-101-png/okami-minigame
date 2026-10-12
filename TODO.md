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
- The latest custom wolf code and model are local, unpushed drafts. Their successful build and gameplay checks do not establish acceptable visual quality.
- `wolf-design-review` contains screenshots and a motion preview of the rejected draft, not an approved design.
- This chat interface does not display outgoing screenshots reliably and does not provide usable project downloads. Use GitHub browser previews for review.

## 1. Choose a better wolf foundation — highest priority

- [ ] Collect clear side, front, and movement references for lean wolf anatomy and the desired painted interpretation.
- [ ] Find a well-designed rigged wolf with an actual walk/run animation demo, or commission/model one with comparable quality.
- [ ] Verify the model's anatomy, proportions, skeleton, animation quality, format, and cost before integrating it.
- [ ] Verify the license permits including the model and animations in this GitHub-distributed project; compiled-game permission alone is insufficient for distributing source assets.
- [ ] Resolve access to the candidate asset's authoritative page. Previous model-site requests were blocked; no replacement asset has been verified or selected.
- [ ] Show the user the candidate model and its existing motion demo in a browser before another major implementation pass.
- [ ] Record the chosen asset/source, license, required attribution, and the user's feedback here.

## 2. Wolf appearance and animation

- [ ] Create a coherent silhouette: defined chest, tucked waist, shaped shoulders and hips, tapered muzzle, pointed ears, long legs, bent rear hocks, and a flowing tail.
- [ ] Apply painted ivory fur, expressive ink features, and red brush markings that follow the body surface.
- [ ] Remove visible primitive seams, floating markings, distorted skinning, and texture/shadow artifacts.
- [ ] Implement a readable walk with planted paws, natural leg articulation, and weight transfer.
- [ ] Implement a distinct run/gallop with coordinated spine, shoulder, hip, head, and tail motion.
- [ ] Blend idle, walk, run, turns, stopping, jumping, landing, dodge, and combat without abrupt pose changes or excessive foot sliding.
- [ ] Check motion from the actual gameplay camera as well as a close side view.

## 3. Combat rhythm and responsiveness

- [ ] Improve the quick opening thrust with anticipation, a deliberate step, contact, and recovery.
- [ ] Improve the second attack into a planted pivot and sweeping strike with a visibly different arc.
- [ ] Improve the finisher with a readable windup, whole-body lunge, impact, landing, and recoil.
- [ ] Keep the spear grip attached naturally to the mouth throughout every pose.
- [ ] Tune input buffering, combo links, movement during attacks, and dodge cancellation against the animation timing.
- [ ] Align hit detection, range, direction, and damage with the visible weapon motion.
- [ ] Tune brief impact pauses, enemy stagger, knockback, attack cues, and effects so combat feels responsive.

## 4. Painted town and exploration

- [ ] Improve watercolor surface textures and brushwork rather than relying on an outline/grain filter alone.
- [ ] Refine the village composition using the supplied reference: warm timber houses, curved roof silhouettes, greenery, paths, and recognizable landmarks.
- [ ] Keep the town larger than the combat arena, with connected streets and space to explore.
- [ ] Improve NPC designs, readable dialogue/name labels, and walking/idle behavior.
- [ ] Keep the village safe and the combat grove accessible; allow exploration after victory.
- [ ] Check the controlled camera for blocked views, readable character scale, and consistent movement controls.

## 5. Review, validation, and delivery

- [ ] Capture actual in-engine screenshots and a looping motion preview showing walk, run, turns, and all three attacks.
- [ ] Upload review media separately so the user can inspect it on GitHub without downloading or installing the game.
- [ ] Collect feedback and revise; do not label a rejected draft as a completed improvement.
- [ ] Verify dependency installation, production build, local model loading, and browser rendering.
- [ ] Verify movement, jump/landing, dodge, NPC dialogue, building collisions, combo timing/damage, enemy attacks, win/loss, restart, and continued exploration after winning.
- [ ] Push the game update after the user has reviewed the visuals and motion.
- [ ] Provide the new branch/download link and short Windows setup instructions, including the known Node path and esbuild script approval if npm requires it.

## Delivery notes

- Game branch: `sunward-minigame`.
- Review-media branch: `wolf-design-review`.
- Local project: `/workspace/okami-minigame`.
- User's Node folder: `C:\Users\giuse\Desktop\node-v24.21.0-win-x64`.
- Keep the user's working download until a replacement has been tested successfully.
- Save changes to this list without accidentally committing the unapproved local wolf/game drafts.

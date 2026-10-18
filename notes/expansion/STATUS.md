# Sunward RPG expansion — continuation checkpoint

## Implemented and connected

- Existing town expanded westward with bridges, gardens, bamboo, lanterns, five additional houses and three additional villagers. Open-door home with resting mat, altar and weapon display; no scene loading.
- Painted kimono NPCs replace the old block-shaped figures; existing routes/dialogue/flower offering retained. Taro sells eight permanent upgrade tracks and Sundial Flame.
- Spear retained. Sundial Flame has shorter radial combos, its own rigged attack poses, painted flames and independent upgrade damage. Weapon ownership/equipment save.
- Three mixed enemy waves followed by Kurogane, the Hollow Bell: charge, shock slam and ink fan; faster second phase. Six spirit types, readable tells, hit/death reactions, between-wave breaks, victory/defeat/retreat and return home.
- Coins and XP from kills save immediately. Levels, purchased stats, weapons, shrine blessing and wins persist. Versioned, validated localStorage with backup recovery and storage-failure feedback. Repeat trials scale.
- Saved power gradually enables separate shoulder/ankle curls and spectral strokes. Original wolf vertices, UVs, materials, textures and skin weights are not edited.
- Original wolf exports 25 existing Blender movement/jump/dodge Actions. Sixteen game-only spear, disc, charging and bark Actions reuse the existing rig and IK helpers. The source Blender project is never saved or overwritten.
- Camera orbit/zoom, stamina sprint/dodge, energy bark/charge and permanent double-jump unlock. Paper wash lighting, brush barriers, painted projectiles/hits and parchment shop/journal/results.

## Recovery and protected work

`sunward-pre-expansion` preserves the starting game commit `2ba1f2b7f829145334a261f7a0fc36d80f39b29e`.
The original Blender movement source is `original-wolf-jump-dodge/Amaterasu-Movement.blend`, SHA-256 `5e24c750d5c31e1ba071f3290927bc3006d9b4bcd4628aba59bff96fc6f5aa0e`.
Original game models and standalone viewer files are unchanged. Existing uncommitted viewer studies are deliberately excluded from this branch's expansion commit.
The GLB exporter requires that source project (available on branch `amaterasu-jump-dodge`) plus the included IK helpers; the ordinary game needs only the committed GLB.

## Verification

- Pure progression tests: purchase affordability/caps, ownership, reward retention, save recovery/migration, malformed fields and unavailable browser storage.
- Chromium integration: movement/jump/dodge, walk-through home, rest, actual shop buttons, reload persistence, unlocked double jump, arena boundary, enemy tell and player damage, weapon strikes through all waves/both boss phases, victory/home, harder repeat trial, defeat retention and saved-power fur.
- Automated wave-clear uses temporary invulnerability to isolate offensive/reward mechanics. It is not a human balance playthrough. Player damage and defeat are checked separately.
- Production build and the extracted play ZIP are checked, including local model/audio requests. Native combat authoring records sampled IK error/paw-floor checks in `combat-export.json`.
- Browser visuals inspected separately; no claim of universal 60 FPS, Windows execution or final art approval. Software WebGL in this cloud is not representative of a gaming GPU.

## Next work — genuine unfinished polish

1. Human playtest progression costs, stamina/ink economy, enemy density and repeated-run difficulty. Add a tutorial/map and controller support if wanted.
2. Hand-polish combat poses and moving charge blending. Existing new clips are functional IK-authored first versions, not final authored cinematic combat.
3. Bespoke NPC faces/hair/cloth deformation and varied buildings. The town is an expanded procedural painted environment, not a complete hand-authored art pass.
4. Fur attachment deformation and curl layering at extreme poses; check minor prop/weapon intersections. Growth is additive; source wolf remains exact.
5. More elaborate battle calligraphy, brush-dissolve particles, distinct boss defeat staging and richer encounter scenery. Current barriers animate/dissolve by ribbon scale and opacity.
6. Test real Windows launchers and a broader set of GPUs/resolutions. Add quality presets if needed; no hardware frame-rate guarantee.
7. Save export/import/cloud sync. Current saves are browser/origin-local; users must retain site data and use the same address/port.

No changes to the standalone browser viewer, its deployment or the original Blender projects are included.

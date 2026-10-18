# Painted Valley — environmental art checkpoint

## What changed

The previous playable RPG is preserved at `6f4f90a` on `sunward-before-art-overhaul`.
This pass changes the existing world's art and rendering. It does not replace the game.

The guiding principles are ink as shape/gesture, layered translucent pigment,
restrained warm accents against cool landscape washes, paper/negative space, and
reduced contrast with distance. Existing user-provided Ōkami and sumi-e references
informed these principles; no game textures or copyrighted music were copied.

- **Surfaces:** original seeded canvas brush textures, anchored object/UV-space
  pigment variation, edge pooling, dry-brush highlights and broken ink shells.
  A smoother lighting ramp supports the pigment rather than serving as the only
  style. The old screen-space edge filter is removed; only restrained grain and
  vignetting remain. The art persists through camera rotation because it is on
  the surfaces, not a screen overlay.
- **Architecture:** curved hipped roofs, raised corners, layered eaves, tile rows,
  ridge ornaments, verandas, rafters, diagonal supports, sliding-door rails,
  lattices, stone plinths, ribbed paper lamps and original painted wall scrolls.
  The shrine retains its taller layered silhouette and gains rope/shide details.
  Amaterasu's home has a moon window, veranda and extended canopy; its cutaway
  keeps the interior usable. Taro has a dedicated indigo roofed pavilion.
- **Terrain:** one 2048 × 1536 nonrepeating painted valley atlas, soft path fringes,
  varied meadow washes, an irregular arena wash, grassy terraces and rock banks.
  The traversable floor stays at its existing physical height. Decorative raised
  meadow islands have matching solid collision rather than invisible walkable hills.
- **Vegetation:** old flat blossom sprites are hidden. Twenty-one branching trees
  use tapered calligraphic trunks and dimensional, instanced painted leaf clusters,
  including cherry, maple and pine. Seven bamboo groves, instanced grass/flowers,
  softer garden beds and ground washes enrich the landscape. Leaves, branches,
  grasses and instanced petals across the whole village move gently; foreground canopies fade to keep the wolf visible.
- **Water and horizon:** flowing brush-current river, original bridges, a lotus
  garden pond, a falling-water wash, tiered cliff/forest boundaries, layered ink
  mountain silhouettes, illustrated clouds, a muted sun and low valley mist.
  World collision limits are retained and backed by visible landscape boundaries.

## Protected gameplay and assets

The original wolf GLB remains byte-identical (SHA-256
`dbb683222afcb3cfdfe675a6882114ebd53c14e485de28d2607256ea274be921`).
Its geometry, skinning, materials, textures and 41 animation clips are not edited.
Scene illumination changes with the rest of the world; no pigment shader is
applied to the original skinned wolf materials. Existing attached weapons/effects
continue to use the game's painted materials.

No Blender project or standalone `wolf-viewer` source/asset is changed. The save
format/key, shop, NPC dialogue/routes, home access, combat, waves, boss, currency,
upgrades and victory/defeat loop remain. New play builds use the same local port;
keep the same browser/address/site data to retain progress.

## Verification and visual review

See `verification.json` for the current results and `review/` for representative
before/after screenshots. Six fixed camera comparisons plus two garden detail views are used: home exterior, market,
river/bridge, arena, home interior and mountain horizon, with additional pond and meadow-terrace views. Rendered images were
inspected separately from compilation and geometry checks. An intermediate bad
cliff colour was traced to batching dropping vertex colours and repaired. Excess
roof-curve tessellation was reduced substantially before delivery.

Checks cover finite geometry, outward rock winding, meadow normals, absence of meadow plants indoors, original wolf material exclusion, stationary surface
texture offsets during updates, all four physical world edges and unchanged clip
availability. Gameplay integration covers real shop clicks, reload persistence,
movement/home access, player damage, wave/boss victory, repeat difficulty and
progress retention after defeat. Its scripted offensive test uses invulnerability
and is not a human balance playthrough.

## Genuine remaining work

- Further bespoke building variation, finer stonework/cloth painting and more
  individually composed garden/forest areas. This is a substantial procedural art
  overhaul, not a claim of finished studio-quality hand-authored environments.
- Some foliage still uses alpha-textured planes arranged in 3D; inspect extreme
  camera angles and overlapping transparency on real hardware.
- Further optimisation and quality presets for low-end GPUs. Cloud software WebGL
  draw/triangle counts are recorded, not presented as a real-device FPS guarantee.
- Windows launcher execution and broader browser/GPU checks remain. The packaged
  server/game are tested in Linux Chromium; Node is still required on Windows.
- Water is stylised decorative geometry, not a swimming or fluid simulation system.
  Background mountains are layered illustrations; world-edge slopes are physical
  scenery backed by the existing movement bounds.

## Files and next-task entry points

`src/environment/` contains pigment, architecture, terrain, vegetation, rocks and
scenery modules. `src/art.js` keeps its old material API; final material hooks are
restored after static batching. The integration point is `installEnvironment()`
in `src/main.js`. Never batch a vertex-coloured cliff through a utility that drops
its colour attribute. `tools/environment/` contains focused checks and review capture.

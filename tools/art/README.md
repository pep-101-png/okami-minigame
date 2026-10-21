# Windflower painted-world art pass

This modifies the existing playable scene through its existing material/texture
GUIDs. No scene reconstruction, editor migration, runtime spawner, asset pack,
paid API, gameplay change, wolf change or Windows task is involved.

- Seven original 1024px surface sets: cedar/endgrain, natural stone seams,
  blue-green roof tiles, warm paths, meadow brush strokes and paper plaster.
  Colour, relief and packed metal/AO/smoothness maps share the same paintings.
- Original blossom/maple canopy cards retain their existing mesh/material bindings.
- Surface Detail adds continuous coordinate variation and broad pigment washes;
  Pigment adds stone/moss articulation and reduces double-dark albedo multiplication.
- Windflower's existing sky material now uses Painted Dawn Sky: indigo/apricot
  atmosphere, painted cloud ribbons, distant ridges and a restrained sun disc.
  Existing fog/ambient settings are tuned for cooler depth and warm village bounce.
- Two existing closed stone cap meshes now have shaped Kasuga hips, lifted corners,
  cornices and a finial. Original GUIDs, mounting height and bounds are retained.
- Surface normal imports are explicitly NormalMap/linear; packed masks are linear.
  Previously all 21 surface files used the default sRGB colour importer. The old
  editor migration could correct this locally, but its completed marker skipped it
  on subsequent machines; the asset metadata now contains the correct settings.

Regenerate artwork with Python 3, Pillow and NumPy already available in the authoring
environment (no external artwork downloads):

```sh
python tools/art/paint_windflower.py
python tools/art/paint_foliage.py
python tools/art/sculpt_lantern_caps.py
python tools/art/check_art.py
```

Preview images in `previews/` are texture sheets and a **Blender geometry render**,
not screenshots of the updated game. The original map/Art/SurfaceDetail metadata GUIDs
are preserved. 1024px textures replace existing files; no new texture sampling pass,
post-processing volume or world-population system was introduced. The two cap types
increase from 384/480 to 1,152 triangles per instance; this needs real frame-time
measurement, although it remains a small decorative mesh.

## Actual visual inspection and limitations

Inspected GitHub feedback run `20261021T092745607Z-9936e8`, source commit
`aefd595771e933a3313ecb4170251764c94ab1e3` before authoring. SHA-256:
`9b91788538a1af9b96e91c877f3770fc96b92b1cc1bceb5608b120dbc6a4da63`.
All 12 screenshots and sampled time sequences from all 14 MP4s were opened.
All 14 had their full expected frame counts and encoded successfully, but were
marked `frames_captured_coverage_incomplete`. Walk/jog/sprint (all three angles),
jump, stop/turn, dodge, combat and the gameplay route show little or no intended wolf
motion. This is **not** evidence of correct locomotion. Several still captures also
frame the whole world instead of their named subjects. These are pre-existing
capture limitations in the uploaded build, not an approval of movement quality.

The old village images show dark uniform ground, plain walls, striped roofs and pale
faceted scenery. These informed the materials/sky pass. Texture sheets were inspected
and corrected (notably natural stone instead of a masonry grid on boulders, and
removing an overlapping endgrain ring artefact). A cap geometry render was inspected.
Unity is unavailable in this cloud environment: the changed shaders and scene have
**not** been compiled/rendered in Unity, and no updated gameplay video was inspected.

After review/merge, existing PC Git syncing can retrieve the source and the existing
validator can publish fresh feedback. No runner installation/update or task activation
is required by this art pass. Review shader errors/magenta surfaces, roof scale,
foliage alpha/overdraw, lantern contacts, near/far contrast, wolf readability and frame
time before approving visuals. Lighting inevitably affects how the unchanged wolf is
illuminated. Building silhouettes, faceted cliff geometry and NPC shapes are retained;
this pass does not claim those structural limitations are solved.

# Ink-world shader changes

These are environment-only changes. The existing wolf shader, wolf model,
materials and animation assets are not changed by this shader work.

- `Pigment.shader`: warm ochre light planes with a softly broken painted light
  boundary; darker irregular grazing edges, sparse interior brush hatching and
  dark central/branching leaf ribs. The connected colour artwork, raw-linear RGB
  normal maps, terrain/path blend, shadow reception, fog, additional lights and
  existing vegetation wind remain supported. New material defaults:
  `_InkStrength=.62`, `_WashBands=.68`. Set either to zero to reduce the new
  contribution on a particular environment material.
- `InkContour.shader`: separate inverted-hull material for explicitly added shared
  mesh renderers. It deliberately does not depend on drawing two forward passes
  from a single renderer. Default sumi colour `.018,.014,.010`, stroke width
  `_InkPixels=2.7` at 1080 lines, `_InkWorldMax=.055` metres, pressure variation
  `_InkIrregularity=.32`. Thickness uses the inverse-transpose world normal and
  perspective/orthographic projection scale, so object scale does not scale the
  stroke. The final irregular width is capped at `.055` metres. Fog softens
  distant ink. One ordinary `UniversalForward` pass, `Cull Front`, depth write on,
  `Geometry-1` queue; no shadow-casting/depth-only pass.
- `BrushWater.shader`: slower directional calligraphic ribbons, a broken dark
  shoreline and quieter reflections/specular. The saved material's base colour
  now controls the river wash. Retains actual opaque-scene/depth sampling and
  placed-rock wakes. The rock loop is capped at its 16-element shader array.
  Squared signed river-bend inputs use multiplication instead of `pow` to avoid
  platform-dependent negative-base behaviour.
- `GardenPond.shader`: slower broader ripples, broken painted rings, a darker
  edge and quieter reflections. Existing depth-aware contact/refraction remains.
- `PaintedSky.shader`: three warm/green distant ink-wash ridge layers, broader
  cloud ribbons with broken dark undersides, faint fixed paper grain, and a red
  and gold seal-like sun with an ink rim. This background painting supplements
  actual scene geometry.

## Contour integration requirements

Add shell renderers only to selected **closed, solid environmental forms**.
Prefer a welded/averaged-normal copy of the mesh to avoid separated hard-normal
triangles. Share that shell mesh between repeated rocks/trunks/building elements.
Do not add colliders, scripts or navigation obstacles to shells; turn off shadow
casting/reception, motion vectors and light/reflection probes. Include maximum
extrusion in the shell mesh bounds; in object coordinates use `.055` metres
**divided by the smallest absolute world scale**. Do not apply shells to the
wolf, vegetation cards, water, the whole terrain, interior walls or home cutaway
parts. Inverted hulls can show solid black backfaces when viewed from inside.

## Checks and remaining verification

Run `python tools/ink-world/check_shaders.py` for delimiter, property-buffer,
explicit-pass, capped-extrusion, bounded-rock-loop and water dependency contracts.
The existing ValleyURP asset has both required depth and opaque textures enabled.
The changes use URP Core/Lighting APIs already used by the project and add no
renderer feature, package, runtime C# or PC task.

The static check passed in the cloud. **It is not a shader compiler or a rendered
visual test.** Unity 6000.6.6f1/URP17.6 compilation, Windows Direct3D11/12 output,
actual contour joins, occlusion, water ordering/refraction and performance still
require the existing Windows Unity feedback run. Inspect fresh gameplay-camera
screenshots and recordings at close range and from inside the home before calling
these changes visually verified. Blender asset previews cannot verify these URP
shaders.

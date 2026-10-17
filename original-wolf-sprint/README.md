# Amaterasu — Walk, Jog and Sprint

Open **Amaterasu-Movement.blend** in Blender 4.3 or newer and press **Space**.
**Sprint** is selected. Use the lower Action Editor's dropdown to select
**Idle**, **Walk**, **Jog** or **Sprint**. All original textures are packed.
See [OPEN-IN-BLENDER.txt](OPEN-IN-BLENDER.txt) for controls and export ranges.

## Preserved

The accepted `RUN_REFINED` Action is renamed **Jog**, with its curves, timing
and evaluated motion unchanged. `IDLE` and `WALK` are renamed **Idle** and
**Walk** without changing their motion. The older Run is kept as **Legacy_Run**.
The approved source `.blend` remains untouched on `amaterasu-run-refinement`.

Mesh, proportions, UVs, split normals, materials, packed textures, skin weights,
rest bones, constraints and controls are retained. No rig repairs or remodels
were required. The actual game and browser viewer are untouched.

## New Sprint

Sprint is authored separately, rather than copied and retimed from Jog:

- Longer forward foreleg reach and a high, extended hind-leg kickback.
- Shorter ground support and distinct gathered/extended flight phases.
- Coordinated pelvis tuck, lumbar flexion/extension, chest counter-motion,
  scapular motion, landing compression, stabilised gaze and neck follow-through.
- A trailing tail pose with a delayed wave through its existing five controls.
- Low hind recovery beneath the body to avoid the old overfolded-hip defect.
- Cyclic curve tangents, planted paw targets and toe/heel roll.

Sprint uses a 7.8-unit stride and 32-frame cycle at 60 fps, compared with Jog's
4.8-unit stride and 40-frame cycle. Its matching travel speed is 14.625 source
units/s; Jog remains 7.2. Body scale has not changed.

The earlier user-provided canine gallop GIF informed the support order,
extended/gathered poses and rear propulsion.

## Review

`review/preservation.json` verifies exact original appearance/rig fingerprints,
unchanged Action curves and 25 sampled poses of the retained Actions.
`review/contacts.json` checks fractional-frame contacts, virtual ground slip
and the loop boundary. Evaluated-frame diagnostics and rendered side/front/rear
sequences support the visual review. Deeply bent joints can retain some creasing
in the original skin; this is not a new skinning pass.

The project contains no game changes, extra gameplay systems or new animations
other than Sprint. The source model attribution/licence is in LICENSE-SOURCE.txt.

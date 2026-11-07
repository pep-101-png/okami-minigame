# Heavens, weapon surfaces, audio controls and vegetable soil

Implements the user's completed follow-up list. All visible paint, models,
motion and sound remain original Ōkami resources.

- ES4A/ES4B ribbons are exclusive to ES3A form three. Six roots sit along the
  dorsal torso, below the weapon attachment point; none attach to head or paws.
  Original seamless et03_002/003 wind loops run forward at 0.32 speed with stable
  length and softly following roots. Non-looping ping-pong entrance curves and
  whole-root sinusoidal bobbing are removed.
- Thunder Edge's normal lightning grows from 2 to 5.2 metres; charged main strike
  grows from 8 to 22 metres. The charged ground flash grows from 5.3 to 14 metres,
  with larger secondary bolts. Particle count per hit and damage remain unchanged.
- Removes solid effect sheets from the always-visible weapon assembly: WP29
  group 0 and WP25 group 2. Physical spikes, ring and fittings remain visible.
  Original vertex streams, UVs and texture files remain intact. This fixes the
  opaque white bands caused by drawing attack effects as weapon surfaces.
- Garden return gate uses only post/lintel collisions and a floor-relative
  passage matching the widened original spirit curtain. Walk-in detection covers
  the opening and approach, and calls the existing return-home path.
- Garden and NPC music-house music targets reduce from 0.10 to 0.035. Palace
  target reduces from 0.045 to 0.014, with overlapping original audio voices at
  the loop boundary rather than a hard stop/restart. These are source gain values.
- Pause → Sound provides original-ink sliders for master, music, and effects/
  voices, including controller left/right adjustment. PlayerPrefs persist them
  separately from game saves. Category gains recover from zero without compounding.
- Growing soil increases from 12.8 × 6.8 × 0.10 to 16.8 × 9 × 0.26 metres.
  Original earth paint has two detail scales and rounded, feathered edges with
  lighting following the actual relief. Mesh collision supports the bed. Crops
  are raised to its surface without changing identities, harvesting or regrowth.

## Audio identities deliberately awaiting listening choices

The user reported all recent numbered assignments mismatched their fan-made
Ōkami Rejuvenated Studio. Its okrmods.com site could not be reached through the
workspace's domain policy, including after network permission was granted. The
user asked to use another way instead of supplying more links. No guessed
replacement was assigned. Existing recordings, cue bindings and the approved
bark mix remain byte-identical.

The separately delivered listening pack previews the exact installed files and
labelled alternative original entries, plus isolated bark and lightning layers.
Its raw file/index/SHA manifest makes a subsequent choice reproducible by the
actual waveform rather than unconfirmed Studio numbering. Alternatives are NOT
claimed to be the intended sounds. The pack is outside Assets and outside the game.

## Validation

Actual game source compiled with explicit engine doubles, zero C# errors.
Tests cover gate return, third-form visibility, original loop seams, crop regrowth,
volume/persistence API calls, music crossfade, real combat hold/release and real
SaveStore I/O in a temporary profile. All Assets C# syntax and original asset
integrity checks pass. Weapon surfaces, ribbon motion and soil paint/relief were
inspected using offline native-asset OpenGL diagnostics.

No current Unity import, shader compilation, Play Mode physics/rendering or PC
listening test is claimed. The latest existing Unity feedback is from an older
commit, with all fourteen clip coverages incomplete; it cannot validate this patch.

# Full-power Shiranui, original weapon parts and selected audio

Implemented from the user's completed 6 November list. All models, textures,
motion curves and recordings come from original Ōkami files. Existing combat
recordings, approved bark mix and weapon portraits are preserved.

- Quiet palace loop: CORE #16.
- Menu and save-menu opening: CORE #35.
- Ammy swing voice: PL00 #14, #15, #16 on a separate channel over existing weapon audio.
- Pond sitting: PL00 #27.
- Festival Spirit Run: BGM00 #27, with its own fade and cleanup.
- Full-power reveal: EVBC #5, starting with the longer cutscene.
- P cycles Ammy → PL0D awakened Shiranui → ES3A full power → Ammy. The third form
  is 1.2 times the second form's visual scale and uses a 2.2 combat multiplier,
  ten percent above the second form's 2.0 damage/speed/attack-rate multiplier.
- Third-form cutscene runs 6.4 seconds with a wider camera orbit, stronger original
  spirit/electricity bursts and lighting. Skip/cancel restores input and time.
- Twelve original ES4A/ES4B tendril skins follow live body bones. Their recovered
  original ES4A motion runs on unscaled time through smooth ping-pong sampling,
  including idle/cinematics. ES4B's exact mesh and bind data match ES4A's.
- Awakened Thunder Edge replaces the base entry in ownership, the catalogue and
  home selection; older saves migrate without losing other weapons. Re-buying
  the replaced base is blocked. Other weapon evolutions remain future work.
- All original Thunder Edge spike sections, including the chest-reveal asset,
  are enabled. Divine Retribution's original green disc and Tsumugari's original
  omitted pieces are restored. Full-power charge clearance accounts for scale.
- Q cannot cycle weapons in a trial, with a living enemy, during an attack/charge,
  while locked/swimming or behind menus/cinematics. It works outside combat.
- Home weapon text uses original scroll paint, larger high-contrast native ink
  glyphs and measured text sizing instead of text directly over the scene.

## Validation and limits

Actual source compiled against explicit engine doubles with zero C# errors.
New form/cutscene/skip/tendril/audio/evolution tests passed; actual WolfCombat
hold/release/explosion/Q/stat checks passed at 15/30/60/120fps. Actual SaveStore
file/slot/backup/corruption tests passed in an isolated temporary directory.
All Assets C# parsed successfully. Original asset/metadata/preservation checks
passed. Native weapon assemblies and ES3A were inspected in offline GL renders.

These are not Unity import, shader compilation, physics or Play Mode checks.
Latest available PC feedback belongs to an older source and does not validate
this patch. No claim is made that the user's current game was play-tested.

The user's audio list numbering could not be established by their audition.
This patch assumes standard one-based player subsong numbering, preferring AFS2
when that subsong exists, otherwise the original SES embedded ADX order. The
exact source/index/hash/decode record is in audio-provenance.json. Their intended
sound identities remain unconfirmed; no substitute recordings or invented audio
have been introduced.

The thirty-second MP4 is delivered separately and is never installed into Assets.
It is a standalone native-asset cinematic at 1080p60, not Unity gameplay footage.

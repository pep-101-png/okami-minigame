# Eighth Wonder completeness repair

Inspection of the actual WP28 archive found that the runtime visibility mask kept
only groups 1 and 2. Restore groups 3 and 4: original metal side faces and ink
outline belonging to the moving hilt. Keep group 0 hidden in the normal appearance;
it is the separate half-alpha white blade overlay, which washes out the painted
blade if blindly enabled. All original geometry, UVs, weights, colours and texture
pixels are retained. The atlas pixels match the decoded ken400/ken402 DDS entries
exactly, and repeat wrapping already matches the out-of-unit native UVs.

The held weapon selected WP28_001, a static carrier after controller translation
removal. Select the genuine WP28_000 pose/8-second wheel curve for this instrument.
The moving hilt uses native bone 1 (runtime bone 2), including its correct 0.285m
bind-relative position. Displayed and falling blades sample only that bone, so
restoring the wheel does not tip or translate the whole falling sword. Bounds
include the rotating side faces. Held charge uses the existing live mesh/head
clearance treatment. Original authored wheel pauses remain intact.

WP28's six embedded PL00_520..525 attack files have the same source SHA-256 values
as the existing glaive attack source; keep those recovered primary attack clips.
WP28_002..00f contain static weapon poses and are not substituted as fabricated
attack animations. The original pose bank and painted PNG bytes are unchanged.
Normal and awakened variants share this native model/animation repair. Existing
portraits, damage/ranks, falling-sword gameplay, portal repair and tendrils remain.

Verification compares each model part/UV/paint to the decoded archive, checks the
six original attack payload identities, and executes actual equipped/displayed
wheel sampling and attack continuity against engine doubles at multiple frame
rates. Original-data offline GL reviews compare sections/carriers and inspect a
moving idle/attack sequence. No current Unity import, rendering, charge collision
or Play Mode verification is claimed. Latest published Unity feedback still targets
the old October 21 source with incomplete coverage. The download contains Assets
only; no previews or tooling are installed in the game.

# Celestial guardians and earned Shiranui forms

Adds Sunward's own two-guardian quest using only recovered original models, paintings and source MOT poses. It is an adapted encounter, not a recreation of an original Ōkami boss script or canonical story episode.

- Crimson Helm's final defeat unlocks the river passage. Its howl victory is preserved, followed by a skippable river-light reveal. Existing Crimson victories count; saves are not reset.
- The garden keeper, village conversations, elder's tea stories and Hana give short, changing hints. Examining a quiet gate gives exact requirements; ordinary NPC dialogue avoids a checklist.
- Level 20 and every base rank in all eight blessing paths open the courtyard gate past the palace's eastern eaves. The Veiled Sentinel unlocks second form and permanently removes Shiranui's seal.
- Second form plus level 30 exposes five additional purchasable ranks in every blessing path. All forty further ranks are required for the Eclipse Warden, reached through the passage inside the chamber. Victory unlocks third form.
- T/right-stick press cycles earned forms. P remains the unrestricted testing shortcut. Saved unlocks persist, including ranks beyond the old caps.
- Each guardian has native source attack poses, telegraphed charge/slam/fan attacks, projectile contact, recovery openings and a brush counter. Stagger cannot permanently lock the bosses. Defeat returns to the appropriate gate for retry; victories award each form only once. Intro, release and transformation sequences can be skipped.
- Separate cloud courtyards use original stone/meadow/cloud paint, native gates, flowers and lanterns. The garden warms and gains blossom effects after release. Battle music is separate from the quiet palace and NPC flute tracks. The existing ultimate now frames the active arena instead of the village centre.

## Original assets

`recover.py` checks the inspected source hashes and converts original MD/DDP/MOT streams at 60 samples/second. `asset-provenance.json` records source identities. The sentinel uses EM16's EM60 sword wolf; the fox uses EM61's body and original ninth tail alongside EM62's eight-tail companion. Inspected group masks exclude shadow/alternate body meshes, retaining the complete visible forms. The palace sleeping bank gains the compatible original standing-idle record so freeing the wolf cannot select a missing clip. No original motion curves, weights, paint or UVs are replaced with invented artwork.

## Validation and limits

`runtime.py` exercises actual progression, guardian, original actor, native player transformation and GameFlow celestial methods using Unity API doubles, with a scripted target and flat collision floor. The current fixture completes 89 assertions and checks both complete attack cycles, actual ranged/contact calls, brush guard breaks, victory/defeat/retry, earned skin reveal, serialized unlock/rank validation, swept gate crossing, and river reveal skip/cancel. `full_compile.py` additionally checks the actual GameFlow integration. `verify_assets.py` checks skeletons, finite/unit pose data, geometry/weights, original texture bindings and metadata.

`review.py` renders actual captured guardian poses and recorded prop transforms, at normal speed, using original models and paint. Inspected source pose sequences, native group sheets and new rendered arena frames. The preview's original battle track is added at review gain; it does not simulate Unity particle systems, player physics or attack sound playback. This is not Unity Play Mode or verification on the user's PC. No Windows capture task was dispatched.

Latest retrieved published Unity feedback is still `aefd595771e933a3313ecb4170251764c94ab1e3` from October 21. Editor validation passed without logged errors; all fourteen clips have incomplete coverage. Those older clips do not validate this new quest.

The engine doubles are isolated under tools and never shipped in Assets. `package.py` produces the cumulative Assets-only ZIP from baseline `1ad16ca739d2a1f2ac3be3faabdedd9e8e00912d`; its separate MP4 remains outside the game.

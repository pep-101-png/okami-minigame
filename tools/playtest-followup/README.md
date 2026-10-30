# Windflower audio, entrances and native activity follow-up — 31 October 2026

This candidate modifies the existing Windflower game following the second playtest list. It builds on the exact downloaded source `262519a7ac762e4e1f5af7f472139cedf87f8bd9`. Rollback branch: `backup/before-second-playtest-20261031`.

## Short issue report

| Issue | Source change | Verification limit |
|---|---|---|
| 1 Animals audible everywhere | Player-position listener, positional actor sources, strict distance cutoff/falloff, four-source pool, global animal cooldown, quieter rooster within six metres, less frequent calls. | Audible PC balance remains unverified. |
| 2 Harsh/loud walk and jump | Correct ADX frame-scale decryption before transcoding; reduce-only levels, DC removal/edge fades, gentler runtime gains and rate limits. | No claim of listening approval. |
| 3 Distorted NPC speech | Same actual codec correction; positional voices, capped gain and a shared cooldown longer than the selected voice sample, preventing speech overlap. | Exact original dialogue cue meanings/timing are not reconstructed. |
| 4 Overall audio | Rebuilt all 42 cues, 39 encrypted streams corrected, existing source hashes retained; music/ambient waves rechecked too. World actors cannot fall through the 2D cue method. | Waveform, clipping and source integrity checks are offline. |
| 5 Dojo entrance/exit | Rotate native exterior toward the village, add a visible original paper door, correct landing points and snap camera focus on entry/exit; E exit remains reachable throughout the room. | Real controller/camera traversal needs Unity playtesting. |
| 6 Food-house entrance/exit | Simple original house exterior with a clear west entrance toward the village path and matching split collision wall and matching entry/exit points. The previous east opening and stranded prompt are replaced; the entrance avoids the enlarged house to the north. | Same runtime limitation. |
| 7 Frozen identical women/music | Three visually different diner models and a separate female performer; scheduled native seated/hand curves replace held transition poses. Original music plays in the venue. | Dedicated authentic koto finger-playing animation has NOT been identified. The current performance is adapted original hand motion at the native instrument, not a reconstructed native playing action. |
| 8 Enemy animation | Stable locomotion thresholds, preserved gait phase when switching walk/run, speed-dependent native playback, stun pauses and attack duration snapshots that do not change halfway through phase two. Existing combat timing/damage remain unchanged. | Must be judged in actual combat; no complete gameplay approval claimed. |
| 9 Swimming | Keep the extracted 01d/01e bindings, lower the torso to the waterline, slow the stroke clock/movement and emit original water wake artwork. | Native action names are not documented: these clips have not been newly proven to be the game's dedicated swim actions. Their earlier assignment was provisional. Do not claim that a different confirmed swim clip was installed. |
| 10 Blossom trees | Use the original VTB1 blossom canopy and tree bark only. Remove house divisions and post triangles. Blossom-card material supports viewing both sides. | Updated saved-scene Blender preview provided; Unity appearance unverified. |
| 11 Shiranui power | Remove the belly cloud/fire emitters. Original starglow/circleLight sprites emit from the animated body surface, with small warm light motes. | Unity emission adaptation, not complete original EST/SEQ playback. |
| 12 Dummy practice | Three native partners face nearby dummies, alternate original activity/rest clips and produce quiet, local contact feedback. The sword trainee uses native HM08_088; guard HM2d_080; third partner HM44_080. Practice grants no currency/progression and does not spam notifications. | Activity meanings/placement are Sunward adaptations; verify contact alignment in Unity. |

## Important audio correction

Many original clips have ADX revision `0x0408`: their per-frame ADPCM scale words are encrypted. Passing them directly to FFmpeg produced severely clipped, distorted output. The fix decrypts those scale words using the publicly documented Ōkami type-8 parameters before normal ADX decoding. Original uploaded/archive bytes stay untouched.

Reference algorithm/parameters: [vgmstream ADX keys](https://github.com/vgmstream/vgmstream/blob/master/src/meta/adx_keys.h) and [decoder](https://github.com/vgmstream/vgmstream/blob/master/src/coding/adx_decoder.c). No public reference code is used as sound content. All sound content remains the supplied original recordings.

`audio-audit.json` records all 42 source/output hashes, encryption handling, decoded/output RMS, peak, sample duration and attenuation. Derivative PCM peak is bounded at 0.45; no derivative samples are clipped. This does not establish that the selected cue is semantically the right call or that the final Unity mix is audibly approved.

## Native motion and artwork provenance

`motion-provenance.json` records original seated/hand MOT hashes and retargeting to the first twenty human joints, whose parent hierarchies match. Target-only costume/prop joints retain their own native binds. No skeletal poses are hand-authored. The native blade demonstration is from HM08; its native body and wooden blade groups are kept, while the alternate gold blade is hidden.

`extra-assets.json`, `effect-provenance.json` and `scene-changes.json` identify the added human resource, native body glow sprites and exact saved-scene changes. The two blossom trees preserve source triangles, UVs and paint; building parts are excluded and a dedicated two-sided material fixes the canopy's back-facing cards.

## Preservation and evidence

The same Windflower scene/build identity, village terrain/bounds, working controller, saves/progression, NPC interactions and arena mechanics are retained. Five previous pub wall boxes are retired and five corrected wall boxes installed; other existing colliders remain byte-identical to the downloaded candidate. The selected native actor bank gains the seated activity adapters and inspected sword motion resources.

`verification.json` contains focused offline scene/audio/motion checks. The broader previous verification is also rerun; C# parser success is NOT Unity compilation. Labelled Blender previews show saved geometry/poses with approximate materials. They do not show actual Unity playback, audio, swimming or the runtime Shiranui particle effect.

Latest published PC feedback still belongs to the older October 21 source, with all fourteen clips marked as incomplete action coverage. It cannot validate this revision. This environment has no Unity editor or PC-control capability. No Windows task or paid API workflow was started.

## Installation

Close Unity and back up the working project. Merge the update's Assets (and any other included project folders) into the EXISTING Sunward project, replacing matching files while keeping all other project content. Do not delete or replace the whole Assets directory. Open the existing Windflower scene. E enters/exits venues, Q changes owned weapons, P toggles Shiranui. The complete remaster is not declared finished while the runtime and native-action limitations above remain.

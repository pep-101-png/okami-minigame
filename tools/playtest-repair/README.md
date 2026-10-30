# Windflower playtest repair candidate — 30 October 2026

Latest follow-up: [31 October audio/entrance/activity repairs](../playtest-followup/README.md). The report below describes the previous candidate; the follow-up corrects its encrypted-audio decoding and other playtest issues.

This modifies the existing playable Windflower scene, not a separate demo. Source candidate only: Unity compilation, playback, purchase tests and audible cue approval have NOT been verified for this revision. Blender images are diagnostics, not game screenshots. Do not describe this candidate as a completed remaster.

Rollback source: `72336e1aa558d1344c1b52b93bac882b3dd31eb4`. Working branch: `repair/playtest-issues-20261030`. Integration baseline: `00fd8695363df01de80b012d68feb20c9961e8a9`.

## User checklist

| Request | Actual implementation and remaining limits |
|---|---|
| 1 Readable UI | Original scroll-paper crop, dark ink, explicit button states and responsive text sizing. Existing OS font remains; original font rendering is unported. |
| 2 Sound | 42 source-hash-traced original recordings: player, footsteps, weapons, impacts, NPC voices, six enemy voices, three farm animals, music, wind and river. Musical track names, cue timing and perceived balance need audible gameplay review. |
| 3 Building scale | Twelve ordinary houses enlarged 1.75 times; dojo and food house use larger native exteriors. Four houses/colliders/navigation boxes moved to clear interiors. Door clearance still needs gameplay review. |
| 4 Home cutaway | Interior renderer list is hidden outside the tighter home bounds; exterior hidden inside. |
| 5 Dojo | Native temple exterior, original dojo floor/walls/water/sign, native guards/master/Benkei poses and three training dummies. E entry, usable weapons, hit feedback without currency farming. |
| 6 Food house | Original exterior, floor/tatami, seating, tea props, Kushi at original koto and native music. Dedicated instrument-playing finger animation is NOT reconstructed; seated native motion is held. Ammy has an E sitting mat. |
| 7 Watermill | Select one native model form. |
| 8 Enemy duplication | Per-model body masks suppress alternate bodies/states while preserving weapons. |
| 9 Arena | Giant floor decoration removed; native wind artwork emitted along arena edge. Full original effect sequencing remains unported. |
| 10 Blue jump ring | Removed from jump/double jump. |
| 11 Movement effects | Original leaf artwork emitted behind sprint and on jump, using Unity emission adapters. |
| 12 Boundary rocks | Original groups lowered against terrain footprint. Requires final game-camera review. |
| 13 Pond | Two native flowering trees plus original blossom and steam sprites. |
| 14 Merchants | Umbrella group hidden and body calibration corrected to visible group bounds. |
| 15 Shops | Larger native stalls; separate weapon and upgrade menus. |
| 16 Weapons | All fifteen divine instruments have models/textures and their own native motion bank; purchase/equip and Q cycle owned weapons. Existing spear/sundial IDs and mechanics retained. Rosary attacks bind extracted player motions. In-memory purchase/save tests are prepared in the Unity editor validator but have not run here. |
| 17 P Shiranui | Original PL0d appearance toggles on P with compatible native skeleton/motions and original cloud/fire sprite artwork. Complete native Shiranui EST/SEQ dispatch and exact event timing are NOT ported. |
| 18 Swimming | River swimming controller state with extracted paddle motions, surface movement, jump-out and shore recovery. Needs real gameplay testing. |
| 19 Farm | Original stable, farmer, pens, animals, native dry-grass feed and water basins; selected cow/pig/rooster audio. A dedicated hay bale and long trough are not confirmed integrated assets. |
| 20 Original-only media | Selected models, paint, motion samples, effect sprites and sound recordings originate in supplied native files. Layout/colliders/emission/controllers are Sunward adaptations. OS font and full native effect sequencing prevent a claim of complete original-only presentation. |

## Actual modified scenes and prefabs

The existing `Windflower.unity` scene retains its scene identity/build entry. Changed generated prefabs: Enemy-boss, Enemy-elite, Enemy-heavy, Enemy-ranged, Enemy-reed, Enemy-wisp, NPC-1, NPC-2 and NPC-6. Additional native actors and venues are placed directly in that same scene. The separate demonstration scene is not the target.

Integrated source families: PL00 motion bindings and PL0d appearance; WP20–WP2e instruments; HM human bodies/poses; EM enemy bodies; VT buildings, stalls, cherry trees, musical instrument, farm props and watermill; ST1 r10c dojo surfaces/fences; ID scroll paper; core leaf/blossom/steam/wind/cloud/fire sprites; SES/AFS2/ADX recordings. Exact resource paths, groups, hashes and adaptations are recorded in adjacent manifests.

Solar Flare uses WP24 model, texture and native weapon motion resources with original fire artwork. Complete original EST/SEQ effect timing is still unfinished. This is not a claim of a fully reproduced native weapon effect system.

## Verification and preservation

`verification.json` records 155 model resources, 39 finite pose banks, 22 saved actor bindings, 15 weapons, 60 player motion bindings, 42 non-generated sound bindings and 93 C# syntax files without parser errors. The paper/ink fifth-percentile contrast is 10.5:1. This is source validation, not Unity compilation.

313 existing collider blocks remain byte-identical; two solid building boxes are retired for enterable rooms and 33 static collider blocks are added. Terrain/bounds, save-store source, NPC navigation source, build-scene list and package manifest are preserved. Four building navigation boxes and their matching physical positions move to make room for the requested venues. Existing save format and original two weapon IDs are retained.

Latest available published PC feedback belongs to an older source revision and cannot verify this candidate. No new gameplay recording, Unity compile or sound audition is claimed.

## Applying the eventual update

Close Unity and back up the working project. Merge the supplied update's Assets and any other included project folders into the existing project, replacing matching files while retaining everything else. Do not delete or replace the entire Assets directory. Open the existing Windflower scene and play normally. E enters venues/uses mat, Q cycles owned weapons, P toggles the Shiranui appearance. This report does not itself constitute a downloadable update.

# Windflower dungeon and dojo update — 31 October 2026

Focused incremental update against source `9646fda1fd46017f6627c8f815cdb32382b2d73e` (the preceding Combat/Lower Arena download). Rollback: `backup/before-dungeon-dojo-20261031`. No separate scene. No bosses added.

## Actual changes

- `Assets/Sunward/Scenes/Windflower.unity`: retire the entire previous lower chamber (tatami, repeated boulders, crystals and oversized overhead rocks). Install the original ST1/r10d boss-stage floor, shrine and four matching cavern-wall layers as a coherent layout, uniformly scaled 1.1. Native architecture spans about 193 × 176 m; the central playable area remains radius 31 m. Highest architecture is 28.24 m BELOW village grade. Preserve the existing upper arena, six breakable terrain fragments, win unlock and return-home mirror.
- The actual 68-edge cut in the existing terrain now extends into a 34 m deep, open-ended, six-section shaft. The upper bevel exposes soil and the widening lower section exposes original cliff paint. It is real geometry with inward-facing surfaces and mesh collision, rather than an alpha/texture hole. Shaft rim matches the existing terrain boundary. The shaft opens into the cavern overhead; the dais is at about -110 m. Closed original cover geometry remains unchanged.
- `LowerArena.cs`: use native floor collider heights, preserve progression and mirror mechanics, replace blue spirit lights with warm red/amber lighting, original Flame sprites and tinted original Steam artwork. This adapts original media to Sunward emission; it does not reproduce the entire native EST/SEQ event system.
- `OriginalDepthsPaint.shader`: darker local ambient contribution and distance haze; scoped to lower-arena materials. Existing village materials are unchanged.
- Three dojo pairs repositioned onto the actual native room floor, away from entry ramp; facing still follows each dummy. Remove overlapping full-body variants of the red soldier. Replace the third old man with native HM2e. Use isolated dojo-only resources so village NPC model selections and banks remain unchanged.
- `NativePracticeAnchor.cs`: after native skinning, sample original foot vertices from baked skin and correct support/root drift. Foot selection comes from leg bone weights (14/17); sword/bow bounds no longer lift the body. This also follows actual animation blending rather than a static bounding box.
- `NativeVenueActor.cs`: add a per-actor contact switch. These draw/aim drills do not trigger fabricated dummy-hit sounds at a generic clip percentage.

No prefab assets, combat stats, weapon mechanics, audio files/balance, home furniture, markets, save schema, build-scene list or upper trial rules changed in this patch. Previous known issues outside this focused request remain as before.

## Original media actually used

ST1/r10d SCR layers: `RM__LY80__Boss_Room` parts 1–6 (floating debris part 0 omitted), `__LY82__Boss_Saidan`, `M__LY83__Boss_kabeA`, `M__LY84__Boss_kabeB`, `M__LY85__Boss_kabeC`, `M__LY86__Boss_kabeD`, `SO__LY8f__Sort_Boss`. Native relative placement, original UVs/vertex paint/DDS artwork preserved. See `source-conversions.json` for source SHA-256s and Unity GUIDs. Engraved seal is offset 2.5 cm to avoid overlapping source floor surfaces.

Shaft uses byte-identical original Kamiki earth and recovered cliff PNGs, with separate repeat-wrap importers. Shaft geometry is newly authored as requested; textures are original. No new painted artwork or sounds.

Dojo rigs: HM08/Susano (body group 2 + sword group 0), HM2d red archer (one body group 0 + equipment 2/3), HM2e soldier (one body group 0 + equipment 2). Own original MOT clips: idle plus `hm08_088` (wooden-sword draw/raised stance), `hm2d_080` (bow aim/draw), `hm2e_080` (sword draw/stance). These are original practice gestures, **not a newly verified continuous dummy-striking sequence**. No procedural replacement skeletal animation. Dedicated strike/contact choreography remains unverified and no actual arrows are spawned for the aiming drill. See `training-sources.json` for exact bindings, masks and foot vertex indices. Inspection-only HM08 clips are not installed in village resources.

## Verification and limits

`verification.json`: all new scene GUIDs resolve; one lower-arena controller; first component is Transform on every authored object; native architecture bounds safely below grade; 298 support samples across the playable radius and mirror; six shaft sections with inward normals; 920 idle/practice frames inspected for finite skinning and zero support-foot penetration after correction; syntax parse of 96 C# files. Reviewed three labelled Blender geometry/paint previews (these use flat source paint, not Unity shaders/particles). Native source and DDS hashes asserted during conversion. ZIP manifest verifies committed bytes, no LFS pointers, archive CRC.

**Unity compilation, actual walking/falling/mirror interaction, runtime trainee appearance, light/particle appearance and performance are UNVERIFIED. No Unity editor/compiler or user's PC access exists in this environment.** Syntax parsing is not compilation. Latest available remote Unity feedback is from 21 October and a different source commit, so it does not validate this update. Source PR remains draft pending gameplay verification; this report does not call the overhaul fully completed.

## Install and inspect

Close Unity and back up the working project. Merge the ZIP's **Assets** into the same existing project and replace matching files. Keep all other files; do not delete/replace the whole Assets directory. This small patch requires the preceding Combat/Lower Arena update. Open existing Windflower; win upper trial and choose Explore, jump through the centre, E at the mirror to return home. Existing saves with a prior win already unlock it. Starting another upper trial restores its cover.

Check rim thickness from above; fall down the open shaft; inspect engraved dais, cavern/shrine and red atmosphere; confirm no lower geometry appears in the village; inspect three dojo bodies/feet through complete cycles and enter/exit normally. No bosses should appear downstairs.

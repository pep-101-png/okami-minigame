# Reachable heavenly garden landscape

Baseline: Desktop working lineage `2a553e95b310f67cd626a2ab643eb399d42f1c02`.
This updates the existing river-accessed Sunward garden, not a demonstration scene.

- Lower garden, middle terrace and upper keeper sanctuary, connected by two recovered curved stone ascents from `r102/jimen00_ly04`, division 0 of part 0.
- Three enclosing banks use original `r101/___LY17__x1_kumo3` geometry/paint and its real vertex-alpha edge fade. Banks clear the guarded walking ellipse.
- Original closed VT0a retaining geometry has projected original stair masonry on its sides and original meadow paint on its top. Separate floating meadow sheets were removed: visible floor and collision now use the same original retaining mesh.
- Dense planted beds sit directly on actual ground. Trial stage fragments and planting mounds were removed after side-view inspection; the final layout uses supported terrain without separate floating sheets.
- Twenty original painted trees, 479 native flower placements, three complete original ponds, original lanterns, gongs, paper offerings, shrine, petals and shafts. Visitors moved clear of ponds.
- Existing keeper dialogue closure, world visibility isolation, return interaction, boar pen, approved bark blend and approved catalogue artwork retained.

Verification: selected-script .NET semantic build passes with engine doubles, zero errors; 1,340 behavior/layout assertions. Actual exported triangle audit checks perimeter support, both curved stair routes, landings and cloud clearance. Existing farm, doorway and art/audio regression audits pass. All 131 C# files parse. New resource metadata/GUIDs audited.

Four `offline-view-*.jpg` files are Blender diagnostics of the current placement JSON/native geometry, including arrival/player height, overview, side and keeper approach. They are NOT Unity screenshots or gameplay proof. The offline material approximation includes source paint, cloud fades, face culling and vertex colour; URP rendering, collisions, audio, motion and frame rate require a Unity play-test. No Unity executable is available here. Latest published Unity feedback is from a different October 21 source and cannot validate this update.

The delivery ZIP is cumulative from the approved bark source `1ad16ca739d2a1f2ac3be3faabdedd9e8e00912d`, includes Assets only, and also retains the prior heaven/keeper/boar repairs. Stop Play mode, merge Assets into the existing Desktop project, then restart Play so the runtime garden rebuilds.

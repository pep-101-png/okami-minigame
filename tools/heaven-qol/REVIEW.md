# Heaven grounding, garden and maze repair

Working baseline: `dd551cdee99b2e2306db73a30fdd540c0483f47c`, the Desktop game's previously delivered heaven update. The change targets its existing river-accessed garden.

The previous open stair strips and stretched prop tiers could look supported in the overview while exposing thin edges, intersecting faces and unsupported sections from player height. They are no longer instantiated. A single original r108 meadow mesh now supplies visible terrain and the collision mesh. Its original 98 vertices, indices and UVs are retained; existing vertices are reshaped in Y into gently graded garden levels. This is adapted original terrain, not a claim that the untouched original stage had this layout.

Original stone artwork is blended directly into that same terrain in the shader using 32 layout segments. There are no independent road meshes, raised overlays, new painted road artwork or texture planes. Original meadow painting supplies the jade ground. Original cloud artwork/geometry supplies five softly faded surrounding banks; original steam paint adds a lower veil. Light shafts are narrower and less intense.

The new five-by-five bamboo/hydrangea garden maze has 34 visible planted boundaries, corresponding colliders, two open east gates and a 28m gate-to-gate solution. Its 25 cells are reachable, including dead ends. Maze collision is checked using its actual axis-aligned box extents plus a .35m wolf radius. The original flower garden has a circular walk and 653 flower placements; the maze has another 102 hydrangea clumps, with 102 native bamboo clumps. There are 25 native trees and three complete native pond models. Wide ponds sample their supporting footprint so downhill rims sink into the terrain rather than hover. The shrine's support variation is below two centimetres across the sampled footprint.

The two strolling visitors remain clear of the maze/ponds. Their path rate now exceeds OriginalActor's real walk activation threshold; the former slow ellipse could settle below it and slide while idling. Original recovered idle/walk clips remain unchanged. Keeper dialogue closure, world isolation, home return, the approved bark and catalogue artwork remain intact.

Validation: selected-script .NET semantic compilation succeeds with explicit engine doubles and zero errors; 1,340 existing behavior/layout assertions pass. The new native topology/floor/slope/route/maze/pond/protected-asset audit passes 4,237 checks. Current art/farm/door regression audits and all 131 C# syntax parses pass. New resource metadata/GUIDs are checked.

Five `offline-view-*.jpg` files cover arrival/player height, overview, maze, keeper and flower garden using the final runtime layout and original geometry/art. They are Blender diagnostics, NOT Unity screenshots or gameplay verification. Steam particles, runtime motion, URP rendering, collisions, sound and frame rate still require Unity play-testing. No Unity executable is available here. Latest published Unity feedback is from an unrelated October 21 source; it cannot validate this update.

Delivery remains an Assets-only cumulative ZIP. It contains no tools, report or readme folders. Stop Play, merge Assets into the existing Desktop working project, wait for import/compilation, then restart Play to rebuild the runtime garden.

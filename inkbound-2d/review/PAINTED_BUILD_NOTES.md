# Painted revision — 14 October 2026

Scope: only `inkbound-2d/` on `inkbound-painted-wolf`. Previous 2D and 3D branches remain intact. All 75 original tracked 3D files match the preservation manifest.

The wolf now uses 32 AI-assisted painted poses based on the supplied reference. The character's illustrated anatomy, curled fur ornaments, vermilion markings, ivory pigment, turquoise disc and orange flames replace the previous normal vector drawing. Enemy art has 32 poses including walk cycles, attack tells, attacks and hurt. The level uses a painted background and 16 painted props rather than its old main foliage/building silhouettes.

Sprite extraction follows opaque connected silhouettes across nominal sheet boundaries. This preserves full flames, paws and antlers without bleeding adjacent actors into a frame. The wolf studio loads only the two wolf atlases and renders the same wolf artwork used in-game, with selectable movement/combat/reaction poses.

Simulation now advances at fixed 60 Hz with one HUD update per rendered frame, preserving combat/movement timing across variable frame rates. The lightweight viewer resizes its canvas only on window resize. Input tests wait for gameplay state transitions where a browser event is processed on the next simulation tick.

Validation: production build, all 18 browser checks, real-input full-route victory, and isolated viewer playback. Reports distinguish fixtures, virtual gamepad checks and real-input traversal. Physical controller and Windows CMD execution are not verified on this Linux machine. The compiled launcher is checked after extracting the ZIP with no node_modules.

The new compiled launcher defaults to port 5190 to coexist with older builds on 5173/5180. The ZIP keeps source art only once in public/art; its dependency-free server serves these local files beside the compiled JavaScript. The downloadable folder includes START-2D-GAME.cmd and START-WOLF-STUDIO.cmd.

Visual quality still needs the user's review. Generated poses and timed playback are not a claim of commercial animation polish or traditional artist authorship.

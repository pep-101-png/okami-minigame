# Required Unity gates — none marked passed without a current-build result

Record the exact Git commit, Unity version, renderer/backend, result, log and screenshots/video for each gate. Older feedback from a different commit is not a pass. Existing automation may publish feedback normally; this stage does not start, enable or modify installed Windows tasks.

| Gate | Acceptance | Current status |
| --- | --- | --- |
| Import/compile | Unity 6000.6.6f1 opens the actual project; no C# errors, missing script or importer errors | Not run |
| Shaders | All eight review shaders compile for the actual platform, including cutout shadows, water, ink and transparent passes | Not run |
| Asset validation | Run Sunward/Remaster/Validate Village Assets; inspect JSON and actual scene, not JSON alone | Not run |
| Review navigation | Overview/on-foot controls, mouse capture/release, null input devices, doors, all stairs, room collisions, bridge, river banks | Not run |
| Review presentation | Compare source village artwork/UVs, ink hull coverage, alpha/cutouts, foliage sway, petals, water flow, splashes and steam | Not run |
| Opaque optimization | Compare filter on/off captures; no missing faces, alpha changes or collision differences; profile actual draw cost and startup allocations | Not run |
| Animals | 13 actors/nine types; grounded idle/walk loops, sensible paths, doors/props not trapping animals, pet interaction and soft chime | Not run |
| Native models | Default Ammy/38 bones and Solar Flare/16 bones; material flags, original texture slots, native scale, axis/winding, ink, bind pose | Not run |
| Live movement | Walk/jog/sprint, stop/turn, slope/steps, jump/double jump, fall/land, all dodge directions; no neck/leg/tail breaks or sliding | Not run; live assets unchanged |
| Combat | Both weapons; light chains, heavy, charge/release, air strike, switching, damage/hit windows/line of sight/stagger | Not run; live systems unchanged |
| Native animation conversion | Verified original interpolation/Euler order/FPS; confirmed action map, root-motion policy, pose/foot/transition comparison | Not implemented |
| Native Solar Flare | Verified original activation/flame/trail/impact sequencing and attachment; old custom effects disabled together only after approval | Not implemented; Sundial retained |
| NPCs/quests | All seven named NPCs plus shoppers; dialogue, role interactions, flower quest, shop, routes and doorway clearance | Not run; all baseline bytes preserved |
| Arena | Entry bell, enemy spawning, all four waves, elites, Kurogane, completion/rewards and return | Not run; all baseline bytes preserved |
| Progression | Collectibles, permanent upgrades, economy, equipment and unlocks remain stable | Not run; baseline preserved |
| Save/load | Existing save opens; temporary verified writes and backup recovery work; home/mirror/rest/UI unchanged | Not run; format/code preserved |
| Audio/UI/camera | Existing sounds/menus, prompts, home cutaway, equipment UI and camera; no duplicate audio listener when changing scenes | Not run |
| Performance/build | Startup memory/time, actual triangles/batches, CPU/GPU frame time, GC, Resources build-size increase and Windows build | Not run |
| Final review | All live-world replacements rendered and all regression gates passed on the exact final build | Not reached |

# Amaterasu — Natural movement and turning

Open **Amaterasu-Movement.blend** in Blender 4.3 or newer and press **Space**.
The default scene plays a 51-second, native NLA demonstration: look-around idle,
stepping standing pivots, Walk/Jog/Sprint, both turn directions, acceleration,
deceleration and speed-dependent wind. No add-ons or script trust are needed.

For individual Actions, choose scene **01 · Action inspection**, select
**WOLF_RIG**, and use the lower Action Editor dropdown. Full instructions are in
[OPEN-IN-BLENDER.txt](OPEN-IN-BLENDER.txt) and the project's embedded text
**MOVEMENT — START HERE**.

## New animation library

- Idle_Natural, Walk_Natural, Jog_Natural.
- Walk_Turn_L/R, Jog_Turn_L/R, Sprint_Turn_L/R.
- Idle_Turn_L90/R90 (stepping, one-shot pivots).
- ADD_LookAround (rotation-only additive layer).
- Sprint_Fluid and every earlier source Action remain preserved.

Turn clips use curved paw trajectories, inside/outside stride differences,
speed-dependent bank, coordinated chest/hip/spine/gaze and tail follow-through.
The showcase adds independent root travel, phased NLA blending and a reduced
additive paw-contact layer. Its linked actor shares original geometry data.

## Checks and limits

All 3,069 showcase frames were checked for IK reach, ground clearance and abrupt
joint changes; loop closure and subframe contacts were checked on the Action
library. Rendered review covers both directions at all speeds, both standing
pivots, idle and transition poses (86 current rendered views, collected in the
review contact sheets). The final saved file was reopened with auto-execution
disabled. Geometry, rest rig, weights, packed textures and eight previous
Actions match the input checkpoint. The accepted source file is unchanged.

These checks reduce obvious defects; artistic approval still belongs to the
user. Painted eyes have no separate eye rig. Gait turns are in-place Actions
with radius/speed metadata, not a finished game controller. Editing showcase
timing requires rebaking its contact correction. 60 FPS is the scene rate;
actual GPU viewport playback depends on the user's hardware. CPU evaluation
measurements are not GPU FPS measurements.

## Reproducibility

Source checkpoint: `../original-wolf-sprint-playback/Amaterasu-Movement.blend`.
Author with `author.py`, polish with `polish_contacts.py`, then use `demo.py` on
the resulting **single-scene** checkpoint. Do not run demo.py on the already
assembled two-scene delivery. `finalise.py` sets the opening scene and guide.
`validate.py`, `check_actions.py` and `smoke_saved.py` record the checks;
`render_review.py`, `render_showcase.py` and `sheets.py` create review media.

The game and browser viewer were not modified. This separate branch does not
replace their versions. Original model attribution: [LICENSE-SOURCE.txt](LICENSE-SOURCE.txt).

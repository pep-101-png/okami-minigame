# Independent trailing spirit motion

Corrects the user's latest in-game screenshot: mirrored quarter-circle fans and
elastic-looking motion remained after the previous geometry/material repair.

The original ES wind clips carry a large authored resting bend and root twist.
This adapter now removes their mean rotation and keeps their small wind variation
around a shallow trailing bow. Bone-delayed sampling moves the wave along each
trail instead of opening/closing an entire bent pose together. The six trails
have separate mounts, lengths, speeds, phases, strengths, bows and bending planes.
No left/right mirror choreography remains. Roots are pinned directly to the torso;
bind-chain positions and bone scales are fixed rather than elastically following
or lengthening. The bounded translucent material and third-form-only rule remain.

All meshes, paints and motion inputs remain recovered original Ōkami data. This
is an adapted motion treatment, not a claim of original-game effect playback.
Other gameplay, audio assignments and previous fixes are unchanged.

Validation: actual C# compiled against explicit engine doubles with zero errors.
The real effect is exercised at 15/30/60/120fps for profile independence, pinned
roots, constant lengths/scales and small joint rotations. Native-data diagnostics
check head clearance in idle, run, charge and howl poses, and sampled directions
remain within 18 degrees of rearward, rather than turning into quarter-circle fans.
Twenty still diagnostics and a six-second/90-frame offline motion preview use the
actual profiles, native player bank, native effect bank and material blend/fade
rules. Encoded MP4 frames were inspected and full decoding passed.

No current Unity import, shader compilation or Play Mode/motion verification is
claimed. Latest published automated PC feedback is older and cannot approve this
patch. The motion preview is explicitly offline and stays outside Unity Assets.

# Amaterasu — neck motion and playback repair

Open Amaterasu-Movement.blend in Blender 4.3+. Sprint_Fluid is selected.
Press Space. The previous Sprint_Polished, Sprint, Idle, Walk and Jog Actions
remain available. See OPEN-IN-BLENDER.txt, also embedded in the project.

The neck controls, constraints and weights were working. The previous clip
combined same-direction neck motion with an exact world-space head orientation.
The new clip distributes counter-flexion through the two neck joints with a
phase offset, and retains some neck inheritance in its head stabilisation.
No extra neck keys, bones, constraints or authored weight changes were needed.
All non-neck/head animation curves, including body, legs and tail, are identical.

The file was already 60 FPS with continuous Bézier interpolation. Profiling
found a real CPU bottleneck in two live SIMPLE subdivision modifiers: about
86 ms per evaluated frame here. Precomputing their existing surface before
skinning reduced this to about 3 ms. Evaluated vertices and normals match the
previous project exactly in 25 retained poses. Original base mesh datablocks
are stored in the project as ORIGINAL_BASE, and the previous project is intact.

FULL · Painted wind retains the finished wind. FAST · Lightweight wind uses
three opaque preview streaks, with the original textured wolf. The preview
objects and FAST layer are disabled for rendering; the full effect remains.

CPU evaluation now fits the 16.7 ms budget for 60 FPS. This is not a guarantee
of 60 drawn FPS: the software-rendered cloud display remained GPU-limited
(about 4.3 FPS full Material Preview, 4.7 with light wind, 12.6 Solid). Those
are not Windows GPU measurements. Actual viewport FPS depends on hardware,
viewport size and shading. The optional preview and Solid mode allow cheaper
motion inspection without changing the final materials or finished effect.

No game or browser viewer files are changed. Source attribution is included.

# Continuous full-power spirit wisps

Replaces the previous rigid bone-strip adapter. Each of ten strands now follows
its own continuous 3D travelling wind curve. Unit-tangent integration fixes its
arc length; Catmull–Rom interpolation deforms the original-derived ES4A/ES4B
vertices between controls. There is no mirrored pose pair, 90-degree resting
bend, spring or periodic stretching. The original native paint and tapered
geometry are preserved; a broad translucent profile with view-facing edge fade
softens the previous bright narrow strips. Roots remain on the torso/flanks.
Only ES3A full power displays these wisps. Other gameplay/audio is unchanged.

The wind motion and shader treatment are adapted code, not recovered original
wind animation. Source geometry/paint are original-game derived; no external art
or audio was added.

The C# engine-double suite covers continuously moving curves, pinned roots,
constant arc length, independent profiles and full-power-only visibility at
15/30/60/120fps. Native-vertex shader emulation checks clearance through actual
idle/run/charge/howl poses. Existing asset/audio preservation checks remain green.
Review uses actual source model data and a corresponding offline OpenGL shader,
with twelve stills and a separate four-second 60fps motion preview. This preview
is a diagnostic render, not a Unity recording, and is not included in Assets.

No current Unity import, HLSL shader compilation or Play Mode verification is
available. Latest published PC feedback still describes the older October 21
source, with incomplete coverage on all fourteen clips; it cannot validate this
change. Offline rendering does not establish perfect in-game appearance.

Variety update: preserve the approved six strands and their motion exactly; add
four staggered small/medium/large companions with independent width/length.
Lengths now span 0.43–1.14 and extra widths span 0.65–1.15, without changing the
approved curve motion or making the original strands brighter.

# Gate-owned heaven return

The user confirmed that pause-menu Return Home works and that the outdoor torii
can be walked through without a transfer. Replace the separate garden coordinate
poll with a HeavenReturnPortal component on the actual visible gate transform.
The existing curtain, light, particles and solid posts are preserved.

A kinematic trigger handles entry/stay. The same component independently sweeps
player movement through the local opening, so low frame rates cannot skip it.
The sensor is independent of garden realm/height/interaction/Locked checks. It
respects active cinematics. WolfMotor exposes a teleport revision so real movement
can be swept at any speed without treating realm transfers as walking segments.
The gate runs after movement and before the garden's visibility/global refresh.

The old test only counted a ReturnHome call. The new harness compiles and executes
the real ReturnHome, ClearEnemies, ClearProjectiles, Close and WolfMotor.Teleport
routines, together with the real portal builder/component and combat code. Its
engine double implements parent-space position, rotation and scale. Cases cover
a shifted/rotated gate; trigger and polling activation; 5/15/30/60/120fps movement;
a complete 16m crossing between samples; ordinary teleports not activating the
sweep; stale dialogue/locks/upper-tier probes; full transfer and control/pose/pool
cleanup; non-player colliders; post clearance; and repeat visits. These are C#
integration checks with explicit engine doubles, not Unity physics verification.

No current Unity import or in-game playback is available. Latest published PC
feedback still targets the old October 21 source with incomplete clip coverage.
The user will test this portal-focused cumulative Assets update. No other gameplay,
weapon, music, portrait or approved tendril change is included in the source diff.

# Double ultimate explosion effects

Only SolarPaint.cs changes in Assets. Double the ultimate burst quad size and distance from its ground origin. Double SolarBlast, CannonFire, SolarPuff, ImpactDust, OriginalWhiteRing and ImpactRocks counts. Keep one enlarged core and glow each, avoiding duplicate coplanar overlays. Interleave the six shockwaves at half the former delay, preserving the blast lifetime envelope. Total burst quads increase from 185 to 368.

The approved charging sun, cinematic pose and camera, Eight Wonder impact, sounds, damage and timings remain unchanged. All paintings and audio are original assets.

Ran the actual-driver runtime fixture (713 assertions), captured new geometry and rendered it at normal speed. verify.py compares 15,355 quads for doubled size/spread and confirms the body/camera/audio/damage capture and sword impact remain unchanged. Visually inspected encoded burst frames. The renderer uses actual driver outputs with Unity API doubles; it is not Unity Play Mode or a PC performance test. Latest fetched Unity feedback is still the October 21 build, with all fourteen clips marked incomplete; it cannot validate this change.

Reproduce: run tools/solar-ultimate/runtime.py, tools/solar-ultimate/review.py, then this folder's verify.py. The delivered preview is the ultimate portion of the full review at 1.8–9.2 seconds, normal speed, with original scheduled audio. package.py publishes a cumulative Assets-only ZIP and the MP4 separately outside Assets.

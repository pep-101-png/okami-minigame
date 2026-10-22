# Amaterasu river and airborne motion

The existing model, rig, 47 animation clips and Animator controller are retained.
`CanineMotionPose` supplies rest-relative skeletal IK paddles, jump gathering and
an observation-mat seated pose after Animator evaluation. It changes no bone
scales and never translates the player root. All 14 required front/rear
upper/lower/paw/hock names were verified against the actual Amaterasu FBX with
Blender's importer. Missing core bindings produce one warning at initialization.

`WolfMotor` now floats in deep river water, including beneath bridge arches.
Walk/jog/sprint controls also select gentle/normal/fast paddling. Jump leaves the
water; a second press while airborne performs the double jump without requiring
an upgrade. The third press is rejected until grounded or swimming again.
Entering water no longer causes a timed shore teleport. Invalid/non-finite world
positions and falls below -6 still use the existing safe-location recovery.

Original jump clips (~1.8 s) are played over the motor's ~0.7 s flight, with
rest-relative leg gathering/reaching. The source clips are not rewritten. A quiet
noise-only paw takeoff replaces the pitched 520 Hz jump ding.

`Test-WaterMovement.ps1` exercises the shared engine-free policy in PS5.1/PS7:
13 depth/bridge/jump cases, plus three minutes of buoyancy integration at
30, 60 and 144 FPS. Ran successfully with PowerShell 7 in the cloud. The harness
uses C# syntax accepted by the older PS5.1 Add-Type compiler; PS5.1 itself was
not available here.

`render_pose_preview.py` imports the real FBX in Blender and reproduces the FK/IK
pose geometry for authoring inspection. It uses neutral materials to inspect
limb geometry; these pictures are NOT Unity renders or the final in-game shader.
Run: `blender -b -t 3 -P tools/living-world/movement/render_pose_preview.py`.

Still needs actual Unity 6000.6.6f1 testing: physics around banks/under arches,
waterline/body placement, continuous paddling, jump/landing blending, real skin
deformation and camera behaviour. Static syntax/policy tests do not verify those.

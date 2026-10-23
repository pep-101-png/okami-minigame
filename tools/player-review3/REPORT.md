# Sunward — Player fixes 3

This is a **changed-files update** for the existing Sunward project, following Player Fixes 2. It is not a replacement game. The ZIP is arranged for dragging its `Assets` folder into the existing `Sunward-Unity` folder and replacing matching files. No old files need manual deletion: superseded scene objects are disabled in the saved scene.

## What I changed

### NPC footsteps and the constant glitching noise

The resident foot solver could reset a foot's stance flag as it corrected its position, then treat the same planted foot as a new contact and play another step. Sound was tied to that correction flag. Multiple residents could produce overlapping sounds, even around stopping or correcting their feet.

I removed sound playback from that contact-repair path. Steps now require real distance travelled, a minimum walking speed and an individual cooldown. A shared village budget allows at most five step sounds per second, and only residents within 5.5 metres of Ammy are audible. Sources do not loop; each step uses a new quiet 90 ms sole sound. Standing still, tiny jitter and teleports do not generate steps. The budget resets correctly between Unity play sessions, including when domain reload is disabled.

### 1. Tree roots

The previous detached little root meshes were insufficient. I replaced the flat root fans on all 21 existing tree trunks with rounded, branching root growth integrated into each actual trunk mesh. The roots use the trunk's own colour family, tapered forks, bark seams and terrain-aware seating. Leaf litter surrounds their bases. The first revision still looked like flat fins in a Blender preview; I rejected and revised it before delivery.

### 2. Bamboo, market decorations/glitches and the mill

- Reworked all seven visible replacement bamboo clumps: different culm heights, taper, bend, node spacing, alternate branching leaf fans, colours and young basal shoots. Their saved meshes are distinct. Original superseded bamboo remains disabled.
- Restored a fuller coloured market canopy with 24 red, blue, pink, gold, green and violet paper lanterns on three ropes. Supports sit in clear street lanes outside the stall frames. The existing coloured practical lights remain active. This is newly authored replacement decoration, not a claim that the previous missing canopy had survived unchanged.
- Found a remaining combined black-ink source mesh shared across the original world. Hiding individual old stones/stalls did not hide its corresponding ink faces. The saved scene now uses a copy with the market/mill region's obsolete ink triangles removed. Also retired the original low timber market bars. This directly addresses leftover geometry as well as the earlier shadow changes.
- Added a joined timber floor inside the rice-mill building and disabled a nearby stone's shadow casting. The mill's working wheels, gears and millstones remain. Whether every unwanted mark in your particular view is gone is still unverified in Unity.

### 3. Sundial positioning, effects and attack motion

The disc is now horizontal above the back, with the engraved face upward. Chest-follow displacement is tightly bounded. During attacks it sweeps around the shoulders and returns continuously, with two/three spins, instead of merely tilting through the rear body. Idle rotation is retained.

Replaced the broad blue/orange loops with seven tapered warm ivory/gold/red flame tongues rising from the engraved side, plus a short attack-only sweep trail. Changed the flame material to restrained alpha blending. Added coordinated body compression, restrained pelvis/chest/neck counter-rotation and paw compensation over the retained attack clips. A geometry preview exposed a face-direction error; that was corrected before delivery.

This is presentation work: damage, hit windows, rewards, weapon ownership and arena-only visibility are preserved. It is not a claim that every live attack now looks professionally finished.

### 4. Floating door arches

The previous adjustment used the roof overhang as its front reference. Arches now attach to the actual recessed wall front, with explicit wooden corbels/supports beneath them. All 42 fascia parts are adjusted; inactive replaced buildings remain inactive. A representative saved house and its attached arch were rendered and inspected in Blender.

### 5. Market chatter

Disabled the old continuous market-noise loop. Replaced the repeated synthetic exchange with a softer, voiced harmonic sound without a white-noise layer, added clean fades, and limited nearby conversation to one phrase every 4.5 seconds village-wide. This is quiet synthesised wordless chatter, **not recorded human/Japanese dialogue**. Sound quality still needs listening in the game.

### 6. Musician and Japanese-style music

Enlarged the violin body/neck by 50% and increased the bow to about 70 cm. Repositioned the hand targets for the larger instrument. Replaced the old short bowed loop with an original 48-second Japanese-style composition using an in-sen-inspired melody, koto-like plucked strings, a restrained bowed lead and sparse flute-like responses. It is generated instrument synthesis, not a professional recording or a copied commercial track.

### 7. Samurai practice swords

Authored larger approximately metre-long bokken with shaped blades, wider guards, wrapped grips and wood definition. The grip stays in front of the face throughout windup/strike/recovery. Both arms follow the grip, and the blade swings toward the dummy instead of beginning behind/inside the head. Sampled held-prop poses were inspected in Blender; live motion and dummy contact remain unverified.

### 8. NPC and enemy appearance/motion

All seven resident model families have revised facial planes, contained almond lids/pupils, nose planes, fuller face proportions, collars, hands/fingers and cloth folds. Long garments now follow a restrained amount of leg motion rather than remaining rigid. Their existing rigs, role identities, interactions and routes remain. Fixed a skin-weight normalisation defect exposed by the new garment folds.

All six enemy families have additional carved mask channels, tied paper charms and layered clothing detail. Joint presentation now eases between poses instead of snapping directly when the combat state changes. Their established identities and gameplay definitions remain. These are iterative improvements to the current models, not a claim of a finished professional character set.

### 9. Running, jumping and landing

Added distance-driven quadruped paw targets, with walk/trot/gallop phase patterns, a restrained body rise and softer gait blending on the existing skeleton. Jump gathering and landing reach now follow vertical movement rather than a fixed short sine timing alone. Added restoration before Animator evaluation so unkeyed procedural offsets cannot accumulate across frames. Attack and swimming poses remain separate.

Lengthened the landing transition slightly and replaced the loud pitched/noisy landing placeholder with a padded paw sound at a much lower gain. Source animation files and Ammy's original mesh, markings and rig were not replaced.

### 10. Temporary P-key Shiranui appearance

P toggles an added ivory cloud-mane and animated white-gold streamers. Press P again to return to normal. The switch is an **appearance preview only**: it does not write the save, unlock upgrades or change combat balance. It does not display an unwanted ground indicator circle. The cloud-mane geometry is additional; Ammy's recognisable base appearance remains intact.

## Uploaded st0.zip

See `ST0-INSPECTION.md`. I decoded the actual uploaded archive and found architectural textures and recognisable building/shrine geometry. I inspected texture contact sheets and raw geometry previews. The extracted game assets were **not** added to this update. Their instance transforms, UV associations and conversion into complete Unity-ready houses are a separate unfinished step.

## What has and has not been verified

Completed local checks include C# syntax parsing for editor/player modes; saved-scene references and asset GUIDs; native mesh indices, normals, bounds and skin weights; preserved red bridge rails; real-distance footstep simulations at 30/60/144 FPS; a 20-resident shared sound-budget simulation; stationary/jitter/teleport suppression; audio PCM/loop endpoints; and changed-files ZIP checks.

I rendered and inspected Blender geometry/pose previews of the bamboo, roots, a wall-attached doorway, the market canopy, shield fit, cloud-mane, resident appearances/props and sampled wolf target poses. These are **Blender previews, not Unity renders or live animation approval**. Target-pose previews do not test Unity's blend with source clips, collision, animation timing or shader output.

No Unity executable is available in this cloud environment. **Unity compilation, actual gameplay, final lighting/shadows, sounds, shader appearance, frame rate, live animation blending and your PC remain unverified.** No recordings, PC tasks, syncing changes, automatic merge or paid services were used.

## Opening and checking this update

Close Unity. Extract the ZIP. Drag the extracted **Assets** folder into your existing **Sunward-Unity** folder (the folder that already contains Assets, Packages and ProjectSettings). Allow folders to merge and choose Replace for matching files. Do not delete your existing Assets folder and do not put the patch's Assets folder inside it.

Open your existing project normally. After importing, the welcome/pause menu should say **River & Lanterns · Player fixes 3 · 23 October 2026**. Test NPC sound at close/far distances, day/night market decoration, mill marks, roots/bamboo, door arches, both weapons in the arena, jumping/running/landing, student swords, the musician, and P on/off. The report identifies uncertain results rather than calling them passed.

## Unity compilation correction

Removed the obsolete Object.GetInstanceID call from resident footstep pitch after a confirmed Unity CS0619 report. Pitch is now neutral; distance gates, quiet volume and global rate limits are unchanged. All 88 C# files passed syntax parsing, the source audit found no remaining GetInstanceID calls, and footstep simulations passed. Actual Unity compilation on the Windows PC remains unverified. Download ZIPs contain project files only.

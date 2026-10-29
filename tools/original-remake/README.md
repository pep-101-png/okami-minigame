# Existing Sunward / Windflower original asset integration

Status: IMPLEMENTED SOURCE CANDIDATE — Unity compilation and Play Mode not verified.
This is not a completed or approved remaster. No replacement/demo gameplay scene
was created. The target is `Assets/Sunward/Scenes/Windflower.unity` with its
existing GUID and build entry.

Actual saved-scene work: 856 original model placements, including 14 existing village-house
roots plus the playable home, the two working Taro/Hana market footprints,
21 tree roots, seven bamboo roots, rocks, flowers, grass, lanterns, bridges,
an original waterwheel, a trial-entry gong, original futon, mirror prop and shelf.
Original ET/VT props are adapted to Sunward roles; e.g. the mirror prop is not
claimed as a fully reconstructed original Origin Mirror save system.

Seven main NPC prefabs and six existing ambient NPCs use original HM skins,
rigs and native source motions. Six existing enemy-role prefabs use original
EM00/01/02/03/04 and EM11 appearances and source motion banks. The existing
controllers, dialogue identities, stats, combat rules, wave schedule, saving,
progression, world data and all 315 existing collider blocks are preserved.
Enemy mesh visibility/attachment states still need Play Mode review; original
AK/SEQ state dispatch has not been fully reconstructed.

The player keeps the original PL00 model/rig and native action bindings from the
preceding repair work, included in this branch. The second weapon now uses WP25
original glaive geometry and motion; WP34 was confirmed as a Solar Flare variant
and is not used for the glaive. Solar Flare retains original WP24 geometry,
paint and skeletal flame deformation. Invented flame orbit and power curls are
removed. Weapon and enemy display titles now describe the native appearances;
save IDs and mechanics are unchanged.

All 13 human actors and six enemy roles have native motion resources wired.
Imp combat uses inspected `em00_130`; Crimson Helm uses inspected `em65_020`,
sampled through windup/strike/recover windows tied to the existing AI timer.
The imp `em00_040` source sequence shows collapse. A confirmed full boss death
sequence is not identified; the boss uses a native hit reaction before its existing
despawn. Action timing, foot contact, attachment positions and every semantic
mapping are not approved until tested in Unity. Native curves follow the existing
30 FPS / 60 Hz port convention; source timing is not universally encoded in MOT.

The terrain and water retain Sunward's layout surfaces and collision heights.
Their artwork is rebound to byte-identified native Kamiki DDS paintings. The
layout mask remains layout/control data. The procedural sky is replaced by an original illustrated-paper sky adaptation.
The original thin tree/bamboo paintings
receive a camera-facing rendering adapter so they do not disappear edge-on.
GT18's completed bridge mesh group is fitted to the preserved walk-deck arch;
no new bridge plank artwork is generated.

Only three original PL voice clips are connected. Their cue assignments are a
Sunward adaptation, not a recovered original event table. Generated tones,
third-party ambience/music and unmapped ambient particle artwork are disabled.
Missing authentic music, ambience, general combat/footstep/bell/collect banks
remain silent. UI paper/ink come from original images; readable existing UI fonts
remain because an original font bank has not been supplied.

ET08/ET09/ET24 original models and paintings provide adapted existing gameplay
feedback and projectile appearances. These are not faithful recovered EST/SEQ
emitters, Solar Flare trails or impact sequences. Full native effects remain
unfinished. No substitute orbit is presented as an extracted original effect.

`integrated-assets.csv` lists 63 actually referenced original model packages with source
payload hashes. `original-assets.json` also records 139 converted model candidates; conversion
alone is not integration. `media-bindings.json` records exact image/sound sources.
`world-install.json` lists scene IDs, prefabs, placements and motion bindings.
`player-animation-bindings.csv` lists every retained native Amaterasu action
assignment, including walk/run/sprint, jump/landing, dodge and disc/glaive combat.
These bindings existed in the preceding repair branch; they are included in this
update, not claimed as newly discovered animations.

Modified gameplay prefabs: NPC-0 through NPC-6; Enemy-wisp/reed/ranged/heavy/elite/
boss; Spear. The existing Sundial native adapter and player scene component are
retained. Existing enemy/weapon definitions change display titles only. The new
Editor validator checks native resources instead of requiring the old procedural
NPC rigs or non-original market audio. No Windows task was started or enabled.

Offline verification checks preservation, GUIDs, native weight/index streams,
finite pose banks and motion bindings; C# syntax parses separately. This is not a
Unity compilation or gameplay pass. Unity 6000.6.6f1 is not installed in this cloud
environment. The latest published PC feedback belongs to older commit
`aefd595771e933a3313ecb4170251764c94ab1e3`; all 14 clip statuses and sampled MP4
sequences were inspected, showed incomplete action coverage, and cannot verify
this candidate. No direct communication with local VS Code Codex is claimed.

The screenshots in `previews/` are permanently labeled Blender diagnostics of the
saved static scene plus offline native poses, not Unity screenshots. Arena enemies
are a diagnostic lineup, not a recorded runtime wave. Source inputs remain intact.
Rollback: `backup/sunward-before-original-only-20261030` at
`ee9af00b74c8157bfc93a150068b31e23d3c331f`.

Reproduce source conversion outside Unity with `export_assets.py --inspection
/path/to/full-asset-inspection`, then `install_world.py`, `bind_paint_audio.py
/path/to/full-asset-inspection` and `verify.py`. The installer deliberately starts
from the pinned rollback scene; do not run it over unrelated uncommitted scene edits.

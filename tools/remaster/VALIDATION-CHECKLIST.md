# Actual Windflower acceptance gates — runtime results pending

The existing **Assets/Sunward/Scenes/Windflower.unity** is the target. Never use the separate demo scene or a Blender image as proof of running-game verification. Record exact source commit, Unity version/backend, logs and actual captures.

| Gate | Status |
| --- | --- |
| Existing scene/layout/gameplay-object preservation | Offline object/component and file comparisons pass; play verification pending |
| Actual house/market/ST2 rock/bridge/torii replacements | Saved scene bindings and native mesh/material data checked; Unity rendering pending |
| Cherry/bamboo/grass/decorative flower integration | Saved live bindings checked; alpha/wind/lighting/play verification pending |
| River and recessed pond | Actual material bindings checked; shader compilation/refraction/depth/shore/bridge play pending |
| Native ambient animals | 13 actors/nine types configured; static route clearance checked; actual spawning, foot contact, loops, avoidance and performance unverified |
| Unity import/C#/shaders | Not run; 82 C# files pass syntax parsing only |
| Ammy native idle/walk/run/sprint/jump/landing/dodge/combat | Native 38-bone adapter installed; 47 states bind 34 original motions; converted skinning independently checked, actual contacts/timing/attachment/playback unverified |
| Solar Flare model/texture/animation/effects | Original wp24 model/paint/skeletal flames configured with fallback; full EST/SEQ particles, native trails/impacts and original attack choreography incomplete |
| Player movement/combat/equipment | Motor/input/data and combat methods preserved; visual playback/socket bridges added; full play regression pending |
| All NPC roles/dialogue/quests/shop/routes | Existing data/rigs/components preserved; interactions/navigation play regression pending |
| Home/interior/cutaway/mirror/rest | Existing logic preserved; clearance/cutaway/save play regression pending |
| Arena entry/four waves/elites/Kurogane/rewards/return | Existing logic/data preserved; play regression pending |
| Existing save loading/writing/backup recovery/permanent upgrades/collectibles/UI/audio | Save/progression/UI/audio files preserved; play regression pending |
| CPU/GPU/memory/load-time/build size/Windows build | Not measured or built |
| Actual screenshots/video of changed Windflower | Not available; current comparison images are explicitly Blender layout previews |

The existing Editor **Sunward/Verify Windflower Connections** diagnostic now recognises the new painting paths and river shader and checks assigned remaster shaders for errors. It has not been executed here. No Windows task, automation dispatch or paid service is enabled by this work.

The full remaster remains incomplete until the incomplete weapon effects and unverified player/weapon integrations and actual runtime gates pass.

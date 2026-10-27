# Sunward remaster review stage

**Not the finished remaster.** The existing Windflower game is preserved. New assets are staged on `remaster/okami-native-integration` for review before live replacement.

Read [the full report](REPORT.md), [progress ledger](PROGRESS.json), [1,838-row asset matrix](audit/replacement-matrix.csv), and [offline results](audit/offline-validation.json).

With the existing Sunward project open in Unity 6000.6.6f1, the added **Sunward → Remaster** menu opens the village review scene and checks imported review assets. The scene is also present directly at `Assets/OkamiRemaster/Village/Demo/Scenes/VillageDemo.unity`. Windflower remains the startup/build scene. Default Ammy and both Solar Flare model variants are diagnostic `.okamimodel` assets under `Assets/OkamiRemaster/NativeReview`. The preserved MOT files are source bytes, not playable Unity animations.

The downloadable review update contains only new `Sunward-Unity/Assets/OkamiRemaster` assets/metadata and `tools/remaster` reports/tools. Apply it to the repository containing baseline `00fd8695363df01de80b012d68feb20c9961e8a9`; it is not a standalone game/project or a Windows executable. Keep the existing project and original LFS assets. This stage was not compiled or played in Unity here.

Offline check (Python with NumPy, tree-sitter and tree-sitter-c-sharp):

```bash
python tools/remaster/check_review.py --output tools/remaster/audit/offline-validation.json
```

The hash check expects a hydrated baseline, including the original LFS idle clip. Native review conversion can be reproduced from the two decoded inspection folders with Python and Pillow:

```bash
python tools/remaster/export_native_review.py --pl /path/to/pl-inspection --wp /path/to/wp-inspection
```

The decoder/source inspections are separate research inputs, not downloaded automatically. Shader compilation, exact native motion/timing, feet/root motion, weapon sockets/effects, navigation, saving, arena combat and performance still require actual Unity results. `VALIDATION-CHECKLIST.md` records the acceptance gates. No automation tasks or paid services are enabled by these files.

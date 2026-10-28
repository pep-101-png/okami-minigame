# Existing Sunward remaster — work in progress

The actual modified game scene is **`Sunward-Unity/Assets/Sunward/Scenes/Windflower.unity`**. Open that normal gameplay scene and press Play. There is no separate review-scene step.

The live scene now references replacement houses/markets, ST2 bridges/rocks/torii, painted reference cherry trees, recovered environmental/botanical paintings and an ambient native-animal component. The existing layout, NPCs, arena, systems and save code remain. Read [REPORT.md](REPORT.md) for actual counts, provenance and limits.

**Original Ammy skin/rig and 34 original motions are now connected to all 47 existing action states through a native visual adapter. Solar Flare's original model, paint and skeletal flame motion are configured. Its separate native particle/trail/impact dispatcher remains incomplete. Unity compilation/play/visual verification is unavailable here: this is still an unfinished remaster.**

The `tools` folder contains reports, authoring/research inputs and offline checks. You do not need to run or copy it to play the updated Unity project. Active assets are saved in Assets, including Windflower's existing scene file. Reference scenes/menus are archived outside Assets.

Use the latest download links in [DOWNLOADS.md](DOWNLOADS.md). The earlier Stage1 Review ZIP is superseded and did not change the main town. Keep existing projects backed up; a partial Assets update must be merged, never used to delete the existing Assets folder.

Developer checks require Python, NumPy, Pillow, tree-sitter and tree-sitter-c-sharp:

```bash
python tools/remaster/check_review.py
```

Authoring is reproducible from retained reference inputs with `python tools/remaster/live/apply_windflower.py`. Then run `export_player.py` and `install_player.py` from the same folder to install the native adapters. The environment authoring command starts from the protected scene snapshot and writes the actual scene, so it is for developers—not an installation step. Runtime acceptance gates are documented in VALIDATION-CHECKLIST.md.

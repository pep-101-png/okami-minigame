# Actual Windflower game implementation — work in progress

The earlier **Stage1 Review Update** is superseded. This version modifies the existing game scene. Original Ammy skin/rig and 34 native motions are configured across 47 existing states; original Solar Flare model/paint/skeletal flames are configured. Full native particle/trail/impact effects and Unity compile/play verification remain unfinished.

- [Full Unity game project — WIP](https://github.com/pep-101-png/okami-minigame/raw/refs/heads/delivery/windflower-native-player-20261028/Sunward-Windflower-Game-Project-WIP.zip)
- [Smaller Assets update for an existing working Sunward project — WIP](https://github.com/pep-101-png/okami-minigame/raw/refs/heads/delivery/windflower-native-player-20261028/Sunward-Windflower-Assets-Update-WIP.zip)
- [Download sizes and SHA-256 verification](https://github.com/pep-101-png/okami-minigame/blob/delivery/windflower-native-player-20261028/Download-Verification.json)

The full project is a copy of the existing Sunward game with the saved Windflower changes, not another demo village. Extract it into a fresh folder, retain the existing working copy, open its **Sunward-Unity** folder with Unity 6000.6.6f1, and open **Assets/Sunward/Scenes/Windflower.unity**. Press Play. There is no special remaster-review scene/menu step and no executable is included.

For the smaller update, close Unity and merge the ZIP's **Assets** contents into the existing **Sunward-Unity/Assets** folder. **Keep the rest of your existing Assets folder and all metadata; do not delete or replace the whole folder with a partial update.** The update contains the actual modified Windflower scene and its dependencies. It requires a working baseline game and does not remove older leftover review files from an existing installation.

The `tools` folder is for reports/research/authoring and is not required to apply the saved game changes. These packages are unverified source work in progress, not a claim that Unity compilation, gameplay, native animation playback or full Solar Flare effects have passed.

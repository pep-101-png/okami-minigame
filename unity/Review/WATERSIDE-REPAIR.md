# Targeted repair: river rocks, garden pond, home spear and market trees

This focused patch is for the installed `b0a2113` visual-remake project and addresses four reported failures. It does not redo the wolf, animations, town art or gameplay.

## Install — no Sunward update-menu step

1. Keep a copy of your current project folder. Close Unity Editor; Hub can stay open.
2. Extract **Sunward-Unity-Waterside-Fix.zip** into the existing **Sunward-Unity** folder containing **Assets**, **Packages** and **ProjectSettings**. Allow replacement.
3. Reopen the project and **Windflower**. Wait for compilation/import. The repair runs automatically once, saves a scene checkpoint under `Review/LocalBackups`, applies the changes and saves Windflower.
4. Look for **“Waterside repair 1 saved”** in Console, then press Play.

The marker **Windflower · grounded waterside repair 1** is only marked validated after the connection/contact checks pass. Opening an already repaired scene does not reapply the migration. An error logs the reason; it must not be treated as a successful repair. The manual **Repair Waterside and Home Display** command is a recovery option, not a routine installation step.

The ZIP contains only nine explicitly listed repair code/shader files, their metadata and the repair instructions/checks. The broader project archives are not part of this corrective release. It contains **no wolf FBX, textures, animation clips, controller or save data**, and requires no model/animation repair command.

## What was wrong and what changed

- **Rocks:** the earlier check considered a low point relative to the walking-height sampler. That sampler can return a bridge deck rather than the physical riverbed, and a low point is insufficient to demonstrate a supported base. The new sampler matches the terrain's actual triangle diagonal. Closed stones with flat underside geometry replace the affected source islands; foundations sample the full footprint, with height adjusted to fit the bank relief. The repair reads immutable `Valley.bytes`, even after previous scene migrations filtered away old faces. It suppresses the older replacement-rock root and removes the corresponding original source faces.
- **Pond:** the original water sheet was at **+0.020**, above its bank. The repair lowers water to **−0.230**, excavates the actual terrain into a basin, builds a broad earthen rim and places the water mesh edge beneath that rim. It replaces the old water/lotus planes, removes the obsolete flat ground decal, and places new leaves/flowers on the lower surface. A dedicated pond shader uses scene depth, refraction, ripples and highlights. Terrain row-seam normals are averaged so the bank shades smoothly.
- **Spear:** the eight baked source sections `Valley-743` through `Valley-750` are disabled as GameObjects, not just renderer flags. Older separately instantiated decorative spear copies are also suppressed. The accepted wall-rack hierarchy and everything under the player are excluded. The repair requires exactly one named spear mount on the accepted rack.
- **Market trees:** both old source tree groups and replacement tree prefabs are checked against the market's full space, including canopy bounds. Trees that intrude are suppressed; matching physical trunk colliders and navigation circles are cleared. This avoids checking only the trunk centre while leaving branches through stalls.

## Evidence and limits

Portable checks pass for **122 stone placements**, **36,600 underside support samples**, **2,560 actual terrain-triangle samples**, and **360 pond-boundary samples**. Maximum terrain sampler discrepancy in those samples is under **0.00001 units**. The replacement stone geometry is closed and outward-facing. Syntax and existing portable save/combat checks also pass.

`waterside-geometry-diagnostic.png` is a **Blender geometry-only inspection of the C#-exported repaired terrain, stones and water**. It is not a Unity screenshot and does not validate the Unity materials, scene migration or runtime state. Untextured inspection materials are used to expose ground contact.

**Unity Editor is unavailable here. Unity compilation, shader compilation, automatic scene migration, final spear/tree visibility and Play Mode still require local validation.** The patch implements and checks the repair; its final appearance is not approved or claimed visually verified in Unity.

The original wolf assets and animation processors are unchanged. Baseline `b0a2113` remains recoverable in Git and your local folder backup.

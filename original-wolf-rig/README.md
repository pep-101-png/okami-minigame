# Original Sketchfab wolf — Blender rig review

This is a separate rigged copy of the approved **original** upload. It does not use
any of the later wolves' geometry, paint, shaders, fur, rigs or animations.
The game and browser viewer are unchanged.

## Open on Windows

1. Download `Original-Sketchfab-Wolf-Rig.blend` (or extract the small ZIP).
2. In **Blender 4.3 or newer**, use **File → Open** and select the `.blend`.
3. The file opens in Pose Mode with `WOLF_RIG` selected. Use the controls around
   the wolf. If necessary, select `WOLF_RIG` in the Outliner and press Ctrl+Tab
   to enter Pose Mode.
4. Press **Z → Material Preview** if the original paint is not visible.
   All original texture images are packed; no texture folder or plugin is needed.
5. The Text Editor contains **START HERE — posing and preservation** with the same
   control guide as `OPEN-IN-BLENDER.txt`.

## Controls

| Controls | Use |
| --- | --- |
| Gold `CTRL_root` | Move or rotate the whole rig. |
| Gold `CTRL_body` | Move the torso while IK paws remain planted. |
| Green `CTRL_paw_front/rear.L/R` | G to place paws; R to rotate them. |
| Orange `CTRL_pole_front/rear.L/R` | Set elbow/knee bend direction. |
| Blue hips, spine, chest, shoulders and neck | Rotate for body posing. |
| Purple head, jaw and ears | Rotate; use small local-X jaw rotations. |
| Teal `CTRL_tail_01` through `05` | Pose the entire original curved tail. |
| `CTRL_toes_front/rear.L/R` | Rotate toes independently. |

Select all visible controls in Pose Mode, then **Alt+G, Alt+R, Alt+S** to reset.
Bone collections separate the animator controls from hidden deform and mechanism
bones. The original component meshes are separately organised in the Outliner.
The preview lights and camera are optional and are not part of the wolf.

## Preservation and scope

All ten original mesh pieces are retained, including the inward black outline
hull. Vertex coordinates, faces, UVs, split normals, smooth flags, material slots,
shader node graphs and texture images are preserved. Modifiers and skin weights
are additive and editable; no modifier is applied to the mesh.

Front-face culling is enabled for the same outline-shell display correction used
by the approved recovery viewer. Do not recalculate the original hull normals.
Material Preview, Eevee and the approved browser rendering support this display;
Cycles does not honour the same material backface-culling setting.

The rig includes volume-preserving skinning, a multi-segment body/neck/tail,
non-stretch two-bone leg IK, digitigrade rear hock placement, paw orientation,
toe articulation, shoulder/hip controls and basic jaw/ear controls. The ink shell
uses weights transferred from the actual painted surfaces, rather than a separate
unrelated weighting pass.

Temporary poses check the bind pose, planted-paw crouch, opposing paw lifts,
head/neck and jaw, and tail/spine articulation. The delivered file is reset to
neutral. **There are no animation cycles, actions or keyframes.**

This is a rig for inspection, not a claim that every extreme pose is production
ready. The original low-poly topology, thin ornamental curls and existing mouth
interior are unchanged. Large jaw openings and extreme compressed poses require
further review. No topology was added to hide those source limitations.

## Credit

This work is based on **“Amaterasu the Japanese Fox God”** by
[theamazingdonovan207](https://sketchfab.com/theamazingdonovan207),
licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
[Original model](https://sketchfab.com/3d-models/amaterasu-the-japanese-fox-god-6d64c6b79c0942a086cad6d988e35712).
Changes: separate Blender armature, skin weights, posing controls and preview studio;
original mesh and paint retained.

# Unity 6000.6.6f1 obsolete-API audit

Reference: Unity's [6000.6.6f1 source tag](https://github.com/Unity-Technologies/UnityCsReference/tree/6000.6.6f1),
commit `0acd4917d3a9084e752630127b65a6f8f07bb463`. Audited all 27 C# files
under `Assets/Editor/` (recursively) and `Assets/Sunward/Automation/`.

Screened source identifiers against obsolete declarations in the engine/editor
reference source, including conditional branches, then checked candidate receivers,
namespaces and overloads. Identical member names alone are not evidence of an
obsolete call. This is a source audit, not a semantic Unity compilation or a
complete audit of separately distributed package binaries.

| Finding | Classification | Action |
|---|---|---|
| `SerializedProperty.objectReferenceInstanceIDValue` in `BatchValidation.CheckObject` | `[Obsolete(..., true)]`: CS0619 compilation blocker | Replace with `objectReferenceEntityIdValue != EntityId.None` |
| `EntityId` implicit conversions to/from `int`, and `Equals(int)` | Also `[Obsolete(..., true)]` | Avoid introducing an integer comparison/cast in the replacement |
| `Object.FindFirstObjectByType` in validators, capture and environment editor tools | `[Obsolete(..., false)]`: warning only | Leave unchanged to preserve selection behavior and scope |
| `FindObjectsSortMode` and `FindObjectsByType<T>(FindObjectsSortMode)` in `SceneCapture` | `[Obsolete(..., false)]`: warning only | Leave unchanged; not the current compilation blocker |

No additional confirmed obsolete-error calls were found in this scope. Examples
of ruled-out name matches: `AssetDatabase.GetAssetPath(Object)`/`Contains(Object)`
are not the obsolete integer overloads; `SkinnedMeshRenderer.BakeMesh(Mesh)` is
not `Physics.BakeMesh(int, ...)`; `UnityEditor.Animations.AnimatorController`
is not the removed legacy controller type; particle MainModule properties and
AudioSource properties are not obsolete ParticleSystem shortcuts. Existing curve
operations use `EditorCurveBinding` overloads, not obsolete path/type overloads.
No warnings-as-errors compiler response files were found in the project.

The broken-reference check still rejects a null object with a stored nonempty
entity ID, permits intentionally empty references, and ignores non-object fields.
No ID is truncated to an integer. A temporary C# 5 regression fixture exercised
the exact predicate with typed stand-ins (obsolete integer conversions forbidden):
empty, valid, missing, non-object and high-bit IDs passed. All 27 scoped files
passed Roslyn syntax parsing. Neither check substitutes for Unity compilation.

After merge, rerun the existing Windows Unity 6000.6.6f1 validation and inspect
`validation-editor.log` and `validation.json`. Confirm compilation and serialized
scene/prefab checks complete. No actual Unity serialized-reference execution,
graphics output or animation appearance was verified in this cloud environment.

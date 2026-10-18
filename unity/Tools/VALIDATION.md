Development checks (not prerequisites for opening the shipped Unity project):

- `dotnet run --project unity/Tools/PortableTests/PortableTests.csproj` — existing progression/save checks and syntax parsing of Assets C# files.
- `dotnet run --project unity/Tools/WorldTests/WorldTests.csproj` — actual height/navigation/grounding code against the numerical shim and real Valley data. Does not simulate Unity physics.
- `python unity/Tools/validate-assets.py` — binary mesh/map/binding integrity (Pillow needed).
- `blender -b --python unity/Tools/verify-wolf-fbx.py` and `blender -b --python unity/Tools/validate-wolf-restoration.py` — original source versus Unity-copy rest geometry, UVs, texture pixels, clip durations and sampled poses. The latter uses Pillow in Blender's Python.
- `repair-sleep.py` is an authoring operation, not a test. Supply an unrepaired FBX copy after `--`; it refuses already repaired input. It only writes the Unity FBX. Do not rerun it during installation or simply regenerate the FBX from the GLB without reapplying the repair.
- `python unity/Tools/package-update.py`, then `python unity/Tools/package-project.py` — current overlay and full project archives. Never package while a model exporter is still writing.

Required real-engine checks remain in Review/RESTORATION.md. No shim, parser or Blender check proves Unity C# APIs, HLSL compilation or Play Mode work. Use the actual Editor menus and play checklist for those.

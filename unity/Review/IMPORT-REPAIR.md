# Unity 6.6 import repair

Close Unity before copying the repair ZIP contents into your existing Sunward-Unity project folder (the folder containing Assets, Packages and ProjectSettings). Replace the included files, then reopen the project. Run **Sunward > Create or Rebuild V3 Scene** once. Clear the Console and check for newly reported red errors.

The reported `_MainTex` Cube-to-2D error occurs during automatic FBX material import. This repair disables that legacy conversion for Amaterasu, imports PNG maps explicitly as 2D textures and binds the original materials using mesh-slot names read from the existing FBX. The precise source of Unity's Cube classification has not been reproduced here.

Both deprecated FindObjectsSortMode calls now use the Unity 6.6 overload without a sorting argument. CS0618 was a warning, not a compilation error.

No FBX, texture, rig or animation binary has been changed. This patch also includes the earlier manifest correction removing the nonexistent textrendering package.

Unity Editor is unavailable in this cloud environment. Asset checks and C# syntax checks are separate from Unity compilation, asset import and Play Mode, which still require verification in the Editor. This repair does not claim that all previously reported errors are resolved.

Cloud validation: all 26 C# files parsed without syntax errors; 18 existing portable progression/save checks passed; mesh/material bindings and all PNG files passed integrity checks. These checks do not compile against Unity assemblies.

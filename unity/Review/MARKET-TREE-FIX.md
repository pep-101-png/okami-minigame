# Exact market-tree repair

The supplied Unity screenshot identifies a scene-root `Cherry_A`, containing `Cherry_A(Clone)` and `Cherry_A_Mesh/Cherry_A_Mesh_MeshPart0` plus `MeshPart1`. It is outside `V3 · preserved painted valley`.

The previous cleanup only searched beneath that town root, so it could not remove this instance. The asset builder also expected one renderer; the screenshot shows two imported mesh parts. Its validation could throw before destroying its temporary model, leaving an uncoloured copy at the scene origin.

## Immediate removal without downloading anything

Outside Play Mode, select the TOP-LEVEL `Cherry_A` in the Hierarchy, not just MeshPart0. Press Delete, then Ctrl+S. This removes the entire stray tree and both mesh parts. Do not delete a model asset from the Project panel.

## Small permanent fix

Close the Unity Editor. Extract `Sunward-Unity-Market-Tree-Fix.zip` into the existing Sunward-Unity project root (the folder containing Assets), replacing the listed script files. Reopen Windflower. No world rebuild or graphics update is needed.

The new cleanup inspects all scene roots, identifies actual tree mesh names/owners, and includes both mesh-part names from the screenshot. It suppresses the whole outer `Cherry_A`, removes matching collision/navigation obstacles and saves the scene. It logs the exact hierarchy path and mesh names it found, and saves a scene checkpoint under Review/LocalBackups before removal. Trees outside the central street, houses, residents and the wolf are excluded.

The builder now destroys temporary authoring objects in a finally block, even when validation fails. Future authoring uses 32-bit indices for the separate Remake FBX to prevent 16-bit buffer splitting. The original FBX file and Amaterasu importer are unchanged. Installing this patch does not invoke the builder or reimport the art library.

If the tree has already been deleted, the automatic cleanup does nothing. Recovery menu: Sunward > Remove Misplaced Market Tree. A zero-match manual scan explicitly reports that removal is unconfirmed for any unrecognised object; it does not report a false repair.

## Verification

The C# numerical tests cover the exact split mesh names shown, root/clone names, a scene-origin tree, exclusion of background canopies, flat surfaces and whole-forest holders. C# syntax and existing regression tests pass. Unity itself is not installed here, so native scene execution is not claimed. The screenshot confirms the exact scene hierarchy this repair targets.

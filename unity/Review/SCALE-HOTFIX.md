# Scale repair follow-up — initial Animator enable

The previous update FAILED native validation on the user's Unity 6000.6.6f1 installation: WOLF_RIG became (100,100,100) immediately after Animator.Rebind/Update(0). Removing exposed curves from cloned imported clips was insufficient. The precise surviving internal binding/default cannot be inspected here without Unity; the failure is confirmed, not dismissed.

## Change

- Build fresh native AnimationClips instead of cloning imported clip payload.
- Transfer all non-container float curves, object-reference curves, events and clip settings. Compare non-container keys/wrapping before and after transfer and asset replacement; stop if any differ.
- Write explicit .34 visual-wrapper / 1 WOLF_RIG scale curves on every action, so startup/default evaluation and blends have defined authored values rather than relying on omitted channels. This is asset processing, not a runtime script resetting scale.
- Discover the actual WOLF_RIG binding path from the imported hierarchy and stop if ambiguous.
- Keep existing generated .anim GUIDs, the original FBX/importer, controller backup, geometry and wolf materials untouched. No unrelated artwork/gameplay changes in the hotfix.
- Keep startup validation strict. Add a pre-Rebind scale diagnostic. Do not bypass the failed assertion.

## Install the small hotfix

1. Stop Play and close Unity.
2. Extract Sunward-Unity-Scale-Hotfix.zip into your EXISTING project folder containing Assets and Packages. Replace WolfClipProcessor.cs; do not extract inside Assets.
3. Reopen Unity; wait for compilation.
4. Open Windflower, then choose **Sunward > Repair Amaterasu Animation Scale**. Merely running Validate uses the old generated clips; Repair regenerates them first and automatically validates.
5. If Repair passes, choose **Sunward > Apply Windflower Repair and Artwork Update** to finish any previous update stopped by the scale error, then test Play.
6. If it fails, copy the new first error and the preceding 'Scale diagnostic before Rebind' message. Do not change FBX scale, disable the Animator or manually shrink bones.

## Verification

C# syntax and existing 33 portable checks pass. ZIP content and download hashes checked before delivery. No Unity Editor is installed here: native API compilation, actual curve-transfer assertions and Animator startup/transition validation remain UNRUN. This is a corrected implementation to test locally, not a claim that the user-observed error has already passed.

Hotfix source: Assets/Editor/WolfClipProcessor.cs (and its existing metadata). No FBX, game script, shader, geometry, rig, texture or material is included in the small overlay. Complete project/combined update archives are also refreshed to include this processor.

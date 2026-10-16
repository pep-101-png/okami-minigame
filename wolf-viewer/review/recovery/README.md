# Wolf foundation investigation — no recovery applied

Comparison: https://pep-101-png.github.io/okami-minigame/recovery.html

The original upload, first coloured/rigged adaptation, early art rebuild, pre-narrowing checkpoint, approved neck checkpoint and current review can be selected independently. Cameras, scale, light and animation phase match. Rest pose compares the actual saved geometry; saved clips are optional. The original has no animation. `Hide back faces` is a rendering diagnostic, not a mesh edit.

## Main finding

**The early art rebuild used the original black outline shell as its skin and discarded the original painted head/body surfaces.** This is a more fundamental loss than the latest facial sculpt.

The untouched source has an inward-facing, black `Object_2` outline hull and separate outward-facing painted pieces, including the head (`Object_10`). Its double-sided import setting lets the black hull obscure those pieces. Front-face culling reveals the original without changing geometry or texture files. The first adaptation retained the original pieces, but its new floating eyes/markings changed the expression. In `56cf9e9`, `wolf-art-rebuild/build.py` explicitly keeps only `Object_2` and deletes the other original meshes, then closes the jaw and rebuilds fur.

Later departures are traceable:

- `8b4937b`: subdivision, voxel remeshing and relaxation softened the inherited surface and lip detail.
- `241db88` then `1305e78`/`2ba1f2b`: lengthened the face, narrowed skull/muzzle, lifted/slimmed the lower lip, enlarged/pointed the ears and repeatedly relaxed the mouth. These altered the skull-to-muzzle and jaw relationship.
- Repainted eye positions/shapes and the subsequent `4bf4d00`/`0d49c35` facial sculpts changed the brow, cheek, eye-to-nose balance and chin further. Those later repairs did not restore the discarded original head surface.

## Recommendation

Use the **original painted head** as the visual foundation for a **local head recovery on the current character**. Preserve the approved neck, torso, legs, curls, tail, rig and animation clips. Keep the repaired cheek closed; align/bake the original facial paint onto the recovered facial area rather than keeping the misplaced eye design.

The pre-narrowing native checkpoint matches the current vertex layout, so selectively undoing the later taper is reversible and can preserve weights/UV layout. However, it is already hull-derived and contains the earlier jaw opening: a wholesale rollback is not the answer. Matching the real original facial surface will require local shape correspondence, facial paint alignment and mouth/deformation checks. Transferring the current rig onto the complete original painted skin is also feasible, but changes the body, neck and fur attachment surfaces and needs broader deformation validation. Start with the head-only recovery before considering that larger option.

**Choose the preferred appearance in the comparison before any recovery starts. Current wolf geometry, textures, rig and animations remain byte-identical. No game files were changed or tested.**

The recovered upload is “Amaterasu the Japanese Fox God” by theamazingdonovan207 (CC BY 4.0), from the user's ZIP. The earlier Amaterasu-and-Issun link is not an available model in this checkout/history. Original source files and licence are copied unchanged for browser inspection; historical GLBs are exact Git blobs. See `provenance.json` for origins and hashes.

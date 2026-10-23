# Inspection of the uploaded st0.zip

**Yes: it contains architectural textures and recognisable Japanese building geometry.** This was checked from the actual uploaded bytes, not inferred solely from the filename.

- ZIP: 60 files, approximately 14.6 MB expanded: 48 BIN and 12 DAT files.
- The contents were Blowfish-encrypted game packages. I decoded all 60 locally and verified encryption/decryption round trips against their original bytes.
- Nested packages include 57 SCR model entries. I decoded vertex/triangle data from these and found 38 distinct raw geometry packages; repeated entries/localisation files account for duplicates.
- I extracted and visually inspected 94 distinct DDS textures. These include wood planks, plaster, black timber frames, shoji/doors/windows, red and blue roof tiles, signs, stone walls, grass, cliffs and tree foliage.
- Raw geometry previews visibly include a gabled building/frontage, curved-roof shrine structures, a pagoda, torii, fences, platforms, trees and developer/test structures. Useful candidates are `st0/r006.dat/5.SCP/13.SCR` (building frontage), `.../10.SCR` (curved-roof structure), `.../3.SCR` (pagoda) and `.../14.SCR` (torii). These are package paths, not ready-to-use Unity model filenames.
- The previews show decoded raw geometry. Per-instance transforms, texture associations, UV scaling, normals and complete material/culling behaviour are **not yet reconstructed or validated**. They should not be treated as finished Unity-ready houses.

Nothing from the archive was copied into the Unity game, the update ZIP or the public repository. The decoded models/textures and diagnostic contact sheets remain local inspection files. The original archive was not modified and no included executable or document instruction was run.

A later conversion task can reconstruct the building candidates with their matching textures and check scale, collision, outlines and scene placement before integrating them. This inspection does not claim that Sunward's houses have been replaced with these files.

Format references used for the read-only inspection:
- [Nippon archive format implementation](https://github.com/allogic/Nippon/blob/main/Common/Archive/Archive.cpp)
- [okami-utils model format](https://github.com/whataboutclyde/okami-utils/blob/master/include/okami-utils/model.h)
- [okami-utils mesh division format](https://github.com/whataboutclyde/okami-utils/blob/master/include/okami-utils/mesh_division.h)

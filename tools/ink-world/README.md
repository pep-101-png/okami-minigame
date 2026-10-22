# Windflower ink-world art pass

Actual saved game assets and scene changes, based on the user's supplied Ōkami
image: irregular black contours, ochre cliff planes, olive ground, dark teal
currents, vermilion bridges, angular branches and detailed Japanese roofs.
No external asset packs, paid services or alternate viewer/game are required.

## What opens in Unity

`Assets/Sunward/Scenes/Windflower.unity` directly contains the changes. There is
no editor migration or generator the player must run:

- All 21 established tree locations gain asymmetrical branching pine, broad
  cherry or sparse olive silhouettes, bark ridges/knots and shaped foliage.
- All 14 village houses retain their footprints and completed geometry, with
  curved entrance fascia, carved eave brackets and ceramic/gold roof crests.
  Burnt-orange and indigo roofs share painted wood/plaster/stone detail.
- Two houses have new high curved gables with separate timber/plaster infill and
  individual tile courses. The hall has a supported tiered belfry, louvres and
  curled ridge terminals; these give key buildings different silhouettes.
- Both existing solid bridge decks retain their geometry and collision; the
  superseded side rails are hidden and new curved red rails/caps/medallions added.
- A Blender-authored segmented waterwheel, paddles and curved spokes improve the
  **existing working rice mill**. Its two new mesh parts attach to the established
  axle; original shafts, gears, millstones, spray, shelter, supports and motion
  code are retained. Old wheel renderers remain serialized but hidden. There is
  no second mill or replacement movement script. Timber grain/normal relief is
  anchored to the rotating object. No audio or collision is added.
- Layered ochre cliff sections with moss fill the existing world boundary, with
  open river ends. Old simple mountain/boundary visuals remain serialized but
  hidden. Existing physical boundaries are unchanged.
- Five existing stone lantern locations gain open chambers, sculpted bases and
  curved caps. Prayer ornaments reinforce existing garden compositions.
- Painted environment materials, root-anchored leaf movement, inked light planes,
  restrained calligraphic currents and layered sky painting support the geometry.
- Explicit closed-solid ink shells use a separate URP renderer each; this does
  not assume URP will render a second forward pass on one material. No wolf or
  home-interior outline shell is added. Surface brushwork handles foliage detail.

The wolf model, imported materials/textures, rig, 47 clips, locomotion, combat,
quests, home interior, progression, installed tasks and Git syncing are retained.
The editor artwork audit now recognizes the seven new painting families without
weakening its existing live-reference, river, home, weapon or clip checks.

## Delivery and PC use

Deliver this change through a PR into `sunward-minigame`, then merge it under the
user's standing authorization. The existing PC sync can fetch that merged source.
Do not enable, reinstall, stop or otherwise alter the user's Windows tasks.
The user can open their normal Unity project and play; no PowerShell commands,
manual file transfer or 14-video run are required of them.

The small original PNG paintings in `Textures/Art`, `VillageFinish` and `InkWorld`
are explicitly ordinary Git binaries (each below 2 MiB). This corrects the prior
"should have been pointers" warnings without changing pixels or rewriting history.
The full `Idle_Natural.anim` and large model/audio/source assets continue using LFS.

## Available verification and limits

`check_world.py` validates **saved** native mesh channels/buffers, finite unit
normals, indices, bounds, ink expansion margins under actual parent scales,
asset/local references, original component preservation, texture imports and Git
attributes. Original 10,906 scene objects, 204 physics components and all existing
gameplay component fields are retained. `scene-report.json` records the actual
new renderer/placement counts. Library triangle counts are not runtime frame-time
measurements: instancing and simultaneous visibility affect rendering cost.

The latest available Unity feedback is still from source
`aefd595771e933a3313ecb4170251764c94ab1e3`, run
`20261021T092745607Z-9936e8`. All 12 screenshots and all 14 clip statuses/MP4 contact
sequences were inspected. The clips encode successfully but have incomplete
action coverage and largely idle motion; they do not validate later game changes.
The input-routing improvement from PR13 is retained and still needs fresh footage.

The texture sheets, tree meshes, bridge/wheel assets and scene-layout pictures
were rendered/inspected in Blender. `previews/` is permanently labelled **not
Unity**. The layout reader uses actual scene geometry/material assignments; its
shader, lighting, transparency and outline approximation is not a Unity render.

**Still unverified:** Unity 6000.6.6f1 import and shader compilation; the finished
Unity image versus the reference; camera-motion outline stability; water ordering;
GPU frame time on the user's PC; and whether their installed sync has received the
merged commit. No claim is made that the reference's finished quality has been
achieved or that PC testing has succeeded. No cloud Unity editor/PC control is
available. Fetch new published feedback automatically when it becomes available.

## Offline authoring and developer checks

These commands are for maintainers, not installation steps for the user:

```text
python tools/ink-world/paint.py
python tools/ink-world/geometry.py
python tools/ink-world/roof_variations.py
blender -b -t 4 -P tools/ink-world/blender_landmarks.py
python tools/ink-world/apply.py
python tools/ink-world/check_world.py
python tools/village/check_village.py
python tools/ink-world/check_shaders.py
blender -b -t 4 -P tools/ink-world/preview_scene.py
```

`apply.py` authors from the fixed reviewed PR13 scene (`ce07e12`), preserving its
objects and gameplay. It is an offline authoring tool, **not** a general scene
migration: never run it over later user scene edits without adapting the baseline.
Blender source for the landmarks is reproducible from the included script; binary
working `.blend`/NPZ/render logs remain outside the repository. Meshes/materials,
compact JPEG evidence, paintings and their import metadata are committed.

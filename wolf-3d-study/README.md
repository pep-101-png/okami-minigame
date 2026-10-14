# Inkbound wolf — static 3D study

A separate, unrigged 3D interpretation of the approved painted Inkbound wolf. This does not modify Sunward or Inkbound and is not integrated into either game.

- `wolf-three-quarter.png`: actual Blender render of the mesh.
- `wolf-profile.png`: second viewing angle.
- `wolf-static.blend`: editable native model.
- `wolf-static.glb`: exported mesh for future Three.js work.
- `wolf-preview-scene.blend`: presentation scene, camera and lighting.
- `build.py`: reproducible geometry and render builder (Blender 4.3).

The wolf, fur ornaments, painted surface ribbons, divine disc and flames are dimensional geometry. The render uses ink contours and procedural ivory shading; reproducing that presentation in Three.js will require matching rendering materials. This is a static visual review, with no animation or town work.

Rebuild from the repository root:

```sh
blender -b -t 6 --python wolf-3d-study/build.py
```

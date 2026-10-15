"""Refine the real skinned mesh and all run correctives, before repainting.

The original sculpt has large n-gons and uneven triangulation. Catmull-Clark
works on that original topology, rather than subdividing the exported triangles.
UVs, skin weights and every corrective move through the same surface operator.
"""
from pathlib import Path
import bpy
import numpy as np

root = Path(__file__).resolve().parents[1]
drafts = root / 'review/drafts'
bpy.ops.wm.open_mainfile(filepath=str(drafts / 'run-candidate.blend'))
coat = bpy.data.objects['Wolf ivory coat']
rig = bpy.data.objects['DivineWolfRig']
if coat.get('surface_polished'):
    raise RuntimeError('Already refined: rebuild the coarse candidate before rerunning.')
archive = np.load(drafts / 'surface.npz')
rest, delta = archive['rest'], archive['delta']
assert len(coat.data.vertices) == len(rest)
bpy.ops.wm.save_as_mainfile(filepath=str(drafts / 'surface-before-polish.blend'))
np.savez_compressed(drafts / 'surface-before-polish.npz', **{k: archive[k] for k in archive.files})

rig.animation_data.action = None
for bone in rig.pose.bones:
    bone.location = (0, 0, 0)
    bone.rotation_euler = (0, 0, 0)
for modifier in coat.modifiers:
    modifier.show_viewport = modifier.show_render = False
sub = coat.modifiers.new('Curved sculpt surface', 'SUBSURF')
sub.subdivision_type = 'CATMULL_CLARK'
sub.levels = sub.render_levels = 1
sub.uv_smooth = 'PRESERVE_BOUNDARIES'
bpy.context.view_layer.update()

def refined_coordinates(coords):
    coat.data.vertices.foreach_set('co', np.asarray(coords, dtype=np.float32).ravel())
    coat.data.update()
    bpy.context.view_layer.update()
    evaluated = coat.evaluated_get(bpy.context.evaluated_depsgraph_get())
    mesh = evaluated.to_mesh()
    result = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get('co', result)
    evaluated.to_mesh_clear()
    return result.reshape(-1, 3)

smooth_rest = refined_coordinates(rest)
smooth_delta = []
for i, change in enumerate(delta):
    smooth_delta.append(refined_coordinates(rest + change) - smooth_rest)
    if i % 12 == 0:
        print('REFINED_CORRECTIVES', i, flush=True)
refined_coordinates(rest)
bpy.ops.object.select_all(action='DESELECT')
coat.select_set(True)
bpy.context.view_layer.objects.active = coat
bpy.ops.object.modifier_apply(modifier=sub.name)
assert len(coat.data.vertices) == len(smooth_rest)
if coat.data.has_custom_normals:
    bpy.ops.mesh.customdata_custom_splitnormals_clear()
for edge in coat.data.edges:
    edge.use_edge_sharp = False
for face in coat.data.polygons:
    face.use_smooth = True
for modifier in coat.modifiers:
    modifier.show_viewport = modifier.show_render = True
coat['surface_polished'] = True
coat['coarse_vertices'] = len(rest)
rig.animation_data.action = bpy.data.actions['Idle']
bpy.context.scene.frame_set(1)
np.savez_compressed(drafts / 'surface.npz', rest=smooth_rest, delta=np.asarray(smooth_delta))
bpy.ops.wm.save_as_mainfile(filepath=str(drafts / 'run-candidate.blend'))
print('SURFACE_POLISHED', len(rest), len(smooth_rest), len(coat.data.polygons), flush=True)

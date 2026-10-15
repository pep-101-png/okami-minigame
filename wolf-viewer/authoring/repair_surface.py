"""Close inherited boolean gaps with a fine continuous sculpt surface.

Transfer rig weights and the companion corrective shapes from the nearest
source triangles. The character's proportions, rig and clips remain intact.
"""
from pathlib import Path
import bpy, bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform

root=Path(__file__).resolve().parents[1];drafts=root/'review/drafts'
bpy.ops.wm.open_mainfile(filepath=str(drafts/'run-candidate.blend'))
coat=bpy.data.objects['Wolf ivory coat'];rig=bpy.data.objects['DivineWolfRig']
if coat.get('surface_repaired'):raise RuntimeError('Surface already repaired; start from the coarse rebuild.')
archive=np.load(drafts/'surface.npz');old_rest=archive['rest'];old_delta=archive['delta']
bpy.ops.wm.save_as_mainfile(filepath=str(drafts/'surface-before-repair.blend'))
np.savez_compressed(drafts/'surface-before-repair.npz',rest=old_rest,delta=old_delta)
coat.data.calc_loop_triangles();tri=np.array([t.vertices[:] for t in coat.data.loop_triangles])
tree=BVHTree.FromPolygons([Vector(p) for p in old_rest],tri.tolist(),all_triangles=True)
names=[group.name for group in coat.vertex_groups]
old_weights=np.zeros((len(old_rest),len(names)),dtype=np.float32)
for vertex in coat.data.vertices:
    for group in vertex.groups:old_weights[vertex.index,group.group]=group.weight
original=bmesh.new();original.from_mesh(coat.data)
prior_boundary=sum(edge.is_boundary for edge in original.edges)
original.free()
coat.modifiers.clear()
bpy.ops.object.select_all(action='DESELECT');coat.select_set(True);bpy.context.view_layer.objects.active=coat
remesh=coat.modifiers.new('Continuous sealed fur surface','REMESH');remesh.mode='VOXEL';remesh.voxel_size=.045;remesh.use_smooth_shade=True
bpy.ops.object.modifier_apply(modifier=remesh.name)
print('REMESH_VERTICES',len(coat.data.vertices),flush=True)
assert 10000<len(coat.data.vertices)<70000,'Unexpected remesh density'
smooth=coat.modifiers.new('Relax voxel stair steps','SMOOTH');smooth.factor=.7;smooth.iterations=4
bpy.ops.object.modifier_apply(modifier=smooth.name)
rest=np.array([v.co[:] for v in coat.data.vertices],dtype=np.float32)
lookup=np.empty((len(rest),3),dtype=np.int32);bary=np.empty((len(rest),3),dtype=np.float32)
for i,point in enumerate(rest):
    hit,normal,face,distance=tree.find_nearest(Vector(point));indices=tri[face]
    weights=barycentric_transform(hit,*[Vector(old_rest[v]) for v in indices],Vector((1,0,0)),Vector((0,1,0)),Vector((0,0,1)))
    weights=np.maximum(np.array(weights),0);weights/=max(weights.sum(),1e-10)
    lookup[i]=indices;bary[i]=weights
weights=np.einsum('nv,nvb->nb',bary,old_weights[lookup])
for group in coat.vertex_groups:group.remove(list(range(len(rest))))
for i,row in enumerate(weights):
    top=np.argsort(row)[-4:];total=row[top].sum()
    assert total>0
    for group in top:
        if row[group]>1e-8:coat.vertex_groups[int(group)].add([i],float(row[group]/total),'REPLACE')
delta=np.einsum('nv,knvj->knj',bary,old_delta[:,lookup])
skin=coat.modifiers.new('Wolf skeleton','ARMATURE');skin.object=rig
for face in coat.data.polygons:face.use_smooth=True
mesh=bmesh.new();mesh.from_mesh(coat.data)
boundary=sum(edge.is_boundary for edge in mesh.edges);nonmanifold=sum(not edge.is_manifold for edge in mesh.edges)
mesh.free();assert boundary==0 and nonmanifold==0,(boundary,nonmanifold)
coat['surface_repaired']=True;coat['repaired_boundary_edges']=prior_boundary
np.savez_compressed(drafts/'surface.npz',rest=rest,delta=delta)
rig.animation_data.action=bpy.data.actions['Idle'];bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(drafts/'run-candidate.blend'))
print('SEALED_SURFACE',len(rest),'BOUNDARIES',boundary,'NONMANIFOLD',nonmanifold,flush=True)

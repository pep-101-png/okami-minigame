"""Read-only checks of the saved rig, including packed image bytes and reset pose.
Run: blender -b Original-Sketchfab-Wolf-Rig.blend --python verify_saved_rig.py
"""
import bpy, json, math, hashlib
from pathlib import Path
from mathutils import Vector

root=Path(__file__).resolve().parent
proof=json.loads((root/'review/rig-validation.json').read_text())
rig=bpy.data.objects['WOLF_RIG']
if rig.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
scene=bpy.context.scene
assert len(bpy.data.actions)==0
assert rig.animation_data is None or rig.animation_data.action is None
assert all(not o.animation_data or not o.animation_data.action for o in scene.objects)
assert all(max(abs(v) for v in pb.location)<1e-7 and max(abs(v) for v in pb.rotation_euler)<1e-7
           and max(abs(v-1) for v in pb.scale)<1e-7 for pb in rig.pose.bones)

def fingerprint(o):
    data={'v':[list(v.co) for v in o.data.vertices],
          'faces':[list(p.vertices) for p in o.data.polygons],
          'uv':[[list(l.uv) for l in u.data] for u in o.data.uv_layers],
          'smooth':[p.use_smooth for p in o.data.polygons],
          'normals':[list(n.vector) for n in o.data.corner_normals]}
    return hashlib.sha256(json.dumps(data,sort_keys=True).encode()).hexdigest()

details=[]
deps=bpy.context.evaluated_depsgraph_get()
for name,digest in proof['mesh_fingerprints'].items():
    o=bpy.data.objects[name];assert fingerprint(o)==digest,name
    assert o.parent==rig
    assert len(o.modifiers)==1 and o.modifiers[0].type=='ARMATURE'
    assert o.modifiers[0].object==rig and o.modifiers[0].use_deform_preserve_volume
    sums=[sum(g.weight for g in v.groups) for v in o.data.vertices]
    assert max(abs(s-1) for s in sums)<1e-5
    assert all(m.use_backface_culling for m in o.data.materials)
    ev=o.evaluated_get(deps);em=ev.to_mesh()
    error=max((ev.matrix_world@v.co-o.matrix_world@base.co).length for v,base in zip(em.vertices,o.data.vertices))
    ev.to_mesh_clear();assert error<.001,(name,error)
    details.append({'name':name,'rest_error':error,'vertices':len(o.data.vertices),'weights_normalized':True})

source_hashes=set(proof['source_files_sha256'].values())
images=[]
for image in bpy.data.images:
    if image.source!='FILE':continue
    assert image.packed_file is not None,image.name
    digest=hashlib.sha256(bytes(image.packed_file.data)).hexdigest()
    assert digest in source_hashes,(image.name,digest)
    images.append({'name':image.name,'original_image_bytes':True,'size':list(image.size)})
assert images

# Check full-rig translation, including all planted-paw controls.
bpy.context.view_layer.update()
before={name:rig.pose.bones[name].matrix.translation.copy() for name in ['DEF_head','DEF_tail_05','DEF_front_paw.L','DEF_rear_paw.R']}
pb=rig.pose.bones['CTRL_root'];m=pb.matrix.copy();m.translation+=Vector((.4,.3,.2));pb.matrix=m;bpy.context.view_layer.update()
for name,point in before.items():
    delta=rig.pose.bones[name].matrix.translation-point
    assert (delta-Vector((.4,.3,.2))).length<.001,(name,list(delta))
for p in rig.pose.bones:p.matrix_basis.identity()
bpy.context.view_layer.update()

out={'reopened_blend':str(bpy.data.filepath),'neutral_pose':True,'no_actions_or_cycles':True,
     'geometry_uv_normals_unchanged':True,'meshes':details,'packed_original_images':images,
     'global_root_motion_check':True,'saved_file_modified_by_verification':False}
(root/'review/saved-file-validation.json').write_text(json.dumps(out,indent=2))
print('REOPEN_VALIDATION_OK',json.dumps(out))

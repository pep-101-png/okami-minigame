"""Reopen verification and an isolated glTF export smoke check (no game usage)."""
import bpy,json,math,hashlib,ast,struct,os
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parent;scene=bpy.context.scene;rig=bpy.data.objects['WOLF_RIG']
meshes=[o for o in scene.objects if o.type=='MESH' and o.parent==rig]
proof=json.loads((ROOT/'review/authoring-validation.json').read_text())
tree=ast.parse((ROOT/'animate.py').read_text())
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['geometry_hash','skeleton_hash','materials_hash','weight_hash']]
exec(compile(ast.Module(body=functions,type_ignores=[]),'fingerprints','exec'))
assert geometry_hash()==proof['preservation']['mesh_uv_normals']
assert skeleton_hash()==proof['preservation']['skeleton_rest']
assert weight_hash()==proof['preservation']['source_skin_weights']
assert materials_hash()==proof['preservation']['materials']
assert {i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest()for i in bpy.data.images if i.packed_file}==proof['preservation']['images']
assert set(a.name for a in bpy.data.actions)=={'IDLE','WALK','RUN'}
assert all(a.use_fake_user for a in bpy.data.actions)
assert len(meshes)==10
assert scene.frame_end==720 and scene.render.fps==60
for name,item in proof['actions'].items():
    a=bpy.data.actions[name];assert a.use_frame_range
    assert int(a.frame_end)==item['frames']+1
    assert all(any(m.type=='CYCLES' for m in fc.modifiers)for fc in a.fcurves)
    assert item['max_ik_error']<.001 and item['max_contact_error']<.0001

if rig.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
rig.animation_data.action=None
for p in rig.pose.bones:p.matrix_basis.identity()
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
surface={}
for o in meshes:
    raw=[o.matrix_world@v.co for v in o.data.vertices];o.data.calc_loop_triangles()
    bvh=BVHTree.FromPolygons(raw,[tuple(t.vertices)for t in o.data.loop_triangles],all_triangles=True)
    ev=o.evaluated_get(deps);me=ev.to_mesh()
    distance=max(bvh.find_nearest(ev.matrix_world@v.co)[3]for v in me.vertices)
    assert distance<.001,(o.name,distance)
    surface[o.name]={'original_vertices':len(o.data.vertices),'evaluated_vertices':len(me.vertices),'max_rest_surface_distance':distance}
    ev.to_mesh_clear()

def pose_sample(name,frame):
    rig.animation_data.action=bpy.data.actions[name];scene.frame_set(frame)
    return {n:[v for row in rig.pose.bones[n].matrix for v in row]for n in ['DEF_head','DEF_chest','DEF_tail_05','DEF_front_paw.L','DEF_rear_paw.R']}
loops={}
for name,item in proof['actions'].items():
    a=pose_sample(name,1);b=pose_sample(name,item['frames']+1);c=pose_sample(name,721)
    error=max(abs(x-y)for n in a for x,y in zip(a[n],b[n]))
    review_error=max(abs(x-y)for n in a for x,y in zip(a[n],c[n]))
    assert error<1e-5 and review_error<1e-4
    loops[name]={'one_cycle_matrix_error':error,'review_range_matrix_error':review_error}

out={'reopened_blend':bpy.data.filepath,'original_rig_checkpoint_sha256':hashlib.sha256((ROOT.parent/'original-wolf-rig/Original-Sketchfab-Wolf-Rig.blend').read_bytes()).hexdigest(),
     'base_mesh_uv_normals_weights_materials_images_preserved':True,'original_skeleton_and_controls_preserved':True,
     'neutral_surface_checks':surface,'loop_checks':loops,'actions':list(proof['actions']),'no_game_or_viewer_tested':True}
assert out['original_rig_checkpoint_sha256']==proof['source_sha256']
(ROOT/'review/reopened-validation.json').write_text(json.dumps(out,indent=2))
print('REOPEN_CHECKS_PASSED',flush=True)
if os.environ.get('SKIP_GLTF_SMOKE')=='1':raise SystemExit

# Bake the existing rig constraints using Blender's standard exporter. Export
# only to /tmp; do not load, modify or test any game or browser viewer.
# Apply the static non-smoothing resolution on this disposable export copy,
# avoiding repeated subdivision evaluation during hundreds of bone samples.
rig.animation_data.action=None
for p in rig.pose.bones:p.matrix_basis.identity()
bpy.context.view_layer.update()
for o in meshes:
    for mod in list(o.modifiers):
        if mod.type=='SUBSURF':
            bpy.context.view_layer.objects.active=o
            bpy.ops.object.modifier_apply(modifier=mod.name)
rig.animation_data.action=bpy.data.actions['WALK'];scene.frame_set(1)
for o in scene.objects:o.select_set(False)
for o in [rig]+meshes:o.select_set(True)
bpy.context.view_layer.objects.active=rig
params={'filepath':'/tmp/amaterasu-three-actions.glb','export_format':'GLB','use_selection':True,
        'export_animations':True,'export_animation_mode':'ACTIONS','export_frame_range':False,
        'export_force_sampling':True,'export_frame_step':1,'export_def_bones':True,'export_apply':False}
rna=bpy.ops.export_scene.gltf.get_rna_type().properties
assert all(k in rna for k in params),[k for k in params if k not in rna]
bpy.ops.export_scene.gltf(**params)
data=Path(params['filepath']).read_bytes();length,kind=struct.unpack_from('<II',data,12)
doc=json.loads(data[20:20+length]);animations=doc.get('animations',[])
assert set(a['name']for a in animations)=={'IDLE','WALK','RUN'},[a.get('name')for a in animations]
durations={}
for a in animations:
    times=[doc['accessors'][s['input']]for s in a['samplers']]
    duration=max(t['max'][0]for t in times)-min(t['min'][0]for t in times)
    assert abs(duration-proof['actions'][a['name']]['duration_seconds'])<.001,(a['name'],duration)
    assert len(a['channels'])>10
    durations[a['name']]=duration
assert doc.get('skins')
assert sum('skin'in n for n in doc.get('nodes',[]))==10
assert all('JOINTS_0'in p['attributes'] and 'WEIGHTS_0'in p['attributes']for m in doc['meshes']for p in m['primitives'])
out['isolated_game_export_smoke']={'clips':durations,'skinned_meshes':10,'applied_simple_bend_resolution':True,'standard_constraint_sampling':True,'file_in_tmp_only':True}
(ROOT/'review/reopened-validation.json').write_text(json.dumps(out,indent=2))
print('THREE_ACTION_GLTF_EXPORT_PASSED',json.dumps(durations),flush=True)

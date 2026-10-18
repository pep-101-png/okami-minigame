import bpy,json,struct,math
from pathlib import Path
R=Path(__file__).resolve().parents[2];raw=(R/'public/models/amaterasu-original.glb').read_bytes();n=struct.unpack_from('<I',raw,12)[0];glb=json.loads(raw[20:20+n]);source={a['name']:max(glb['accessors'][s['input']]['max'][0]for s in a['samplers'])-min(glb['accessors'][s['input']]['min'][0]for s in a['samplers'])for a in glb['animations']};bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=60;bpy.ops.import_scene.fbx(filepath=str(R/'unity/Assets/Sunward/Models/Amaterasu.fbx'));found={};errors=[]
for a in bpy.data.actions:
 name=a.name.split('|')[-1].replace('_WOLF_RIG','');found[name]=(a.frame_range[1]-a.frame_range[0])/60
for name,d in source.items():
 assert name in found,(name,'missing');error=abs(d-found[name]);assert error<.035,(name,d,found[name]);errors.append(error)
report={'source_actions':len(source),'fbx_actions':len(found),'max_duration_error_seconds':max(errors),'skinned_meshes':len([o for o in bpy.context.scene.objects if o.type=='MESH']),'nonfinite_vertices':sum(not all(math.isfinite(c)for c in v.co)for o in bpy.context.scene.objects if o.type=='MESH'for v in o.data.vertices),'note':'Blender reimport/animation-duration validation, not Unity visual or runtime approval.'};assert report['nonfinite_vertices']==0;
# Compare the underlying rest geometry in Blender world coordinates after both imports.
from mathutils.kdtree import KDTree
points=[o.matrix_world@v.co for o in bpy.context.scene.objects if o.type=='MESH'for v in o.data.vertices]
kd=KDTree(len(points))
for i,p in enumerate(points):kd.insert(p,i)
kd.balance()
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=60;bpy.ops.import_scene.gltf(filepath=str(R/'public/models/amaterasu-original.glb'))
maximum=0
for o in bpy.context.scene.objects:
 if o.type=='MESH':
  for v in o.data.vertices:maximum=max(maximum,kd.find(o.matrix_world@v.co)[2])
report['maximum_rest_surface_vertex_distance_blender_units']=maximum
assert maximum<.0001,maximum
(R/'unity/Review/fbx-validation.json').write_text(json.dumps(report,indent=2));print(report)

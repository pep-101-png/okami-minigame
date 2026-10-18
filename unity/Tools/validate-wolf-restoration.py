"""FBX preservation/pose checks; not Unity engine or visual approval."""
import bpy,json,math,hashlib,struct,io
from pathlib import Path
from PIL import Image
R=Path(__file__).resolve().parents[1];S=R.parent/'public/models/amaterasu-original.glb';source_hash=hashlib.sha256(S.read_bytes()).hexdigest()
# Read original GLB material flags and verify the exported maps at pixel level.
b=S.read_bytes();n=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+n]);base=28+n
texture_checks=[]
for image in g['images']:
 view=g['bufferViews'][image['bufferView']];start=base+view.get('byteOffset',0);original=Image.open(io.BytesIO(b[start:start+view['byteLength']])).convert('RGBA');export=Image.open(R/'Assets/Sunward/Textures'/('Wolf-'+image['name']+'.png')).convert('RGBA');assert original.size==export.size and original.tobytes()==export.tobytes();texture_checks.append({'name':image['name'],'dimensions':original.size,'pixels_unchanged':True})
source_flags={m['name']:m.get('doubleSided',False)for m in g['materials']};report=json.loads((R/'Review/wolf-export.json').read_text());assert all(m['doubleSided']==source_flags[m['name']]for m in report['materials'])
# Original rest mesh and UVs, plus sample source poses for non-sleep actions.
def read(kind,path):
 bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=60
 if kind=='glb':bpy.ops.import_scene.gltf(filepath=str(path))
 else:bpy.ops.import_scene.fbx(filepath=str(path))
 return next(o for o in bpy.context.scene.objects if o.type=='ARMATURE')
def clean(n):return n.split('|')[-1].replace('_WOLF_RIG','')
a=read('glb',S);meshes={o.name:([tuple(v.co)for v in o.data.vertices],[tuple(u.uv)for u in o.data.uv_layers.active.data]if o.data.uv_layers else [])for o in bpy.context.scene.objects if o.type=='MESH'}
poses={};durations={}
for action in bpy.data.actions:
 name=clean(action.name);a.animation_data.action=action;lo,hi=action.frame_range;durations[name]=(hi-lo)/60
 if name.startswith('Sleep'):continue
 for phase in [0,.25,.5,.75,1]:
  bpy.context.scene.frame_set(round(lo+(hi-lo)*phase));bpy.context.view_layer.update();poses[(name,phase)]={p.name:tuple(v for row in p.matrix for v in row)for p in a.pose.bones}
a=read('fbx',R/'Assets/Sunward/Models/Amaterasu.fbx');actions={clean(x.name):x for x in bpy.data.actions};assert set(durations)<=set(actions);worst=0;finite_samples=0
for name,duration in durations.items():assert abs((actions[name].frame_range[1]-actions[name].frame_range[0])/60-duration)<.035
for (name,phase),original in poses.items():
 action=actions[name];a.animation_data.action=action;lo,hi=action.frame_range;bpy.context.scene.frame_set(round(lo+(hi-lo)*phase));bpy.context.view_layer.update()
 for bone,values in original.items():
  if bone not in a.pose.bones:continue
  actual=tuple(v for row in a.pose.bones[bone].matrix for v in row);worst=max(worst,max(abs(x-y)for x,y in zip(values,actual)))
assert worst<.002,('Unrelated action deformation changed',worst)
# Reimport can split vertices/loops, so compare rest position+UV pairs as sets.
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 old_positions,old_uvs=meshes[o.name];assert len(old_positions)==len(o.data.vertices)
 assert max(abs(x-y)for old,v in zip(old_positions,o.data.vertices)for x,y in zip(old,v.co))<.0001
 assert len(old_uvs)==len(o.data.uv_layers.active.data)
 assert max(abs(x-y)for old,u in zip(old_uvs,o.data.uv_layers.active.data)for x,y in zip(old,u.uv))<.0001
for name in ['Sleep_Down','Sleep_Loop','Sleep_Up']:
 action=actions[name];a.animation_data.action=action
 for frame in range(round(action.frame_range[0]),round(action.frame_range[1])+1):
  bpy.context.scene.frame_set(frame);bpy.context.view_layer.update()
  for p in a.pose.bones:
   assert all(math.isfinite(v)for row in p.matrix for v in row)
  finite_samples+=1
assert hashlib.sha256(S.read_bytes()).hexdigest()==source_hash
result={'original_texture_pixels':texture_checks,'original_material_culling_preserved':True,'all_44_source_actions_retained':True,'three_legacy_sleep_actions_retained':all(n+'_Legacy'in actions for n in ['Sleep_Down','Sleep_Loop','Sleep_Up']),'rest_mesh_and_uvs_unchanged':True,'maximum_non_sleep_pose_matrix_difference':worst,'finite_sleep_frames_checked':finite_samples,'source_glb_unchanged':True,'unity_editor_compilation':'NOT RUN','unity_playmode':'NOT RUN','note':'Blender imports and numeric pose comparisons, not Unity runtime or final visual approval.'}
(R/'Review/wolf-restoration-validation.json').write_text(json.dumps(result,indent=2));print('WOLF_RESTORATION_VALIDATION',json.dumps(result),flush=True)

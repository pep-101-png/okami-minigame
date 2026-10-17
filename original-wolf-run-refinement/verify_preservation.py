import bpy,ast,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
ns={n.name:n for n in ast.parse((ROOT/'refine_run.py').read_text()).body if isinstance(n,ast.FunctionDef)}
exec(compile(ast.Module(body=[ns['action_hash']],type_ignores=[]),'<fingerprint>','exec'))
from mathutils import Vector
fnames=['geometry_hash','skeleton_hash','materials_hash','weight_hash']
for n in ast.parse((ROOT.parent/'original-wolf-animation/animate.py').read_text()).body:
 if isinstance(n,ast.FunctionDef)and n.name in fnames:exec(compile(ast.Module(body=[n],type_ignores=[]),'<fingerprints>','exec'))
def inspect(path):
 global rig,meshes
 bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['WOLF_RIG'];s=bpy.context.scene
 if rig.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
 meshes=[o for o in s.objects if o.type=='MESH'and o.parent==rig]
 output={'mesh':geometry_hash(),'rig':skeleton_hash(),'weights':weight_hash(),'materials':materials_hash(),'images':{i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest()for i in bpy.data.images if i.packed_file},'actions':{n:action_hash(bpy.data.actions[n])for n in ['IDLE','WALK','RUN']},'poses':{}}
 rig.animation_data.action=None
 for p in rig.pose.bones:p.matrix_basis.identity()
 bpy.context.view_layer.update()
 for o in meshes:
  for m in list(o.modifiers):
   if m.type=='SUBSURF':bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name)
 for name,frames in [('IDLE',[1,60,120,180,241]),('WALK',[1,15,28,44,60,73]),('RUN',[1,8,12,19,28,36,41])]:
  rig.animation_data.action=bpy.data.actions[name]
  for frame in frames:
   s.frame_set(frame);dep=bpy.context.evaluated_depsgraph_get();h=hashlib.sha256()
   for o in meshes:
    e=o.evaluated_get(dep);m=e.to_mesh()
    h.update(str([(tuple(v.co))for v in m.vertices]).encode());e.to_mesh_clear()
   output['poses'][name+str(frame)]=h.hexdigest()
 return output
old=inspect(ROOT.parent/'original-wolf-animation/Amaterasu-Idle-Walk-Run.blend');new=inspect(ROOT/'Amaterasu-Run-Refined.blend')
assert old==new,[(k,old[k],new[k])for k in old if old[k]!=new[k]]
print('SOURCE_APPEARANCE_RIG_WEIGHTS_ACTIONS_AND_18_POSES_EXACTLY_PRESERVED',flush=True)
(ROOT/'review/preservation.json').write_text(json.dumps({'source_and_refined_match':True,**new},indent=2))

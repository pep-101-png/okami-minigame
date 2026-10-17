import bpy,ast,hashlib,json,math
from pathlib import Path
R=Path(__file__).resolve().parent
for p,names in [(R.parent/'original-wolf-run-refinement/refine_run.py',['action_hash']),(R.parent/'original-wolf-animation/animate.py',['geometry_hash','skeleton_hash','weight_hash','materials_hash'])]:
 for n in ast.parse(p.read_text()).body:
  if isinstance(n,ast.FunctionDef)and n.name in names:exec(compile(ast.Module(body=[n],type_ignores=[]),'<fingerprint>','exec'))
def scan(path,extra=False):
 global rig,meshes
 bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['WOLF_RIG'];s=bpy.context.scene;meshes=[o for o in s.objects if o.type=='MESH'and o.parent==rig]
 # Ignore extra effects materials for the original-material signature.
 if extra:
  for o in list(bpy.data.collections['05 · Sprint wind — separate effect'].objects):bpy.data.objects.remove(o,do_unlink=True)
  for m in list(bpy.data.materials):
   if m.name.startswith('WIND ·'):bpy.data.materials.remove(m)
 out={'geometry':geometry_hash(),'rig':skeleton_hash(),'weights':weight_hash(),'materials':materials_hash(),'images':{i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest()for i in bpy.data.images if i.packed_file},'actions':{a.name:action_hash(a)for a in bpy.data.actions if a.name not in ['Sprint_Polished','Wind_Speed_Demo']}}
 poses={}
 for name in out['actions']:
  rig.animation_data.action=None
  for p in rig.pose.bones:p.matrix_basis.identity()
  rig.animation_data.action=bpy.data.actions[name]
  for f in [1,9,17,25,33]:
   s.frame_set(f);poses[(name,f)]=[v for p in rig.pose.bones for row in p.matrix for v in row]
 out['poses']=hashlib.sha256(str(poses).encode()).hexdigest()
 return out
old=scan(R.parent/'original-wolf-sprint/Amaterasu-Movement.blend');new=scan(R/'Amaterasu-Movement.blend',True)
assert old==new,[k for k in old if old[k]!=new[k]]
allowed=['CTRL_neck_base','CTRL_neck_upper','CTRL_head']+[f'CTRL_tail_{i:02}'for i in range(1,6)]
def sig(a):return [(f.data_path,f.array_index,[(tuple(k.co),tuple(k.handle_left),tuple(k.handle_right))for k in f.keyframe_points])for f in a.fcurves if not any('"'+n+'"'in f.data_path for n in allowed)]
assert sig(bpy.data.actions['Sprint'])==sig(bpy.data.actions['Sprint_Polished'])
s=bpy.context.scene
core=[p.name for p in rig.pose.bones if p.name.startswith('DEF_')and not any(n in p.name for n in ['neck','head','jaw','ear','tail'])];base={}
for action in ['Sprint','Sprint_Polished']:
 rig.animation_data.action=bpy.data.actions[action]
 for j in range(129):
  f=1+j/4;s.frame_set(int(f),subframe=f%1);row=[v for name in core for line in rig.pose.bones[name].matrix for v in line]
  if action=='Sprint':base[j]=row
  else:assert max(abs(x-y)for x,y in zip(row,base[j]))<1e-6,(j,max(abs(x-y)for x,y in zip(row,base[j])))
first={p.name:p.matrix.copy()for p in rig.pose.bones};s.frame_set(1);loop=max(abs(first[p.name][i][j]-p.matrix[i][j])for p in rig.pose.bones for i in range(4)for j in range(4));assert loop<1e-5,loop
bpy.ops.wm.open_mainfile(filepath=str(R/'Amaterasu-Movement.blend'));rig=bpy.data.objects['WOLF_RIG'];s=bpy.context.scene;wind=bpy.data.objects['Wind ribbon 01'];ctrl=bpy.data.objects['SPRINT_WIND · speed control'];gates={}
for name in ['Idle','Walk','Jog','Sprint','Sprint_Polished']:
 rig.animation_data.action=bpy.data.actions[name];s.frame_set(4);bpy.context.view_layer.update();gates[name]=list(wind.evaluated_get(bpy.context.evaluated_depsgraph_get()).scale)
 print('GATE',name,gates[name],flush=True)
 assert(gates[name][0]>.99 if name=='Sprint_Polished'else max(gates[name])<1e-6),(name,gates[name])
rig.animation_data.action=bpy.data.actions['Sprint_Polished'];speeds={}
for speed in [0,2,7,14.625]:
 ctrl['speed']=speed;ctrl.update_tag();s.frame_set(5);bpy.context.view_layer.update();speeds[speed]=list(wind.evaluated_get(bpy.context.evaluated_depsgraph_get()).scale)
assert speeds[0][0]==0 and speeds[2][0]<speeds[7][0]<speeds[14.625][0]
invalid=[o.name for o in bpy.data.objects if o.animation_data for fc in o.animation_data.drivers if not fc.driver.is_valid];assert not invalid,invalid
(R/'review/checks.json').write_text(json.dumps({'original_data_exact':old,'non_head_neck_tail_curves_identical':True,'core_and_leg_def_matrices_identical_samples':129,'loop_matrix_error':loop,'gates':gates,'speed_response':speeds,'invalid_drivers':invalid},indent=2));print('PRESERVATION_AND_GATING_PASS',flush=True)

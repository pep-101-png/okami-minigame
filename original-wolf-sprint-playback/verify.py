import bpy,ast,hashlib,json,math
from pathlib import Path
R=Path(__file__).resolve().parent
node=next(n for n in ast.parse((R.parent/'original-wolf-run-refinement/refine_run.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='action_hash');exec(compile(ast.Module(body=[node],type_ignores=[]),'<hash>','exec'))
def collect(path):
 bpy.ops.wm.open_mainfile(filepath=str(path));r=bpy.data.objects['WOLF_RIG'];s=bpy.context.scene;meshes=[o for o in s.objects if o.type=='MESH'and o.parent==r];out={'actions':{a.name:action_hash(a)for a in bpy.data.actions if a.name!='Sprint_Fluid'},'images':{i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest()for i in bpy.data.images if i.packed_file},'poses':{}}
 for name in ['Idle','Walk','Jog','Sprint','Sprint_Polished']:
  r.animation_data.action=None
  for p in r.pose.bones:p.matrix_basis.identity()
  r.animation_data.action=bpy.data.actions[name]
  for f in [1,9,17,25,33]:
   s.frame_set(f);dep=bpy.context.evaluated_depsgraph_get();data={}
   for o in meshes:
    e=o.evaluated_get(dep);me=e.to_mesh();data[o.name]={'points':[tuple(e.matrix_world@v.co)for v in me.vertices],'normals':[tuple(n.vector)for n in me.corner_normals]};e.to_mesh_clear()
   out['poses'][name+str(f)]=data
 return out
old=collect(R.parent/'original-wolf-sprint-wind/Amaterasu-Movement.blend');new=collect(R/'Amaterasu-Movement.blend');assert old['actions']==new['actions'];assert old['images']==new['images'];errors={'points':0,'normals':0}
for name,objects in old['poses'].items():
 for obj,data in objects.items():
  for field,rows in data.items():
   other=new['poses'][name][obj][field];assert len(rows)==len(other),(obj,field)
   for p,q in zip(rows,other):errors[field]=max(errors[field],*(abs(a-b)for a,b in zip(p,q)))
assert errors['points']<1e-6 and errors['normals']<1e-5,errors
r=bpy.data.objects['WOLF_RIG'];s=bpy.context.scene;allowed=['CTRL_neck_base','CTRL_neck_upper','CTRL_head'];base=bpy.data.actions['Sprint_Polished'];a=bpy.data.actions['Sprint_Fluid']
def sig(action):return[(fc.data_path,fc.array_index,[(tuple(k.co),tuple(k.handle_left),tuple(k.handle_right),k.interpolation)for k in fc.keyframe_points])for fc in action.fcurves if not any('"'+n+'"'in fc.data_path for n in allowed)]
assert sig(base)==sig(a)
names=[p.name for p in r.pose.bones if p.name.startswith('DEF_')and not any(x in p.name for x in ['head','neck','jaw','ear'])];poses={};motion={}
for action in [base,a]:
 r.animation_data.action=action;rows=[]
 for j in range(129):
  f=1+j/4;s.frame_set(int(f),subframe=f%1);row=[v for n in names for line in r.pose.bones[n].matrix for v in line]
  if action==base:poses[j]=row
  else:assert max(abs(x-y)for x,y in zip(row,poses[j]))<1e-6,j
  rows.append({n:[list(r.pose.bones[n].head),list(r.pose.bones[n].tail)]for n in ['DEF_chest','DEF_neck_base','DEF_neck_upper','DEF_head']})
 motion[action.name]=rows
first={p.name:p.matrix.copy()for p in r.pose.bones};s.frame_set(1);loop=max(abs(first[p.name][i][j]-p.matrix[i][j])for p in r.pose.bones for i in range(4)for j in range(4));assert loop<1e-5,loop
(R/'review/preservation.json').write_text(json.dumps({'old_actions_curves_exact':True,'packed_images_exact':True,'old_evaluated_poses':25,'maximum_surface_errors':errors,'non_neck_head_curves_exact':True,'unchanged_body_leg_tail_matrix_samples':129,'loop_error':loop,'neck_motion':motion},indent=2));print('SURFACE_APPEARANCE_AND_ANIMATION_PRESERVATION_PASS',errors,flush=True)

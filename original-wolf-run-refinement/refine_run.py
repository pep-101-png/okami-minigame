"""Separate Run revision. Existing mesh, rig, weights, materials and three Actions are preserved."""
import bpy,math,json,hashlib,ast
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/'original-wolf-animation/Amaterasu-Idle-Walk-Run.blend'
SOURCE_HASH='94963cbb425d8d9dcfe7b1bfff5086e3330122e93069c9a34dcdf794b0659300'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_HASH
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
scene=bpy.context.scene;rig=bpy.data.objects['WOLF_RIG']
if rig.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
CTRL=[p for p in rig.pose.bones if p.name.startswith('CTRL_')]
meshes=[o for o in scene.objects if o.type=='MESH'and o.parent==rig];TAU=math.tau
names=['geometry_hash','skeleton_hash','materials_hash','weight_hash','reset','smooth','hermite','curve','rotate','translate','set_paw','run_foot','sole_points']
module=ast.parse((ROOT.parent/'original-wolf-animation/animate.py').read_text())
for node in module.body:
 if isinstance(node,ast.FunctionDef)and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),'<original helpers>','exec'))
def action_hash(a):
 return hashlib.sha256(json.dumps([(f.data_path,f.array_index,[(list(k.co),list(k.handle_left),list(k.handle_right),k.interpolation,k.handle_left_type,k.handle_right_type)for k in f.keyframe_points],[(m.type,m.mode_before,m.mode_after)for m in f.modifiers])for f in a.fcurves],sort_keys=True).encode()).hexdigest()
keep={n:action_hash(bpy.data.actions[n])for n in ['IDLE','WALK','RUN']}
preserve={'mesh':geometry_hash(),'rig':skeleton_hash(),'weights':weight_hash(),'materials':materials_hash(),'images':{i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest()for i in bpy.data.images if i.packed_file}}
rig.animation_data.action=None;reset();rest_matrix={p.name:p.matrix.copy()for p in CTRL}
footmesh=bpy.data.objects['Object_11'];rest_points=[footmesh.matrix_world@v.co for v in footmesh.data.vertices];feet={}
for kind in ['front','rear']:
 for side,sign in [('L',1),('R',-1)]:
  key=kind+'.'+side;ids=[i for i,p in enumerate(rest_points)if p.z<.17 and sign*p.x>.25 and(p.y<-.9 if kind=='front'else p.y>1)]
  feet[key]={'ids':ids,'center':sum((rest_points[i]for i in ids),Vector())/len(ids),'control':'CTRL_paw_'+key,'sign':sign}
for o in meshes:
 for m in o.modifiers:
  if m.type=='SUBSURF':m.show_viewport=False
old_run_foot=run_foot
def refined_foot(t,key):
 s=old_run_foot(t,key);u=s['u'];d=s['duty']
 if key.startswith('rear')and u>=d:
  # Follow a rounded recovery arc below the hip, rather than driving the knee
  # above its socket. Contact trajectory/velocity are unchanged.
  s['height']=curve([(d,0),(.36,.18),(.53,.24),(.73,.22),(.90,.11),(1,0)],u,start_d=0,end_d=0,positive=True)
  s['pitch']=curve([(d,18),(.42,16),(.67,12),(.90,-7),(1,-5)],u)
  s['dy']=curve([(d,-.99+4.8*d),(.36,.53),(.53,.24),(.73,-.88),(.90,-1.10),(1,-.99)],u,start_d=4.8,end_d=4.8)
 return s

def pose(t):
 reset();collect=math.cos(TAU*(t-.43));drive=math.sin(TAU*(t-.43))
 # Distributed sagittal wave: pelvis tucks, lumbar region rounds, chest opens.
 # The pelvis and thorax do not simply pitch as one rigid board.
 translate('CTRL_body',(.018*math.sin(TAU*t),.045*math.sin(TAU*(t-.12)),-.07+.105*math.cos(2*TAU*(t-.43))-.28*math.exp(8*(math.cos(TAU*(t-.28))-1))-.045*math.exp(9*(math.cos(TAU*(t-.10))-1))))
 rotate('CTRL_body',x=3.8*math.sin(TAU*(t-.16)),y=.4*math.sin(TAU*t))
 rotate('CTRL_hips',x=-16*collect,z=.55*math.sin(TAU*t))
 rotate('CTRL_spine_mid',x=28*math.cos(TAU*(t-.47)))
 rotate('CTRL_chest',x=-16*math.cos(TAU*(t-.51)),z=-.6*math.sin(TAU*t))
 rotate('CTRL_neck_base',x=3.0+3.2*math.sin(TAU*(t-.19)))
 rotate('CTRL_neck_upper',x=-3.0-2.4*math.sin(TAU*(t-.27)))
 states={key:refined_foot(t,key)for key in feet}
 for side in ['L','R']:
  rotate('CTRL_shoulder.'+side,x=-9.0*math.cos(TAU*states['front.'+side]['u']))
  rotate('CTRL_hip_socket.'+side,x=-3.4*math.cos(TAU*states['rear.'+side]['u']))
  rotate('CTRL_ear.'+side,x=3.0+2.0*math.sin(2*TAU*t-1),z=.35*math.sin(TAU*t))
 for i,lift in enumerate([11,7,3,1,0]):
  rotate('CTRL_tail_%02d'%(i+1),x=lift+(2.0+i*.65)*math.sin(TAU*t-.5-i*.42),z=(.5+i*.15)*math.sin(TAU*t-.5-i*.38))
 bpy.context.view_layer.update()
 p=rig.pose.bones['CTRL_head'];m=p.matrix.copy()
 goal=Quaternion((1,0,0),math.radians(2.4*math.sin(TAU*(t-.28))))@rest_matrix[p.name].to_quaternion()
 q=m.to_quaternion().slerp(goal,.74);target=q.to_matrix().to_4x4();target.translation=m.translation;p.matrix=target
 for key,state in states.items():
  set_paw(key,state['dy'],state['height'],state['pitch']);rotate('CTRL_toes_'+key,x=state['toe'])
 bpy.context.view_layer.update()
 for _ in range(6):
  observed=sole_points()
  for key,state in states.items():
   f=feet[key];q=observed[key]
   translate(f['control'],(f['center'].x-q['center'].x,f['center'].y+state['dy']-q['center'].y,.035+state['height']-q['minZ']))
  bpy.context.view_layer.update()
 return states,sole_points()

a=bpy.data.actions['RUN'].copy();a.name='RUN_REFINED';a.use_fake_user=True
for fc in list(a.fcurves):a.fcurves.remove(fc)
a.asset_mark();a.asset_data.description='Refined gallop: rounded hind recovery, coordinated pelvis/lumbar/thorax motion, stabilised gaze and delayed tail.'
a['previous_run']='RUN';a['revision']=6;rig.animation_data.action=a
samples=[]
for frame in range(1,42):
 scene.frame_set(frame);states,obs=pose((frame-1)/40);row={'frame':frame,'feet':{},'legs':{}}
 for key,s in states.items():
  q=obs[key];row['feet'][key]={'contact':s['contact'],'height':q['minZ'],'center':list(q['center']),'idealY':feet[key]['center'].y+s['dy'],'error':max(abs(q['minZ']-.035-s['height']),abs(q['center'].y-feet[key]['center'].y-s['dy']))}
  low=rig.pose.bones['DEF_'+key.split('.')[0]+'_lower.'+key[-1]];upper=rig.pose.bones['DEF_'+key.split('.')[0]+'_upper.'+key[-1]]
  row['legs'][key]={'ik_error':(low.tail-rig.pose.bones['MCH_target_'+key].head).length,'bend':math.degrees((upper.tail-upper.head).angle(low.tail-low.head)),'hip':list(upper.head),'knee':list(upper.tail)}
 for p in CTRL:
  p.keyframe_insert('location',frame=frame,group=p.name);p.keyframe_insert('rotation_euler',frame=frame,group=p.name)
 samples.append(row)
for fc in a.fcurves:
 points=list(fc.keyframe_points);values=[k.co.y for k in points[:-1]]
 for i,k in enumerate(points):
  j=i%40;prev=values[(j-1)%40];value=values[j];nxt=values[(j+1)%40]
  slope=(nxt-prev)/2 if (value-prev)*(nxt-value)>0 else 0
  k.interpolation='BEZIER';k.handle_left_type='FREE';k.handle_right_type='FREE'
  k.handle_left=(k.co.x-1/3,k.co.y-slope/3);k.handle_right=(k.co.x+1/3,k.co.y+slope/3)
 fc.modifiers.new('CYCLES')
assert keep=={n:action_hash(bpy.data.actions[n])for n in keep}
assert preserve['mesh']==geometry_hash();assert preserve['rig']==skeleton_hash();assert preserve['weights']==weight_hash();assert preserve['materials']==materials_hash()
for o in meshes:
 for m in o.modifiers:
  if m.type=='SUBSURF':m.show_viewport=True
scene.frame_set(1);scene.frame_start=1;scene.frame_end=720
for o in scene.objects:o.select_set(False)
rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='POSE')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Amaterasu-Run-Refined.blend'))
report={'input_sha256':SOURCE_HASH,'preserved':preserve,'unchanged_actions':keep,'new_action':'RUN_REFINED','cycle_frames':40,'samples':samples,'revision':6}
(ROOT/'review/authoring.json').write_text(json.dumps(report,indent=2))
print('REFINED_RUN_SAVED',max(v['ik_error']for s in samples for v in s['legs'].values()),flush=True)

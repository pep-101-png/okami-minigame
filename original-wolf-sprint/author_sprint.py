"""Distinct high-speed gallop on the unchanged approved original-wolf rig."""
import bpy,math,json,hashlib,ast
from pathlib import Path
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT.parent/'original-wolf-run-refinement/Amaterasu-Run-Refined.blend'
SOURCE_HASH='53dccddf955eeb6829ac3c6334a5bf1431fbfca6cf26af89b5887d82fe718dee'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()==SOURCE_HASH
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;rig=bpy.data.objects['WOLF_RIG']
if rig.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
CTRL=[p for p in rig.pose.bones if p.name.startswith('CTRL_')];meshes=[o for o in scene.objects if o.type=='MESH'and o.parent==rig];TAU=math.tau
for n in ast.parse((ROOT.parent/'original-wolf-animation/animate.py').read_text()).body:
 if isinstance(n,ast.FunctionDef)and n.name in ['geometry_hash','skeleton_hash','materials_hash','weight_hash','reset','smooth','hermite','curve','rotate','translate','set_paw','sole_points']:exec(compile(ast.Module(body=[n],type_ignores=[]),'<existing rig helpers>','exec'))
for n in ast.parse((ROOT.parent/'original-wolf-run-refinement/refine_run.py').read_text()).body:
 if isinstance(n,ast.FunctionDef)and n.name=='action_hash':exec(compile(ast.Module(body=[n],type_ignores=[]),'<curve fingerprint>','exec'))
mapping={'IDLE':'Idle','WALK':'Walk','RUN_REFINED':'Jog','RUN':'Legacy_Run'}
keep={new:action_hash(bpy.data.actions[old])for old,new in mapping.items()}
preserve={'mesh':geometry_hash(),'rig':skeleton_hash(),'weights':weight_hash(),'materials':materials_hash(),'images':{i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest()for i in bpy.data.images if i.packed_file}}
for old,new in mapping.items():bpy.data.actions[old].name=new
bpy.data.actions['Jog'].asset_data.description='Approved medium-speed Jog. Motion unchanged from RUN_REFINED.'
rig.animation_data.action=None;reset();rest_matrix={p.name:p.matrix.copy()for p in CTRL}
footmesh=bpy.data.objects['Object_11'];rest_points=[footmesh.matrix_world@v.co for v in footmesh.data.vertices];feet={}
for kind in ['front','rear']:
 for side,sign in [('L',1),('R',-1)]:
  key=kind+'.'+side;ids=[i for i,p in enumerate(rest_points)if p.z<.17 and sign*p.x>.25 and(p.y<-.9 if kind=='front'else p.y>1)]
  feet[key]={'ids':ids,'center':sum((rest_points[i]for i in ids),Vector())/len(ids),'control':'CTRL_paw_'+key,'sign':sign}
for o in meshes:
 for m in o.modifiers:
  if m.type=='SUBSURF':m.show_viewport=False
N=32;STRIDE=7.8
OFFSETS={'front.R':0,'front.L':.09,'rear.R':.47,'rear.L':.56}
def sprint_foot(t,key):
 u=(t-OFFSETS[key])%1;front=key.startswith('front');d=.18 if front else .16
 start=(-1.05 if key.endswith('R')else-1.15)if front else-1.10
 if u<d:
  dy=start+STRIDE*u;height=0
  pitch=-6*(1-smooth(u/.035))+(22 if front else 27)*smooth((u-d+.065)/.065)
  toe=(11 if front else 16)*smooth((u-d+.055)/.055)
 else:
  end=start+STRIDE*d
  if front:
   dy=curve([(d,end),(.34,.80),(.50,.32),(.66,-.90),(.80,-2.20),(.91,-1.70),(1,start)],u,start_d=STRIDE,end_d=STRIDE,positive=True)
   height=curve([(d,0),(.34,.54),(.50,.64),(.66,1.14),(.80,1.20),(.91,.44),(1,0)],u,start_d=0,end_d=0,positive=True)
   pitch=curve([(d,22),(.36,45),(.53,25),(.74,-8),(.91,-13),(1,-6)],u)
  else:
   dy=curve([(d,end),(.34,1.85),(.48,.74),(.64,-.55),(.82,-1.46),(.93,-1.46),(1,start)],u,start_d=STRIDE,end_d=STRIDE,positive=True)
   height=curve([(d,0),(.34,1.30),(.46,.44),(.56,.15),(.68,.10),(.82,.12),(.93,.065),(1,0)],u,start_d=0,end_d=0,positive=True)
   pitch=curve([(d,27),(.34,38),(.46,24),(.56,8),(.68,5),(.82,-8),(.93,-10),(1,-6)],u)
  toe=(20 if front else 24)*math.sin(math.pi*(u-d)/(1-d))**2
 return {'u':u,'duty':d,'dy':dy,'height':max(0,height),'pitch':pitch,'toe':toe,'contact':u<d}

def pose(t):
 reset();collect=math.cos(TAU*(t-.37))
 translate('CTRL_body',(.015*math.sin(TAU*t),.13*math.sin(TAU*(t-.10)),-.18+.24*math.cos(2*TAU*(t-.37))-.20*math.exp(8*(math.cos(TAU*(t-.11))-1))-.12*math.exp(8*(math.cos(TAU*(t-.63))-1))))
 rotate('CTRL_body',x=5.0*math.sin(TAU*(t-.13)),y=.5*math.sin(TAU*t))
 rotate('CTRL_hips',x=-22*collect,z=.7*math.sin(TAU*t))
 rotate('CTRL_spine_mid',x=36*math.cos(TAU*(t-.40)))
 rotate('CTRL_chest',x=-19*math.cos(TAU*(t-.44)),z=-.8*math.sin(TAU*t))
 rotate('CTRL_neck_base',x=8+4.5*math.sin(TAU*(t-.18)))
 rotate('CTRL_neck_upper',x=1-3.2*math.sin(TAU*(t-.27)))
 states={key:sprint_foot(t,key)for key in feet}
 for side in ['L','R']:
  rotate('CTRL_shoulder.'+side,x=-13*math.cos(TAU*states['front.'+side]['u']))
  rotate('CTRL_hip_socket.'+side,x=-5*math.cos(TAU*states['rear.'+side]['u']))
  rotate('CTRL_ear.'+side,x=5+2*math.sin(2*TAU*t-.9),z=.4*math.sin(TAU*t))
 for i,lift in enumerate([19,12,5,2,0]):
  rotate('CTRL_tail_%02d'%(i+1),x=lift+(2.5+i*.7)*math.sin(TAU*(t-.11)-i*.40),z=(.6+i*.2)*math.sin(TAU*(t-.12)-i*.40))
 bpy.context.view_layer.update();p=rig.pose.bones['CTRL_head'];m=p.matrix.copy()
 goal=Quaternion((1,0,0),math.radians(4+3*math.sin(TAU*(t-.22))))@rest_matrix[p.name].to_quaternion()
 q=m.to_quaternion().slerp(goal,.74);target=q.to_matrix().to_4x4();target.translation=m.translation;p.matrix=target
 for key,state in states.items():set_paw(key,state['dy'],state['height'],state['pitch']);rotate('CTRL_toes_'+key,x=state['toe'])
 bpy.context.view_layer.update()
 for _ in range(6):
  observed=sole_points()
  for key,state in states.items():
   f=feet[key];q=observed[key]
   translate(f['control'],(f['center'].x-q['center'].x,f['center'].y+state['dy']-q['center'].y,.035+state['height']-q['minZ']))
  bpy.context.view_layer.update()
 return states,sole_points()
a=bpy.data.actions.new('Sprint');a.use_fake_user=True;a.asset_mark();a.asset_data.description='Distinct fast double-suspension gallop: long fore reach, high rear kickback, compact low recovery and travelling body wave.'
a.use_frame_range=True;a.frame_start=1;a.frame_end=N+1;a['cycle_frames']=N;a['in_place']=True;a['metres_per_second']=STRIDE*60/N;a['stride_length']=STRIDE;a['revision']=4
rig.animation_data.action=a;samples=[]
for frame in range(1,N+2):
 scene.frame_set(frame);states,obs=pose((frame-1)/N);row={'frame':frame,'feet':{},'legs':{}}
 for key,state in states.items():
  q=obs[key];row['feet'][key]={'contact':state['contact'],'height':q['minZ'],'center':list(q['center']),'idealY':feet[key]['center'].y+state['dy'],'error':max(abs(q['minZ']-.035-state['height']),abs(q['center'].y-feet[key]['center'].y-state['dy']))}
  upper=rig.pose.bones['DEF_'+key.split('.')[0]+'_upper.'+key[-1]];lower=rig.pose.bones['DEF_'+key.split('.')[0]+'_lower.'+key[-1]]
  row['legs'][key]={'ik_error':(lower.tail-rig.pose.bones['MCH_target_'+key].head).length,'bend':math.degrees((upper.tail-upper.head).angle(lower.tail-lower.head)),'hip':list(upper.head),'knee':list(upper.tail)}
 for p in CTRL:p.keyframe_insert('location',frame=frame,group=p.name);p.keyframe_insert('rotation_euler',frame=frame,group=p.name)
 samples.append(row)
for fc in a.fcurves:
 ps=list(fc.keyframe_points);values=[k.co.y for k in ps[:-1]]
 for i,k in enumerate(ps):
  j=i%N;prev=values[(j-1)%N];value=values[j];nxt=values[(j+1)%N];slope=(nxt-prev)/2 if(value-prev)*(nxt-value)>0 else 0
  k.interpolation='BEZIER';k.handle_left_type='FREE';k.handle_right_type='FREE';k.handle_left=(k.co.x-1/3,k.co.y-slope/3);k.handle_right=(k.co.x+1/3,k.co.y+slope/3)
 fc.modifiers.new('CYCLES')
assert keep=={n:action_hash(bpy.data.actions[n])for n in keep}
assert preserve['mesh']==geometry_hash();assert preserve['rig']==skeleton_hash();assert preserve['weights']==weight_hash();assert preserve['materials']==materials_hash()
for o in meshes:
 for m in o.modifiers:
  if m.type=='SUBSURF':m.show_viewport=True
for x in bpy.data.actions:x.use_fake_user=True
scene.frame_set(1);scene.frame_start=1;scene.frame_end=1440;scene.use_preview_range=False;scene.sync_mode='FRAME_DROP'
for o in scene.objects:o.select_set(False)
rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='POSE')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Amaterasu-Movement.blend'))
report={'revision':4,'input_sha256':SOURCE_HASH,'preserved':preserve,'unchanged_actions':keep,'action_mapping':mapping,'cycle_frames':N,'stride':STRIDE,'speed':STRIDE*60/N,'samples':samples}
(ROOT/'review/authoring.json').write_text(json.dumps(report,indent=2))
print('SPRINT_AUTHORED','IK',max(v['ik_error']for s in samples for v in s['legs'].values()),'contact',max(v['error']for s in samples for v in s['feet'].values()if v['contact']),flush=True)

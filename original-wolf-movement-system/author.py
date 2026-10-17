import bpy,math,hashlib,json,ast
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
R=Path(__file__).resolve().parent;SOURCE=R.parent/'original-wolf-sprint-playback/Amaterasu-Movement.blend';assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='bcf79d66cd522bbca442982ff71d88a11fecb0391d727f3319496c78721d86e4'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));s=bpy.context.scene;s.name='01 · Action inspection';r=bpy.data.objects['WOLF_RIG']
if r.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
r.animation_data.action=None
for p in r.pose.bones:p.matrix_basis.identity()
bpy.context.view_layer.update();CTRL=[p.name for p in r.pose.bones if p.name.startswith('CTRL_')];REST={n:r.pose.bones[n].matrix.copy()for n in CTRL};ROOTREST=REST['CTRL_root'];mesh=bpy.data.objects['Object_11'];feet={}
for kind in ['front','rear']:
 for side,sign in [('L',1),('R',-1)]:
  ids=[v.index for v in mesh.data.vertices if (p:=mesh.matrix_world@v.co).z<.17 and sign*p.x>.25 and(p.y<-.9 if kind=='front'else p.y>1)]
  feet[kind+'.'+side]={'ids':ids,'ctrl':'CTRL_paw_'+kind+'.'+side}
def soles(rig=r,obj=mesh):
 bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get();ev=obj.evaluated_get(dep);me=ev.to_mesh();out={}
 for key,data in feet.items():
  pts=[ev.matrix_world@me.vertices[i].co for i in data['ids']];out[key]={'center':sum(pts,Vector())/len(pts),'z':min(p.z for p in pts)}
 ev.to_mesh_clear();return out
def reset():
 for p in r.pose.bones:p.matrix_basis.identity()
def source(name,phase):
 r.animation_data.action=bpy.data.actions[name];reset();n=int(bpy.data.actions[name].get('cycle_frames',{'Idle':240,'Walk':72,'Jog':40,'Sprint_Fluid':32}.get(name,32)));f=1+(phase%1)*n;s.frame_set(int(f),subframe=f%1);return{n:(r.pose.bones[n].location.copy(),r.pose.bones[n].rotation_euler.copy(),r.pose.bones[n].scale.copy())for n in CTRL}
def apply(pose):
 r.animation_data.action=None
 for n,(loc,rot,scale)in pose.items():p=r.pose.bones[n];p.location=loc;p.rotation_euler=rot;p.scale=scale
 bpy.context.view_layer.update()
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def quint(x):x=max(0,min(1,x));return x*x*x*(10+x*(-15+6*x))
def root(theta,pos=(0,0,0)):
 m=Quaternion((0,0,1),theta).to_matrix().to_4x4()@ROOTREST;m.translation=pos;r.pose.bones['CTRL_root'].matrix=m;bpy.context.view_layer.update()
def new_action(name,N,**meta):
 a=bpy.data.actions.new(name);a.use_fake_user=True;a.use_frame_range=True;a.frame_start=1;a.frame_end=N+1;a['cycle_frames']=N
 for k,v in meta.items():a[k]=v
 a.asset_mark();return a
def capture(a,f,names=CTRL):
 # Insert into the specified Action without reevaluating the already solved pose.
 r.animation_data.action=a
 for n in names:
  p=r.pose.bones[n]
  for path in ['location','rotation_euler','scale']:p.keyframe_insert(path,frame=f,group=n)
 r.animation_data.action=None
def finish(a,loop=True):
 for fc in a.fcurves:
  ps=fc.keyframe_points
  for k in ps:k.interpolation='BEZIER';k.handle_left_type='AUTO_CLAMPED';k.handle_right_type='AUTO_CLAMPED'
  if loop and len(ps)>2:
   # Periodic endpoint derivatives, including irregular contact-boundary samples.
   dt=(ps[1].co.x-ps[0].co.x)+(ps[-1].co.x-ps[-2].co.x);slope=(ps[1].co.y-ps[-2].co.y)/dt
   for i,k in [(0,ps[0]),(-1,ps[-1])]:
    k.handle_left_type='FREE';k.handle_right_type='FREE';k.handle_left=(k.co.x-1/3,k.co.y-slope/3);k.handle_right=(k.co.x+1/3,k.co.y+slope/3)
   fc.modifiers.new('CYCLES')
def solve(targets,passes=12):
 for iteration in range(passes):
  obs=soles()
  for key,goal in targets.items():
   p=r.pose.bones[feet[key]['ctrl']];m=p.matrix.copy();m.translation+=Vector((goal['x']-obs[key]['center'].x,goal['y']-obs[key]['center'].y,goal['z']-obs[key]['z']));p.matrix=m
  bpy.context.view_layer.update()
 return soles()
# Shared additive gaze layer, with asymmetrical pauses and a gentle return to centre.
looknodes=[(0,0),(.10,0),(.23,1),(.34,1),(.46,0),(.56,0),(.70,-1),(.80,-.8),(.93,0),(1,0)]
def look(t):
 for (a,x),(b,y)in zip(looknodes,looknodes[1:]):
  if t<=b:return x+(y-x)*smooth((t-a)/(b-a))
 return 0
looknames=['CTRL_neck_base','CTRL_neck_upper','CTRL_head','CTRL_ear.L','CTRL_ear.R']
add=new_action('ADD_LookAround',480,additive=True,movement_wind_level=0)
for f in sorted(set([1,481]+[1+round(t*480)for t,v in looknodes]+list(range(1,482,24)))):
 reset();t=(f-1)/480
 for n,factor,delay in [('CTRL_neck_base',2,.025),('CTRL_neck_upper',6,.012),('CTRL_head',12,0)]:
  p=r.pose.bones[n];p.rotation_euler.z=math.radians(factor*look(max(0,t-delay)));p.rotation_euler.x=math.radians(.4*math.sin(math.tau*t))
 for side,sgn in [('L',1),('R',-1)]:r.pose.bones['CTRL_ear.'+side].rotation_euler=(math.radians(2*math.sin(math.tau*3*t+sgn)*math.sin(math.pi*t)**2),0,math.radians(sgn*1.5*look(t)))
 capture(add,f,looknames)
finish(add)
# Standalone natural variants. Accepted source Actions are never overwritten.
for name,base,N in [('Idle_Natural','Idle',480),('Walk_Natural','Walk',72),('Jog_Natural','Jog',40)]:
 a=new_action(name,N,in_place=True,movement_wind_level=.28 if base=='Jog'else 0,metres_per_second={'Idle':0,'Walk':2/1.2,'Jog':7.2}[base])
 for f in range(1,N+2,2 if base!='Idle'else 4):
  t=(f-1)/N;pose=source(base,t*(2 if base=='Idle'else 1));apply(pose)
  if base=='Idle':
   for n,factor,delay in [('CTRL_neck_base',2,.025),('CTRL_neck_upper',6,.012),('CTRL_head',12,0)]:r.pose.bones[n].rotation_euler.z+=math.radians(factor*look(max(0,t-delay)))
   for i in range(1,6):r.pose.bones[f'CTRL_tail_{i:02}'].rotation_euler.z+=math.radians((.7+i*.2)*math.sin(math.tau*(t-.025*i)))
   for side,sgn in [('L',1),('R',-1)]:r.pose.bones['CTRL_ear.'+side].rotation_euler.x+=math.radians(1.8*math.sin(math.tau*3*t+sgn)*math.sin(math.pi*t)**2)
  else:
   amp=1.8 if base=='Walk'else 3.5
   r.pose.bones['CTRL_neck_base'].rotation_euler.x+=math.radians(amp*math.sin(math.tau*(t-.12)))
   r.pose.bones['CTRL_neck_upper'].rotation_euler.x-=math.radians(amp*.75*math.sin(math.tau*(t-.25)))
   r.pose.bones['CTRL_head'].rotation_euler.x+=math.radians(.6*math.sin(math.tau*(t-.37)))
   for i in range(1,6):r.pose.bones[f'CTRL_tail_{i:02}'].rotation_euler.z+=math.radians((.45+i*.20)*math.sin(math.tau*(t-.065*i)))
  capture(a,f)
 finish(a);print('AUTHORED',name,flush=True)
# Read only the actual already-authored soles at touchdown/liftoff.
specs={'Walk':{'base':'Walk_Natural','N':72,'v':2/1.2,'radius':7,'lean':2.5,'d':{'front':.65,'rear':.65},'offset':{'rear.L':0,'front.L':.25,'rear.R':.5,'front.R':.75}},'Jog':{'base':'Jog_Natural','N':40,'v':7.2,'radius':14,'lean':5,'d':{'front':.22,'rear':.23},'offset':{'front.R':0,'front.L':.12,'rear.R':.50,'rear.L':.62}},'Sprint':{'base':'Sprint_Fluid','N':32,'v':14.625,'radius':30,'lean':8.5,'d':{'front':.18,'rear':.16},'offset':{'front.R':0,'front.L':.09,'rear.L':.47,'rear.R':.56}}}
report={}
for kind,sp in specs.items():
 refs={}
 for key in feet:
  off=sp['offset'][key];d=sp['d'][key.split('.')[0]];source(sp['base'],off);start=soles()[key]['center'];source(sp['base'],off+d);end=soles()[key]['center'];refs[key]=(start,end)
 for direction,sign in [('L',1),('R',-1)]:
  N=sp['N'];duration=N/60;w=sign*sp['v']/sp['radius'];a=new_action(kind+'_Turn_'+direction,N,in_place=True,metres_per_second=sp['v'],yaw_rate_radians=w,turn_radius=sp['radius'],movement_wind_level=1 if kind=='Sprint'else .28 if kind=='Jog'else 0)
  def P(t):theta=w*t;return Vector((sp['v']/w*(1-math.cos(theta)),-sp['v']/w*math.sin(theta),0))
  def correction(key,u):
   start,end=refs[key];d=sp['d'][key.split('.')[0]];theta=w*u*duration;desired=Quaternion((0,0,1),-theta)@(start-P(u*duration));straight=start+(end-start)*(u/d);return desired-straight
  frames=set(range(1,N+2,2));frames.add(N+1)
  for key,off in sp['offset'].items():
   for edge in [off,(off+sp['d'][key.split('.')[0]])%1]:frames.add(1+edge*N)
  logs=[]
  for f in sorted(frames):
   t=(f-1)/N;pose=source(sp['base'],t);obs=soles();apply(pose)
   # Centripetal bank, distributed yaw through pelvis, spine, shoulders and neck.
   r.pose.bones['CTRL_body'].rotation_euler.y-=math.radians(sign*sp['lean']);r.pose.bones['CTRL_body'].location.x+=sign*.025;r.pose.bones['CTRL_body'].location.z-=.075
   for n,angle in [('CTRL_hips',-2.8),('CTRL_spine_mid',1.0),('CTRL_chest',2.8),('CTRL_neck_base',1.8),('CTRL_neck_upper',3.2),('CTRL_head',4.0)]:r.pose.bones[n].rotation_euler.z+=math.radians(sign*angle)
   for side in ['L','R']:r.pose.bones['CTRL_shoulder.'+side].rotation_euler.z+=math.radians(sign*1.5)
   for i in range(1,6):r.pose.bones[f'CTRL_tail_{i:02}'].rotation_euler.z+=math.radians(sign*(2.5+i*.6)*(1+.15*math.sin(math.tau*(t-.07*i))))
   bpy.context.view_layer.update();targets={};contacts={}
   for key in feet:
    u=(t-sp['offset'][key])%1;d=sp['d'][key.split('.')[0]];p=r.pose.bones[feet[key]['ctrl']]
    if u<d+1e-7:delta=correction(key,u);yaw=-w*u*duration;contacts[key]=True
    else:
     v=(u-d)/(1-d);endDelta=correction(key,d);eps=1e-4;ds=(correction(key,d+eps)-correction(key,d-eps))/(2*eps);de=(correction(key,eps)-correction(key,-eps))/(2*eps)
     delta=(2*v**3-3*v*v+1)*endDelta+(v**3-2*v*v+v)*ds*(1-d)+(v**3-v*v)*de*(1-d);delta.x+=sign*.045*math.sin(math.pi*v)**2;yaw=-w*d*duration*(1-smooth(v));contacts[key]=False
    m=p.matrix.copy();q=Quaternion((0,0,1),yaw)@m.to_quaternion();m=q.to_matrix().to_4x4();m.translation=p.matrix.translation;p.matrix=m
    targets[key]={'x':obs[key]['center'].x+delta.x,'y':obs[key]['center'].y+delta.y,'z':max(.035,obs[key]['z'])}
   actual=solve(targets);logs.append({'f':f,'error':max(max(abs(actual[k]['center'].x-targets[k]['x']),abs(actual[k]['center'].y-targets[k]['y']),abs(actual[k]['z']-targets[k]['z']))for k in feet),'min_z':min(x['z']for x in actual.values())});capture(a,f)
  finish(a);report[a.name]={'radius':sp['radius'],'yaw_rate':w,'max_solve_error':max(x['error']for x in logs),'min_z':min(x['min_z']for x in logs),'frames':len(frames)};print('AUTHORED',a.name,report[a.name],flush=True)
# Stationary 90-degree shuffles: twelve small paw placements, with world-ground anchors.
order=['front.L','rear.R','front.R','rear.L'];N=216
for direction,sign in [('L',1),('R',-1)]:
 a=new_action('Idle_Turn_'+direction+'90',N,in_place=False,one_shot=True,root_yaw_degrees=sign*90,movement_wind_level=0)
 source('Idle',0);ref=soles();anchors={k:ref[k]['center'].copy()for k in feet};angles={k:0. for k in feet};logs=[]
 def theta(f):return sign*math.pi/2*smooth((f-13)/192)
 for f in range(1,N+2,2):
  t=(f-1)/N;pose=source('Idle',t);apply(pose);th=theta(f);root(th)
  envelope=math.sin(math.pi*t)**2
  r.pose.bones['CTRL_body'].location.z-=.035*envelope
  for n,gain in [('CTRL_neck_base',2),('CTRL_neck_upper',3),('CTRL_head',4)]:r.pose.bones[n].rotation_euler.z+=math.radians(sign*gain*envelope)
  for i in range(1,6):r.pose.bones[f'CTRL_tail_{i:02}'].rotation_euler.z+=math.radians(sign*(2+i*.45)*envelope)
  targets={};current={k:(anchors[k].copy(),angles[k],.035)for k in feet}
  for j in range(12):
   key=order[j%4];start=13+j*16;end=start+12.8
   if f<start:continue
   destination_angle=theta(min(205,end+22))if j<8 else sign*math.pi/2;dest=Quaternion((0,0,1),destination_angle)@ref[key]['center']
   if f>=end:anchors[key]=dest;angles[key]=destination_angle;current[key]=(dest,destination_angle,.035)
   else:
    v=(f-start)/(end-start);h=.16*math.sin(math.pi*v)**2;current[key]=(anchors[key].lerp(dest,quint(v)),angles[key]+(destination_angle-angles[key])*quint(v),.035+h)
    r.pose.bones['CTRL_body'].location.x+=(.045 if key.endswith('L')else -.045)*math.sin(math.pi*v)**2
  bpy.context.view_layer.update()
  for key,(point,angle,height)in current.items():
   p=r.pose.bones[feet[key]['ctrl']];m=p.matrix.copy();q=Quaternion((0,0,1),angle-th)@m.to_quaternion();m=q.to_matrix().to_4x4();m.translation=p.matrix.translation;p.matrix=m;targets[key]={'x':point.x,'y':point.y,'z':height}
  actual=solve(targets,6);logs.append(max(max(abs(actual[k]['center'].x-targets[k]['x']),abs(actual[k]['center'].y-targets[k]['y']),abs(actual[k]['z']-targets[k]['z']))for k in feet));capture(a,f)
 finish(a,False);report[a.name]={'max_solve_error':max(logs),'duration':N/60,'steps':12};print('AUTHORED',a.name,report[a.name],flush=True)
 clone=a.copy();clone.name='.DEMO_'+a.name;clone.use_fake_user=True
 for fc in list(clone.fcurves):
  if '"CTRL_root"'in fc.data_path:clone.fcurves.remove(fc)
# Wind level metadata gates the existing effect; original Actions keep their bone curves.
for action in bpy.data.actions:
 if 'movement_wind_level'not in action:action['movement_wind_level']=1.0 if action.pose_markers.get('SPRINT_WIND_ENABLE')else 0.0
for o in list(bpy.data.collections['05 · Sprint wind — separate effect'].objects)+list(bpy.data.collections['06 · Lightweight wind preview (viewport only)'].objects):
 if not o.animation_data:continue
 for fc in o.animation_data.drivers:
  for v in fc.driver.variables:
   if v.name=='gate':v.targets[0].data_path='animation_data.action["movement_wind_level"]';v.targets[0].use_fallback_value=True;v.targets[0].fallback_value=0
  if fc.data_path=='scale':
   fc.driver.expression=fc.driver.expression.replace('gate','min(1,max(0,gate*4))')
   if fc.array_index==1:fc.driver.expression+='*(0.65+0.35*min(1,max(0,gate)))'
  # Only three finished ribbons are active at medium speed.
  if o.name.startswith('Wind ribbon')and int(o.name[-2:])not in[1,5,9]:fc.driver.expression='('+fc.driver.expression+')*(1 if gate>0.5 else 0)'
for a in bpy.data.actions:a.use_fake_user=True
r.animation_data.action=bpy.data.actions['Idle_Natural'];s.frame_set(1);s.frame_start=1;s.frame_end=480;s.render.fps=60;s.sync_mode='FRAME_DROP';bpy.context.view_layer.objects.active=r;r.select_set(True);bpy.ops.object.mode_set(mode='POSE')
(R/'review/authoring.json').write_text(json.dumps({'turns':report,'specs':specs,'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest()},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(R/'Amaterasu-Movement.blend'));print('MOVEMENT_ACTIONS_SAVED',flush=True)

"""Milestone 2. Existing rig only; new Actions with native root motion and phase markers."""
import bpy,math,json,hashlib,ast
from pathlib import Path
from mathutils import Vector,Quaternion
R=Path(__file__).resolve().parent;SOURCE=R.parent/'original-wolf-movement-system/Amaterasu-Movement.blend'
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest()=='82cee2e6e6d8ac3c3708c4a16d12cb5fefaa155da74c961fe34bec8810082cf4'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));s=bpy.data.scenes['01 · Action inspection'];bpy.context.window.scene=s;r=bpy.data.objects['WOLF_RIG']
bpy.context.view_layer.objects.active=r;r.select_set(True)
if r.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
CTRL=[p.name for p in r.pose.bones if p.name.startswith('CTRL_')]
def reset():
 r.animation_data.action=None
 for p in r.pose.bones:p.matrix_basis.identity()
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def curve(nodes,t):
 for (a,x),(b,y)in zip(nodes,nodes[1:]):
  if t<=b:return x+(y-x)*smooth((t-a)/(b-a))
 return nodes[-1][1]
def vec(nodes,t):return Vector([curve([(f,v[i])for f,v in nodes],t)for i in range(3)])
reset();s.frame_set(2);bpy.context.view_layer.update();s.frame_set(1);bpy.context.view_layer.update();REST={n:r.pose.bones[n].matrix.copy()for n in CTRL};rr=REST['CTRL_root'];foot=bpy.data.objects['Object_11'];feet={}
for kind in ['front','rear']:
 for side,sign in [('L',1),('R',-1)]:
  key=kind+'.'+side;ids=[v.index for v in foot.data.vertices if(p:=foot.matrix_world@v.co).z<.17 and sign*p.x>.25 and(p.y<-.9 if kind=='front'else p.y>1)];feet[key]={'ids':ids,'ctrl':'CTRL_paw_'+key,'sign':sign}
def soles():
 bpy.context.view_layer.update();ev=foot.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();out={}
 for k,d in feet.items():
  points=[ev.matrix_world@me.vertices[i].co for i in d['ids']];out[k]={'center':sum(points,Vector())/len(points),'z':min(p.z for p in points)}
 ev.to_mesh_clear();return out
REF=soles()
def source(name,phase=0):
 reset();a=bpy.data.actions[name];r.animation_data.action=a;f=1+phase*int(a.get('cycle_frames',240));s.frame_set(int(f),subframe=f%1);pose={n:r.pose.bones[n].matrix_basis.copy()for n in CTRL};points=soles();r.animation_data.action=None;return pose,points
def apply(pose):
 reset()
 for n,m in pose.items():r.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
def root(pos):
 m=rr.copy();m.translation=pos;r.pose.bones['CTRL_root'].matrix=m;bpy.context.view_layer.update()
def rotate(n,x=0,y=0,z=0):r.pose.bones[n].rotation_euler=tuple(math.radians(v)for v in(x,y,z))
def solve(goals,iterations=7):
 for j in range(iterations):
  obs=soles()
  for k,g in goals.items():
   p=r.pose.bones[feet[k]['ctrl']];m=p.matrix.copy();m.translation+=Vector((g['center'].x-obs[k]['center'].x,g['center'].y-obs[k]['center'].y,g['z']-obs[k]['z']));p.matrix=m
  bpy.context.view_layer.update()
  # Non-stretch IK: project ankle targets inside the two-bone reach sphere.
  # This prevents an iterative sole solver pushing an unreachable control farther away.
  for key,d in feet.items():
   kind,side=key.split('.');up=r.pose.bones['DEF_'+kind+'_upper.'+side];lo=r.pose.bones['DEF_'+kind+'_lower.'+side];target=r.pose.bones['MCH_target_'+key].head.copy();delta=target-up.head;limit=(up.length+lo.length)*.985
   if delta.length>limit:
    paw=r.pose.bones[d['ctrl']];m=paw.matrix.copy();m.translation+=up.head+delta.normalized()*limit-target;paw.matrix=m
  bpy.context.view_layer.update()
 return soles()
def ikerrors():
 return {k:(r.pose.bones['DEF_'+k.split('.')[0]+'_lower.'+k[-1]].tail-r.pose.bones['MCH_target_'+k].head).length for k in feet}
def capture(a,f):
 r.animation_data.action=a
 for n in CTRL:
  p=r.pose.bones[n]
  for path in ['location','rotation_euler']:p.keyframe_insert(path,frame=f,group=n)
 r.animation_data.action=None

def finish(a,loop=False):
 for fc in list(a.fcurves):
  vals=[k.co.y for k in fc.keyframe_points]
  if max(vals)-min(vals)<1e-6:
   value=vals[0];fc.keyframe_points.clear();fc.keyframe_points.insert(1,value)
  for k in fc.keyframe_points:k.interpolation='BEZIER';k.handle_left_type='AUTO_CLAMPED';k.handle_right_type='AUTO_CLAMPED'
  if loop and len(fc.keyframe_points)>1:fc.modifiers.new('CYCLES')
def new(name,N,markers,wind=0,**meta):
 a=bpy.data.actions.new(name);a.use_fake_user=True;a.asset_mark();a.asset_data.tags.new('Jump and dodge');a.asset_data.description='Original wolf, original rig · '+name.replace('_',' ');a.use_frame_range=True;a.frame_start=1;a.frame_end=N+1;a['duration_frames']=N;a['one_shot']=True;a['root_motion']=True;a['movement_wind_level']=wind
 for label,frame in markers.items():a.pose_markers.new(label).frame=int(frame+1)
 for k,v in meta.items():a[k]=v
 return a
report={};samples={};idle,idlep=source('Idle',0)

def body(t,N,crouch,pitch,compression,lean=0,twist=0,energy=1):
 # Body translation is in world-up under the horizontal body control.
 r.pose.bones['CTRL_body'].location.z=crouch
 rotate('CTRL_body',pitch,y=lean)
 rotate('CTRL_hips',-compression*.62,z=-twist*.35)
 rotate('CTRL_spine_mid',compression,z=twist*.4)
 rotate('CTRL_chest',-compression*.48,z=twist*.55)
 # Delayed flexion across both neck joints, with partial head stabilisation.
 wave=math.sin(math.pi*t/max(1,N));lag=math.sin(math.pi*(t-5)/max(1,N))
 rotate('CTRL_neck_base',-pitch*.24+energy*3.5*wave,z=twist*.25)
 rotate('CTRL_neck_upper',-pitch*.32-energy*2.5*lag,z=-twist*.15)
 rotate('CTRL_head',-pitch*.30+energy*1.6*math.sin(math.pi*(t-9)/max(1,N)),z=-twist*.30)
 for side,sgn in [('L',1),('R',-1)]:
  rotate('CTRL_shoulder.'+side,-compression*.25+sgn*lean*.16,z=twist*.16)
  rotate('CTRL_hip_socket.'+side,compression*.13,z=-twist*.10)
  rotate('CTRL_ear.'+side,energy*3.5*wave,y=sgn*energy*1.5*lag)
 for i in range(1,6):
  follow=math.sin(math.pi*(t-3*i)/max(1,N));rotate(f'CTRL_tail_{i:02}',energy*(4+i*.7)*follow-pitch*.08,y=lean*.05,z=twist*(-.35-i*.06)+energy*(1+i*.35)*math.sin(math.pi*(t-5*i)/max(1,N)))

def blend_pose(pose,w):
 for n,m in pose.items():
  if n=='CTRL_root' or n.startswith(('CTRL_paw_','CTRL_toes_','CTRL_pole_')):continue
  p=r.pose.bones[n];l,q,sc=p.matrix_basis.decompose();l2,q2,sc2=m.decompose();p.matrix_basis=__import__('mathutils').Matrix.LocRotScale(l.lerp(l2,w),q.slerp(q2,w),sc.lerp(sc2,w))

def blend_paw_rotations(pose,w):
 for n in CTRL:
  if not n.startswith(('CTRL_paw_','CTRL_toes_','CTRL_pole_')):continue
  p=r.pose.bones[n];q=p.rotation_euler.to_quaternion();target=pose[n].to_quaternion();p.rotation_euler=q.slerp(target,max(0,min(1,w))).to_euler('XYZ')
 bpy.context.view_layer.update()

def author_jump(name,gait,speed,T,A,height,recover=32):
 F=T+A;N=F+recover;phase={'Idle':0,'Walk_Natural':.45,'Jog_Natural':.52,'Sprint_Fluid':.55}[gait];initial,ip=source(gait,phase);endphase=(phase+N/int(bpy.data.actions[gait].get('cycle_frames',240)))%1;endpose,ep=source(gait,endphase)
 wind=1 if gait=='Sprint_Fluid'else .28 if gait=='Jog_Natural'else 0
 a=new(name,N,{'ANTICIPATE':0,'TAKEOFF_FRONT':T*.45,'TAKEOFF_HIND':T,'AIRBORNE':T+1,'APEX':T+A/2,'LAND_FRONT':F,'LAND_HIND':F+5,'RECOVERY':F+12,'GAIT_READY':N},wind,entry_gait=gait,exit_gait=gait,entry_phase=phase,exit_phase=endphase)
 rows=[];releasepts={}
 for key in feet:
  release=T*(.45 if key.startswith('front')else 1);_,points=source(gait,(phase+release/int(bpy.data.actions[gait].get('cycle_frames',240)))%1);releasepts[key]=points[key]
 def path(t):
  f=max(0,min(1,(t-T)/A));z=height*4*f*(1-f)
  y=-speed*t/60 if speed else -.65*smooth((t-T)/A)
  return Vector((0,y,z))
 # Ground anchors inherit the source lead-in pose. Airborne paws gather then reach.
 for f in sorted(set(range(0,N+1,2))|{T,F,F+5,N}|({10.5,11,11.5,12.5,13,13.5,14.5}if gait=='Sprint_Fluid'else set())):
  t=f;movingpose,movingpts=source(gait,(phase+t/int(bpy.data.actions[gait].get('cycle_frames',240)))%1);reset();pos=path(t);root(pos);u=(t-T)/A
  squat=curve([(0,0),(T*.55,-.5),(T,-.12),(T+A*.22,.02),(F,-.30),(F+9,-.46),(N,0)],t)
  pitch=curve([(0,0),(T*.5,-5),(T,-9),(T+A*.3,-5),(T+A*.65,2),(F,8),(F+10,3),(N,0)],t)
  comp=curve([(0,0),(T*.6,10),(T,-7),(T+A*.3,-11),(T+A*.65,-2),(F,5),(F+9,12),(N,0)],t)
  body(t,N,squat,pitch,comp,energy=1.1 if speed<10 else 1.5)
  if t<T*.3:blend_pose(initial,1-smooth(t/(T*.3)))
  if t>F+5:blend_pose(movingpose,smooth((t-F-5)/10))
  bpy.context.view_layer.update();goals={};contacts={}
  for key,d in feet.items():
   front=key.startswith('front');side=d['sign'];release=T*(.45 if front else 1);land=F+(0 if front else 5)+(0 if side>0 else 1)
   start=ip[key]['center'].copy();start.z=0
   end=pos+REF[key]['center'];end.y+=(-.55 if front else -.2);end.z=0
   # At touchdown, lock world X/Y through impact; release into the accepted gait later.
   lp=path(land);anchor=lp+REF[key]['center']+Vector((0,-.55 if front else -.2,0))
   if t<=release:
    point=pos+movingpts[key]['center'] if speed else start;z=max(.035,movingpts[key]['z'] if speed else ip[key]['z']*(1-smooth(t/max(1,release*.5))));contact=z<.055
   elif t<land:
    v=(t-release)/(land-release);spread=1.3 if gait=='Sprint_Fluid'else .85
    dy=curve([(0,releasepts[key]['center'].y-REF[key]['center'].y if speed else start.y-REF[key]['center'].y),(0.25,-spread if front else .85),(0.52,-spread*.75 if front else .35),(.78,-.72 if front else -.55),(1,anchor.y-path(land).y-REF[key]['center'].y)],v)
    lift=curve([(0,(max(.035,releasepts[key]['z'])-.035)/.85-path(release).z if speed else -path(release).z),(.2,.70 if front else .38),(.48,.85 if front else .8),(.75,.3),(1,0)],v)
    point=pos+REF[key]['center']+Vector((side*.07*math.sin(math.pi*v),dy,0));z=max(.035,pos.z+lift*.85+.035);contact=False
    # Interpolate world touchdown to avoid a paw velocity discontinuity.
    w=smooth((v-.78)/.22);z=max(.035,pos.z+lift*.85+.035)
   else:
    point=anchor;z=.035;contact=True
    if t>F+5:
     blend=smooth((t-F-5)/10);goal=pos+movingpts[key]['center'];point=point.lerp(goal,blend);z=.035+(max(.035,movingpts[key]['z'])-.035)*blend;contact=blend<.08
   p=r.pose.bones[d['ctrl']];m=REST[p.name].copy();m.translation+=pos;q=Quaternion((1,0,0),math.radians(curve([(0,0),(release,0),(release+8,25 if front else 32),(land-10,-9),(land,0),(N,0)],t)))@m.to_quaternion();rot=q.to_matrix().to_4x4();rot.translation=m.translation;p.matrix=rot
   rotate('CTRL_toes_'+key,x=8*math.sin(math.pi*max(0,min(1,(t-release)/max(1,land-release)))))
   goals[key]={'center':point,'z':z};contacts[key]=contact
  blend_paw_rotations(movingpose,1-smooth(t/max(1,T*.45)) if t<T*.45 else smooth((t-F-5)/10) if t>F+5 else 0);obs=solve(goals);errors=ikerrors()
  rows.append({'f':f+1,'root':list(pos),'contacts':contacts,'ik':errors,'goal_error':max((Vector((obs[k]['center'].x-goals[k]['center'].x,obs[k]['center'].y-goals[k]['center'].y,obs[k]['z']-goals[k]['z']))).length for k in feet),'min_z':min(x['z']for x in obs.values())});capture(a,f+1)
 finish(a);report[name]={'N':N,'takeoff':T,'land_front':F,'land_hind':F+5,'gait':gait,'phase':phase,'exit_phase':endphase,'speed':speed,'height':height,'distance':path(N).y,'max_ik':max(v for row in rows for v in row['ik'].values())};samples[name]=rows;print('JUMP',name,report[name],flush=True)
for args in [('Jump_Standing','Idle',0,26,48,2.25,36),('Jump_Walk','Walk_Natural',1.6666667,24,44,2.0,36),('Jump_Jog','Jog_Natural',7.2,18,46,2.4,34),('Jump_Sprint','Sprint_Fluid',14.625,12,50,2.65,32)]:author_jump(*args)
# Falling is an AIRBORNE loop, with no planted-paw assumptions or landing baked in.
a=new('Air_Fall',72,{'FALL_LOOP':0},airborne=True);a['one_shot']=False;a['cycle_frames']=72
for t in range(0,73,3):
 reset();body(t,72,0,7+2*math.sin(math.tau*t/72),-3+2*math.sin(math.tau*t/72),energy=.35);goals={}
 for key,d in feet.items():
  front=key.startswith('front');point=REF[key]['center']+Vector((0,-.3 if front else .15,0));goals[key]={'center':point,'z':.48 if front else .72}
 solve(goals);capture(a,t+1)
# Exact closure for the airborne loop.
for fc in a.fcurves:fc.keyframe_points[-1].co.y=fc.keyframe_points[0].co.y
finish(a,True);report[a.name]={'N':72,'airborne':True}
# Magical aerial rebound: asymmetric corkscrew tuck, then extended second flight.
N=78;a=new('Jump_Double',N,{'AIR_ENTRY':0,'ENERGY_GATHER':10,'MAGIC_IMPULSE':18,'SECOND_APEX':39,'DESCENT_READY':78},airborne=True,entry_gait='Air_Fall',exit_gait='Air_Fall')
fall,fallpts=source('Air_Fall',0);rows=[]
for t in range(0,N+1,2):
 reset();z=curve([(0,0),(10,-.10),(18,.2),(40,2.7),(N,0)],t);root((0,-2.8*t/N,z));env=math.sin(math.pi*t/N)**2;twist=16*env;body(t,N,-.12*env,-10*env,22*math.sin(math.pi*t/N)**3,lean=-8*env,twist=twist,energy=1.8)
 blend_pose(fall,1-smooth(t/12)if t<12 else smooth((t-64)/14)if t>64 else 0);goals={}
 for key,d in feet.items():
  front=key.startswith('front');point=REF[key]['center']+Vector((d['sign']*.15*env,-2.8*t/N+(-.55 if front else -.5)*env,0));goals[key]={'center':point,'z':z+(.48 if front else .72)+(.68 if front else .4)*math.sin(math.pi*t/N)**2}
 solve(goals);rows.append({'f':t+1,'ik':ikerrors()});capture(a,t+1)
finish(a);report[a.name]={'N':N,'height':2.7,'distance':-2.8,'max_ik':max(v for row in rows for v in row['ik'].values())};samples[a.name]=rows
# Standalone landings start on descent, then front-to-rear impact and recovery.
for heavy,N,startheight,depth,delay in [(False,54,.65,.30,5),(True,78,1.5,.62,8)]:
 name='Land_Heavy'if heavy else'Land_Soft';hit=12 if heavy else 8;a=new(name,N,{'DESCENT':0,'LAND_FRONT':hit,'LAND_HIND':hit+delay,'ABSORB':hit+delay+5,'RECOVERY':hit+delay+12,'IDLE_READY':N},entry_gait='Air_Fall',exit_gait='Idle');rows=[]
 for t in sorted(set(range(0,N+1,2))|{hit,hit+delay,N}):
  reset();z=startheight*(1-smooth(t/hit));root((0,0,z));c=-depth*math.sin(math.pi*max(0,min(1,(t-hit+3)/(N-hit+3))))**2;pitch=curve([(0,5),(hit,10),(hit+delay,-3),(N,0)],t);body(t,N,c,pitch,-c*20,energy=.8 if not heavy else 1.4);blend_pose(idle,smooth((t-N*.72)/(N*.28)));goals={}
  for key,d in feet.items():
   front=key.startswith('front');contact=hit if front else hit+delay;zz=z+(.035 if front else .18*(1-smooth(t/contact)));goals[key]={'center':REF[key]['center'],'z':max(.035,zz)}
  solve(goals);rows.append({'f':t+1,'ik':ikerrors()});capture(a,t+1)
 finish(a);report[name]={'N':N,'hit':hit,'rear_hit':hit+delay,'max_ik':max(v for row in rows for v in row['ik'].values())};samples[name]=rows
# Evasive bounds. L/R/back/dash have separate pushes, arcs, bank and paw offsets.
def dodge(name,dx,dy,gait='Idle',speed=0,N=58):
 phase={'Idle':0,'Walk_Natural':.25,'Jog_Natural':.50,'Sprint_Fluid':.50}[gait];initial,ip=source(gait,phase);epose,ep=source(gait,(phase+N/int(bpy.data.actions[gait].get('cycle_frames',240)))%1)
 push=10 if speed>10 else 14;land=push+(16 if speed>10 else 20);wind=1 if speed>10 else .28 if speed>3 else 0
 a=new(name,N,{'LOAD':0,'PUSH':push-5,'AIRBORNE':push,'LAND_FRONT':land,'LAND_HIND':land+3,'RECOVER':land+9,'GAIT_READY':N},wind,entry_gait=gait,exit_gait=gait,entry_phase=phase,exit_phase=(phase+N/int(bpy.data.actions[gait].get('cycle_frames',240)))%1)
 def path(t):
  u=smooth((t-4)/(land+7-4));flight=max(0,min(1,(t-push)/(land-push)));return Vector((dx*u,dy*u-speed*t/60,(.40 if speed<10 else .56)*math.sin(math.pi*flight)**2))
 rows=[];releasepts={}
 for key in feet:
  front=key.startswith('front');inside=key.endswith('L')if dx>0 else key.endswith('R');release=push-(4 if inside and dx else 2 if front else 0);_,pts=source(gait,(phase+release/int(bpy.data.actions[gait].get('cycle_frames',240)))%1);releasepts[key]=pts[key]
 for t in sorted(set(range(0,N+1,2))|{push,land,land+3,N}):
  movingpose,movingpts=source(gait,(phase+t/int(bpy.data.actions[gait].get('cycle_frames',240)))%1);reset();pos=path(t);root(pos);env=math.sin(math.pi*t/N)**2;sgn=1 if dx>0 else-1 if dx<0 else 0;body(t,N,-.32*env,(-5 if dy>0 else 4)*env,9*env,lean=-sgn*9*env,twist=sgn*8*env,energy=1.15)
  if t<6:blend_pose(initial,1-smooth(t/6))
  if t>land+3:blend_pose(movingpose,smooth((t-land-3)/14))
  goals={}
  for key,d in feet.items():
   front=key.startswith('front');inside=key.endswith('L')if dx>0 else key.endswith('R');release=push-(4 if inside and dx else 2 if front else 0);touch=land+(0 if front else 3)+(1 if inside else 0);anchor=path(touch)+REF[key]['center'];start=ip[key]['center'].copy()
   if t<=release:point=pos+movingpts[key]['center'] if speed else start;zz=max(.035,movingpts[key]['z'] if speed else ip[key]['z']*(1-smooth(t/max(1,release*.6))))
   elif t<touch:
    u=(t-release)/(touch-release);point=pos+REF[key]['center']+Vector((-dx*.12*math.sin(math.pi*u),(.30 if dy<0 else -.25)*math.sin(math.pi*u),0));point+=(releasepts[key]['center']-REF[key]['center'])*(1-smooth(u/.35)) if speed else Vector();zz=pos.z+.035+(.48 if front else .60)*math.sin(math.pi*u)**2+(max(.035,releasepts[key]['z'])-.035)*(1-smooth(u/.35)) if speed else pos.z+.035+(.48 if front else .60)*math.sin(math.pi*u)**2
   else:
    point=anchor;zz=.035
    if t>land+3:
     w=smooth((t-land-3)/14);point=point.lerp(pos+movingpts[key]['center'],w);zz=.035+(max(.035,movingpts[key]['z'])-.035)*w
   p=r.pose.bones[d['ctrl']];m=REST[p.name].copy();m.translation+=pos;q=Quaternion((0,0,1),math.radians(sgn*7*env))@m.to_quaternion();mm=q.to_matrix().to_4x4();mm.translation=m.translation;p.matrix=mm;goals[key]={'center':point,'z':zz};rotate('CTRL_toes_'+key,x=7*env)
  blend_paw_rotations(movingpose,1-smooth(t/6)if t<6 else smooth((t-land-3)/14)if t>land+3 else 0);obs=solve(goals);rows.append({'f':t+1,'root':list(pos),'ik':ikerrors(),'goal_error':max(abs(obs[k]['z']-goals[k]['z'])for k in feet)});capture(a,t+1)
 finish(a);report[name]={'N':N,'gait':gait,'phase':phase,'exit_phase':a['exit_phase'],'speed':speed,'distance':list(path(N)),'land':land,'push':push,'max_ik':max(v for row in rows for v in row['ik'].values())};samples[name]=rows;print('DODGE',name,report[name],flush=True)
for args in [('Dodge_Left',2.6,0),('Dodge_Right',-2.6,0),('Dodge_Back',0,2.7),('Dodge_Forward',0,-4),('Dodge_Walk',1.8,-.6,'Walk_Natural',1.6666667,64),('Dodge_Jog',2.2,-.6,'Jog_Natural',7.2,58),('Dodge_Sprint',3.2,-1.0,'Sprint_Fluid',14.625,52)]:dodge(*args)
for a in bpy.data.actions:a.use_fake_user=True
r.animation_data.action=bpy.data.actions['Jump_Standing'];s.frame_start=1;s.frame_end=180;s.frame_set(1);s.render.fps=60
(R/'review/authoring.json').write_text(json.dumps({'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'actions':report,'samples':samples},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(R/'Amaterasu-Movement.blend'));print('JUMP_DODGE_ACTIONS_SAVED',flush=True)

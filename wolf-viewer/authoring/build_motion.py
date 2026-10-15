"""Direct authoring: continuous whole-tail rig and coordinated canine run."""
import bpy,bmesh,math,json,numpy as np
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];draft=root/'review/drafts';draft.mkdir(parents=True,exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(root.parent/'wolf-run-repair/authoring/wolf.blend'))
rig=bpy.data.objects['DivineWolfRig'];coat=bpy.data.objects['Wolf ivory coat'];scene=bpy.context.scene
if coat.data.shape_keys:coat.shape_key_clear()
rig.animation_data.action=None
for b in rig.pose.bones:b.rotation_mode='XYZ';b.location=(0,0,0);b.rotation_euler=(0,0,0)
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
def read(v):return {coat.vertex_groups[g.group].name:g.weight for g in v.groups}
def write(v,w):
 top=sorted(((n,a) for n,a in w.items() if a>1e-7),key=lambda p:-p[1])[:4];total=sum(a for n,a in top)
 for i in [g.group for g in v.groups]:coat.vertex_groups[i].remove([v.index])
 for n,a in top:
  group=coat.vertex_groups.get(n) or coat.vertex_groups.new(name=n);group.add([v.index],a/total,'REPLACE')
# Subdivision across the whole tail preserves the existing surface and UVs.
bm=bmesh.new();bm.from_mesh(coat.data);edges=[e for e in bm.edges if all(v.co.y>2.72 and abs(v.co.x)<.58 for v in e.verts)];bmesh.ops.subdivide_edges(bm,edges=edges,cuts=1,use_grid_fill=True);bm.to_mesh(coat.data);bm.free()
control=np.array([(0,2.55,3.15),(0,3.15,3.23),(0,3.70,3.58),(0,4.12,4.02),(0,4.24,4.29)]);lengths=np.linalg.norm(np.diff(control,axis=0),axis=1);arc=np.r_[0,np.cumsum(lengths)];total=arc[-1]
def point(s):
 i=min(len(lengths)-1,int(np.searchsorted(arc,s,side='right')-1));u=(s-arc[i])/lengths[i];return control[i]*(1-u)+control[i+1]*u
samples=np.array([point(s) for s in np.linspace(0,total,17)]);tailnames=[f'plume{i:02}' for i in range(16)]
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for i,name in enumerate(tailnames):
 b=rig.data.edit_bones.new(name);b.head=samples[i];b.tail=samples[i+1];b.parent=rig.data.edit_bones[tailnames[i-1]] if i else rig.data.edit_bones['hips'];b.use_connect=i>0
bpy.ops.object.mode_set(mode='OBJECT')
for name in tailnames:rig.pose.bones[name].rotation_mode='XYZ'
for v in coat.data.vertices:
 old=read(v);amount=sum(w for n,w in old.items() if n.startswith('tail'))
 if amount<1e-7:continue
 # Projection onto the imported tail centreline gives continuous arc coordinates.
 best=(1e9,0)
 for j in range(len(lengths)):
  d=control[j+1]-control[j];u=np.clip(np.dot(np.array(v.co)-control[j],d)/(lengths[j]**2),0,1);distance=np.linalg.norm(np.array(v.co)-(control[j]+u*d))
  if distance<best[0]:best=(distance,arc[j]+u*lengths[j])
 t=np.clip(best[1]/total*16-.5,0,14.999);i=int(t);u=smooth(t-i);new={n:w for n,w in old.items() if not n.startswith('tail')};new[tailnames[i]]=amount*(1-u);new[tailnames[i+1]]=amount*u;write(v,new)
# Calibrated IK retains planted feet while the back and shoulder girdle articulate.
leg_specs={}
for side,x in [('L',.61),('R',-.61)]:
 for leg in ['fore','hind']:
  joints=[(x,-1.42,3.02),(x,-1.20,1.68),(x,-1.36,.46),(x,-1.76,.18)] if leg=='fore' else [(x,2.35,3.08),(x,1.80,1.94),(x,2.22,.68),(x,1.82,.18)]
  leg_specs[leg+side]=(joints,leg,side)
source=(root.parent/'wolf-art-rebuild/build.py').read_text();a=source.index('for name,(joints,leg,side) in leg_specs.items():');b=source.index('# Feet push back',a);exec(source[a:b])
for track in list(rig.animation_data.nla_tracks):
 if track.name=='Run':rig.animation_data.nla_tracks.remove(track)
old=bpy.data.actions.get('Run');rig.animation_data.action=None
if old:bpy.data.actions.remove(old)
action=bpy.data.actions.new('Run');rig.animation_data.action=action
def cycle_curve(t,keys):
 t=t%1;i=max(j for j,k in enumerate(keys) if k[0]<=t);extended=[(keys[-1][0]-1,keys[-1][1])]+keys+[(keys[0][0]+1,keys[0][1]),(keys[1][0]+1,keys[1][1])];p0,p1,p2,p3=extended[i:i+4];u=(t-p1[0])/(p2[0]-p1[0]);h=p2[0]-p1[0];m0=(p2[1]-p0[1])/(p2[0]-p0[0]);m1=(p3[1]-p1[1])/(p3[0]-p1[0]);return (2*u**3-3*u*u+1)*p1[1]+(u**3-2*u*u+u)*h*m0+(-2*u**3+3*u*u)*p2[1]+(u**3-u*u)*h*m1
def world_location(name,xyz):rig.pose.bones[name].location=rig.pose.bones[name].bone.matrix_local.to_3x3().inverted()@Vector(xyz)
def swing_y(u,length,contact):
 # End velocities match the planted foot. Brief overshoot allows natural toe-off.
 keys=[(0,.5),( .12,.57),(.36,.23),(.63,-.28),(.88,-.57),(1,-.5)];v=(1-contact)/contact
 i=min(len(keys)-2,next((j for j in range(len(keys)-1) if keys[j][0]<=u<keys[j+1][0]),len(keys)-2));a,ya=keys[i];b,yb=keys[i+1];q=(u-a)/(b-a)
 ma=v if i==0 else 0 if i in [1,len(keys)-2] else (keys[i+1][1]-keys[i-1][1])/(keys[i+1][0]-keys[i-1][0]);mb=v if i==len(keys)-2 else 0 if i==0 or i==len(keys)-3 else (keys[i+2][1]-keys[i][1])/(keys[i+2][0]-keys[i][0])
 return length*((2*q**3-3*q*q+1)*ya+(q**3-2*q*q+q)*(b-a)*ma+(-2*q**3+3*q*q)*yb+(q**3-q*q)*(b-a)*mb)
for f in range(1,50):
 t=(f-1)/48;p=math.tau*t
 for b in rig.pose.bones:b.location=(0,0,0);b.rotation_euler=(0,0,0)
 height=cycle_curve(t,[(0,-.27),(.12,-.59),(.27,-.36),(.43,-.20),(.60,-.58),(.73,-.43),(.88,-.22)])
 pitch=cycle_curve(t,[(0,.02),(.16,.08),(.38,.04),(.62,-.065),(.78,.015),(.92,.04)])
 gather=cycle_curve(t,[(0,1),(.18,.35),(.43,-.45),(.64,0),(.87,1)])
 rig.pose.bones['body'].location.z=height;rig.pose.bones['body'].rotation_euler.x=pitch
 hips_pitch=-.115*gather;chest_pitch=.095*gather-.025*math.sin(p)
 rig.pose.bones['hips'].rotation_euler.x=hips_pitch;rig.pose.bones['hips'].rotation_euler.z=.018*math.sin(p-.2)
 rig.pose.bones['chest'].rotation_euler.x=chest_pitch;rig.pose.bones['chest'].rotation_euler.y=.022*math.sin(p)
 world_location('hips',(0,-.13*gather,.015*gather));world_location('chest',(0,.10*gather,0))
 for j,name in enumerate(['hipsBackB','hipsBackA','chestBackB','chestBackA']):
  rig.pose.bones[name].rotation_euler.x=.025*math.sin(p-.75+j*.32);world_location(name,(0,0,.13*gather*[.4,1,1,.25][j]))
 head_pitch=.025*math.sin(p-.95);desired=-.025-.020*math.exp(-((t-.62)/.09)**2)
 rig.pose.bones['head'].rotation_euler.x=.38+head_pitch;rig.pose.bones['neck'].rotation_euler.x=.38+pitch-chest_pitch+head_pitch-desired
 world_location('neck',(0,0,-.35*(height+.4)))
 rig.pose.bones['head'].rotation_euler.z=.008*math.sin(p-.4)
 for side,start in [('L',.60),('R',.56)]:
  q=math.tau*(t-start);world_location('fore'+side,(0,.09*math.sin(q),-.055*math.cos(q)))
 for j,name in enumerate(['ruffL','ruffR','shoulderFurL','shoulderFurR','foreFurL','foreFurR','hindFurL','hindFurR']):
  for suffix,amplitude,lag in [('',.025,0),('Flow',.055,.45),('Tip',.085,.8)]:rig.pose.bones[name+suffix].rotation_euler.z=amplitude*math.sin(p-j*.3-lag)
 for name,(joints,leg,side) in leg_specs.items():
  start={('hind','L'):.08,('hind','R'):.12,('fore','L'):.60,('fore','R'):.56}[leg,side];u=(t-start)%1;contact=.20;stride=2.2
  if u<contact:q=u/contact;dy=stride*(q-.5);lift=.005;curl=.025*math.cos(math.pi*q)
  else:
   q=(u-contact)/(1-contact);dy=swing_y(q,stride,contact);lift=(.52 if leg=='hind' else .78)*math.sin(math.pi*q)**2;curl=(.32 if leg=='hind' else .42)*math.sin(math.pi*q)**2
  if u>=contact:
   if leg=='fore' and .65<q<.98:dy-=.42*math.sin(math.pi*(q-.65)/.33)**2
   if leg=='hind' and 0<q<.32:dy+=.32*math.sin(math.pi*q/.32)**2
  target=rig.pose.bones[name+'Target'];target.location=target.bone.matrix_local.to_3x3().inverted()@Vector((0,dy,lift));rig.pose.bones[name+'Level'].rotation_euler.x=-curl
 for b in rig.pose.bones:b.keyframe_insert('rotation_euler',frame=f);b.keyframe_insert('location',frame=f)
# 48 samples over one second: correction sampling and skeletal keys share a clock.
scene.render.fps=48;bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.nla.bake(frame_start=1,frame_end=49,step=1,only_selected=False,visual_keying=True,clear_constraints=False,use_current_action=True,bake_types={'POSE'})
# Existing clips were authored at 24 fps. Double their frame indices to retain durations.
for other in bpy.data.actions:
 if other==action:continue
 for curve in other.fcurves:
  for key in curve.keyframe_points:key.co.x=1+(key.co.x-1)*2;key.handle_left.x=1+(key.handle_left.x-1)*2;key.handle_right.x=1+(key.handle_right.x-1)*2
for track in list(rig.animation_data.nla_tracks):rig.animation_data.nla_tracks.remove(track)
for clip in [a for a in bpy.data.actions if any('pose.bones' in f.data_path for f in a.fcurves)]:
 tr=rig.animation_data.nla_tracks.new();tr.name=clip.name;tr.strips.new(clip.name,1,clip);tr.mute=True
for b in rig.pose.bones:
 for c in list(b.constraints):b.constraints.remove(c)
rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_set(1)
(draft/'tail-rig.json').write_text(json.dumps({'bones':tailnames,'points':samples.tolist(),'length':float(total),'joints':16},indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(draft/'run-candidate.blend'))
motion=json.loads((root/'public/motion.json').read_text());motion['Run']['ground_speed']=2.2/.20*.34;(root/'public/motion.json').write_text(json.dumps(motion,indent=2))

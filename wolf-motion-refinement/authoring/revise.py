"""Ten cumulative corrections, preserving approved idle keys and rest anatomy."""
import bpy,bmesh,math,os,json,hashlib,struct,numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.kdtree import KDTree
root=Path(__file__).resolve().parents[1];stage=int(os.environ.get('WOLF_PASS','1'))
review=root/'review'/'drafts';review.mkdir(parents=True,exist_ok=True)
baseline=root.parent/'wolf-animation-viewer'/'authoring'/'wolf.blend';bpy.ops.wm.open_mainfile(filepath=str(baseline))
rig=bpy.data.objects['DivineWolfRig'];coat=bpy.data.objects['Wolf ivory coat'];scene=bpy.context.scene
rest=np.array([tuple(v.co) for v in coat.data.vertices]);rest_hash=hashlib.sha256(rest.astype('<f4').tobytes()).hexdigest()
def action_hash(action):
 return hashlib.sha256(json.dumps([(f.data_path,f.array_index,[(tuple(k.co),k.interpolation) for k in f.keyframe_points]) for f in action.fcurves]).encode()).hexdigest()
idle_hash=action_hash(bpy.data.actions['Idle']);idle_poses={}
rig.animation_data.action=bpy.data.actions['Idle']
for frame in [1,25,49,73]:
 scene.frame_set(frame);mesh=coat.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;idle_poses[frame]=np.array([tuple(v.co) for v in mesh.vertices])
rig.animation_data.action=None
for bone in rig.pose.bones:bone.rotation_mode='XYZ';bone.location=(0,0,0);bone.rotation_euler=(0,0,0)
# The original y=-1 threshold cut through a continuous ankle ornament.
# Rebind the whole low front-leg volume, including swept-back fur, to its limb.
def smoothstep(v):
 t=max(0,min(1,v));return t*t*(3-2*t)
def read_weights(vertex):return {coat.vertex_groups[g.group].name:g.weight for g in vertex.groups}
def set_weights(vertex,weights):
 values=sorted(((n,w) for n,w in weights.items() if w>1e-6),key=lambda a:a[1],reverse=True)[:4];total=sum(w for _,w in values)
 for group_index in [g.group for g in vertex.groups]:coat.vertex_groups[group_index].remove([vertex.index])
 for name,w in values:
  group=coat.vertex_groups.get(name) or coat.vertex_groups.new(name=name);group.add([vertex.index],w/total,'REPLACE')
rebound=0
for vertex in coat.data.vertices:
 x,y,z=vertex.co
 if z>=2.95 or any(n.startswith('tail') and w>.01 for n,w in read_weights(vertex).items()):continue
 side='L' if x>=0 else 'R';attach=smoothstep((2.95-z)/.72)
 lateral=1-(1-smoothstep(abs(x)/.55))*smoothstep((z-1.70)/.65)
 fore=(1-smoothstep((y-.15)/.70))*(1-smoothstep((y+1.0)/1.60)*smoothstep((z-1.75)/.80))
 hind=smoothstep((y-.60)/.65)*(1-(1-smoothstep((y-.60)/1.15))*smoothstep((z-1.75)/.80))
 fore*=attach*lateral;hind*=attach*lateral
 if fore+hind>1:total=fore+hind;fore/=total;hind/=total
 chest=smoothstep((1.60-y)/2.70);old=read_weights(vertex)
 fur={n:w for n,w in old.items() if n in ['foreFur'+side,'hindFur'+side]};fur_total=sum(fur.values());scale=1-fur_total
 weights={'chest':(1-fore-hind)*chest*scale,'hips':(1-fore-hind)*(1-chest)*scale}
 for leg,amount,knee in [('fore',fore,1.68),('hind',hind,1.94)]:
  lower=smoothstep((knee+.25-z)/.56);paw=smoothstep((.64-z)/.36)
  weights[leg+side]=amount*(1-lower)*scale;weights[leg+'Shin'+side]=amount*lower*(1-paw)*scale;weights[leg+'Paw'+side]=amount*lower*paw*scale
 weights.update(fur);set_weights(vertex,weights);rebound+=1
# Close seam-scale discontinuities using neighbouring weights, without moving geometry.
for iteration in range(3):
 weights=[read_weights(v) for v in coat.data.vertices];near=[[] for _ in coat.data.vertices]
 for edge in coat.data.edges:
  a,b=edge.vertices
  if (coat.data.vertices[a].co-coat.data.vertices[b].co).length<.075:near[a].append(b);near[b].append(a)
 for vertex in coat.data.vertices:
  if vertex.co.z>2.80 or not near[vertex.index] or any(n.startswith('tail') and w>.01 for n,w in weights[vertex.index].items()):continue
  mixed={n:w*.76 for n,w in weights[vertex.index].items()}
  for index in near[vertex.index]:
   for n,w in weights[index].items():mixed[n]=mixed.get(n,0)+w*.24/len(near[vertex.index])
  set_weights(vertex,mixed)
for vertex in coat.data.vertices:set_weights(vertex,read_weights(vertex))
fur_names=['ruffL','ruffR','shoulderFurL','shoulderFurR','foreFurL','foreFurR','hindFurL','hindFurR'];extra_fur=[]
# Additional fur joints inherit exactly the parent's idle deformation at zero rotation.
if stage>=9:
 bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
 for name in fur_names:
  parent=rig.data.edit_bones[name];start=parent.head.copy();end=parent.tail.copy();previous=name
  for suffix,t in [('Flow',.45),('Tip',.77)]:
   child=rig.data.edit_bones.new(name+suffix);child.head=start.lerp(end,t);child.tail=end+(end-start)*.12;child.parent=rig.data.edit_bones[previous];previous=child.name;extra_fur.append(child.name)
 bpy.ops.object.mode_set(mode='OBJECT')
 for name in extra_fur:rig.pose.bones[name].rotation_mode='XYZ';coat.vertex_groups.new(name=name)
 for vertex in coat.data.vertices:
  old=read_weights(vertex);new=old.copy()
  for name in fur_names:
   amount=old.get(name,0)
   if not amount:continue
   bone=rig.data.bones[name];d=bone.tail_local-bone.head_local;t=max(0,min(1,(vertex.co-bone.head_local).dot(d)/d.length_squared));q=max(0,min(1.999,t*2));i=int(q);u=smoothstep(q-i);names=[name,name+'Flow',name+'Tip'];new.pop(name,None);new[names[i]]=new.get(names[i],0)+amount*(1-u);new[names[i+1]]=new.get(names[i+1],0)+amount*u
  set_weights(vertex,new)
extra_tail=[]
if stage>=10:
 bm=bmesh.new();bm.from_mesh(coat.data);edges=[e for e in bm.edges if all(v.co.y>2.70 and abs(v.co.x)<.60 for v in e.verts)];bmesh.ops.subdivide_edges(bm,edges=edges,cuts=2,use_grid_fill=True);bm.to_mesh(coat.data);bm.free();coat.data.update()
 # Keep the four approved idle joints intact. Two additional deform controls
 # along EACH segment distribute motion from the base to the very tip.
 bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
 for base in ['tail','tailMid','tailTip','tailEnd']:
  parent=rig.data.edit_bones[base];start=parent.head.copy();end=parent.tail.copy();previous=base
  for suffix,t in [('Flow',.33),('Silk',.67)]:
   child=rig.data.edit_bones.new(base+suffix);child.head=start.lerp(end,t);child.tail=end+(end-start)*.05;child.parent=rig.data.edit_bones[previous];previous=child.name;extra_tail.append(child.name)
 bpy.ops.object.mode_set(mode='OBJECT')
 for name in extra_tail:rig.pose.bones[name].rotation_mode='XYZ';coat.vertex_groups.new(name=name)
 for vertex in coat.data.vertices:
  old=read_weights(vertex);new=old.copy()
  for base in ['tail','tailMid','tailTip','tailEnd']:
   amount=old.get(base,0)
   if not amount:continue
   bone=rig.data.bones[base];d=bone.tail_local-bone.head_local;t=max(0,min(1,(vertex.co-bone.head_local).dot(d)/d.length_squared));q=min(1.999,t*2);i=int(q);u=smoothstep(q-i);names=[base,base+'Flow',base+'Silk'];new.pop(base,None);new[names[i]]=new.get(names[i],0)+amount*(1-u);new[names[i+1]]=new.get(names[i+1],0)+amount*u
  set_weights(vertex,new)
# Distributed back controls retain the approved root hierarchy and idle bindings.
spine_names=[]
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for base in ['chest','hips']:
 for suffix,y in [('BackA',-.45 if base=='chest' else .65),('BackB',.30 if base=='chest' else 1.45)]:
  name=base+suffix;child=rig.data.edit_bones.new(name);child.head=(0,y,3.0);child.tail=(0,y-.45,3.04);child.parent=rig.data.edit_bones[base];spine_names.append(name)
bpy.ops.object.mode_set(mode='OBJECT')
for name in spine_names:rig.pose.bones[name].rotation_mode='XYZ';coat.vertex_groups.new(name=name)
for vertex in coat.data.vertices:
 x,y,z=vertex.co;old=read_weights(vertex);new=old.copy()
 for base in ['chest','hips']:
  amount=old.get(base,0)*smoothstep((z-2.10)/.85)*(1-smoothstep((abs(x)-.65)/.5))
  if not amount:continue
  centre=.0 if base=='chest' else 1.05;t=smoothstep((y-centre+.45)/.90);new[base]=new.get(base,0)-amount;new[base+'BackA']=new.get(base+'BackA',0)+amount*(1-t);new[base+'BackB']=new.get(base+'BackB',0)+amount*t
 set_weights(vertex,new)
# A jaw hinge opens the existing lower lip; it is not a floating mouth overlay.
if stage>=7:
 bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT');jaw=rig.data.edit_bones.new('jaw');jaw.head=(0,-3.36,4.09);jaw.tail=(0,-3.93,3.99);jaw.parent=rig.data.edit_bones['head'];bpy.ops.object.mode_set(mode='OBJECT');rig.pose.bones['jaw'].rotation_mode='XYZ';coat.vertex_groups.new(name='jaw')
 jaw_count=0
 for vertex in coat.data.vertices:
  x,y,z=vertex.co
  if y<-3.43 and z<4.12 and not (y<-4.01 and z>4.01):
   amount=smoothstep((-y-3.40)/.24)*smoothstep((4.14-z)/.13);old=read_weights(vertex);old={n:w*(1-amount) for n,w in old.items()};old['jaw']=amount;set_weights(vertex,old);jaw_count+=1
leg_specs={}
for side,x in [('L',.61),('R',-.61)]:
 for leg in ['fore','hind']:
  joints=[(x,-1.42,3.02),(x,-1.20,1.68),(x,-1.36,.46),(x,-1.76,.18)] if leg=='fore' else [(x,2.35,3.08),(x,1.80,1.94),(x,2.22,.68),(x,1.82,.18)]
  leg_specs[leg+side]=(joints,leg,side)
source=(root.parent/'wolf-art-rebuild'/'build.py').read_text();a=source.index('for name,(joints,leg,side) in leg_specs.items():');b=source.index('# Feet push back',a);exec(source[a:b])
def remove_action(name):
 rig.animation_data.action=None
 for track in list(rig.animation_data.nla_tracks):
  if track.name==name:rig.animation_data.nla_tracks.remove(track)
 old=bpy.data.actions.get(name)
 if old:bpy.data.actions.remove(old)
 action=bpy.data.actions.new(name);rig.animation_data.action=action;return action

def reset_pose():
 for bone in rig.pose.bones:bone.rotation_mode='XYZ';bone.location=(0,0,0);bone.rotation_euler=(0,0,0)

def secondary(phase,speed=1):
 names=['tail','tailMid','tailTip','tailEnd']+extra_tail
 for i,name in enumerate(names):
  bone=rig.pose.bones[name]
  if name in extra_tail:
   j=extra_tail.index(name);amplitude=(.022+.006*j)*speed;bone.rotation_euler=(amplitude*math.sin(phase-j*.48),amplitude*.3*math.sin(phase-j*.48-.4),amplitude*.8*math.sin(phase-j*.48-1))
  else:bone.rotation_euler.x=[-1.08,-.20,-.08,.10][i]+.04*math.sin(phase-i*.65);bone.rotation_euler.z=.045*math.sin(phase-i*.7)
 for j,name in enumerate(spine_names):
  rig.pose.bones[name].rotation_euler.x=.012*speed*math.sin(phase-j*.45)
 for i,name in enumerate(fur_names+extra_fur):
  bone=rig.pose.bones[name];tip=name.endswith('Tip');amount=(.10 if tip else .075 if name.endswith('Flow') else .038)*speed
  bone.rotation_euler=(amount*.55*math.sin(phase-i*.65),amount*.35*math.sin(phase-i*.65-.4),amount*math.sin(phase-i*.65-.9))

def target_leg(name,dy=0,lift=0,curl=0,spread=0):
 bone=rig.pose.bones[name+'Target'];bone.location=bone.bone.matrix_local.to_3x3().inverted()@Vector((spread,dy,lift));rig.pose.bones[name+'Level'].rotation_euler.x=-curl

def key_pose(frame):
 for bone in rig.pose.bones:
  bone.keyframe_insert('rotation_euler',frame=frame);bone.keyframe_insert('location',frame=frame)

def bake(action,duration):
 bpy.context.view_layer.objects.active=rig;rig.select_set(True);bpy.ops.nla.bake(frame_start=1,frame_end=duration+1,step=1,only_selected=False,visual_keying=True,clear_constraints=False,use_current_action=True,bake_types={'POSE'})
 track=rig.animation_data.nla_tracks.new();track.name=action.name;track.strips.new(action.name,1,action);track.mute=True
motion=json.loads((root.parent/'wolf-animation-viewer'/'public'/'motion.json').read_text())
offsets={'Walk':{('fore','L'):0,('hind','R'):.25,('fore','R'):.5,('hind','L'):.75},'Run':{('hind','L'):0,('hind','R'):.09,('fore','L'):.45,('fore','R'):.54}}
for name,duration,contact,length in [('Walk',36,.64,2.0),('Run',24,.40,2.70)]:
 action=remove_action(name);running=name=='Run'
 for f in range(1,duration+2):
  cycle=(f-1)/duration;phase=cycle*math.tau;reset_pose()
  rig.pose.bones['body'].location.z=(-.52 if running and stage>=2 else -.56 if running else -.38)+(.06 if running else .035)*math.sin(phase*(1 if running else 2))
  rig.pose.bones['body'].rotation_euler.x=(.025 if running and stage>=2 else .035 if running else .012)*math.sin(phase*(1 if running else 2)-.4)
  rig.pose.bones['chest'].rotation_euler.x=(.090 if running and stage>=2 else .12 if running else .030)*math.sin(phase-.35);rig.pose.bones['hips'].rotation_euler.x=(-.075 if running and stage>=2 else -.10 if running else -.022)*math.sin(phase-.55)
  rig.pose.bones['chest'].rotation_euler.y=(.028 if running else .05)*math.sin(phase);rig.pose.bones['hips'].rotation_euler.y=-(.020 if running else .04)*math.sin(phase-.25)
  rig.pose.bones['neck'].rotation_euler.x=-(.060 if running and stage>=2 else .075 if running else .021)*math.sin(phase-.35);rig.pose.bones['head'].rotation_euler.x=.013*math.sin(phase-.7)
  secondary(phase,1.1 if running else .75)
  if running:
   for i,bone_name in enumerate(['tail','tailMid','tailTip','tailEnd']):rig.pose.bones[bone_name].rotation_euler.x=[-.10,-.19,-.24,-.10][i]+.065*math.sin(phase-i*.65-.4)
  for leg_name,(joints,leg,side) in leg_specs.items():
   t=(cycle+offsets[name][leg,side])%1
   if t<contact:
    u=t/contact;dy=-length/2+length*u;curl=.055*math.cos(math.pi*u)*max(0,1-abs(u-.5)*.8);lift=abs(curl)*.16
   else:
    u=(t-contact)/(1-contact);v=(1-contact)/contact;dy=length*(.5+v*u-(1+v)*(10*u**3-15*u**4+6*u**5));lift=(.58 if running and stage>=2 else .78 if running else .29 if stage>=3 else .56)*math.sin(math.pi*u)**2;curl=(.36 if running else .21 if stage>=3 else .34)*math.sin(math.pi*u)**2
   target_leg(leg_name,dy,lift,curl)
  key_pose(f)
 bake(action,duration);motion[name]['ground_speed']=length/contact/(duration/24)*.34
# Pose functions let the complete jump and individual phases share the same mechanics.
def jump_pose(t):
 reset_pose();u=max(0,min(1,(t-.17)/.63));height=2.7*4*u*(1-u) if .17<t<.80 else 0
 squat=.22*math.sin(math.pi*t/.17)**2 if t<.17 else .26*math.sin(math.pi*(t-.80)/.20)**2 if t>.80 else 0
 base=-.38*smoothstep(t/.12)*(1-smoothstep((t-.87)/.13))
 rig.pose.bones['body'].location.z=base+height-squat
 rig.pose.bones['body'].rotation_euler.x=.085*math.sin(math.pi*u)+.075*math.sin(math.pi*u*2)
 lead=math.exp(-((t-.15)/.055)**2);landing=math.exp(-((t-.83)/.08)**2)
 rig.pose.bones['neck'].rotation_euler.x=-.23*lead+.075*landing;rig.pose.bones['head'].rotation_euler.x=.07*lead-.035*landing
 rig.pose.bones['chest'].location=rig.pose.bones['chest'].bone.matrix_local.to_3x3().inverted()@Vector((0,0,.32*lead-.09*landing));rig.pose.bones['chest'].rotation_euler.x=-.095*lead+.045*landing
 rig.pose.bones['hips'].location.z=-.055*lead;rig.pose.bones['hips'].rotation_euler.x=.05*math.sin(math.pi*u)
 secondary(t*math.tau,.9)
 for name,(joints,leg,side) in leg_specs.items():
  tuck=.30*math.sin(math.pi*u)*(1-smoothstep((u-.62)/.25)) if leg=='fore' else .17*math.sin(math.pi*u)**2
  front_lead=.31*lead if leg=='fore' else 0
  rear_lag=.065*math.sin(math.pi*u) if leg=='hind' else 0
  reach=(.12-.38*smoothstep((u-.50)/.40))*math.sin(math.pi*u) if leg=='fore' else .17*math.sin(math.pi*u*2)
  target_leg(name,reach,height+tuck+front_lead+rear_lag,.12*math.sin(math.pi*u))
if stage>=4:
 action=remove_action('Jump');duration=46
 for f in range(1,duration+2):jump_pose((f-1)/duration);key_pose(f)
 bake(action,duration)
if stage>=5:
 for name,duration,start,end in [('JumpRise',22,0,.485),('JumpFall',22,.485,1),('Land',12,.80,1)]:
  action=remove_action(name)
  for f in range(1,duration+2):jump_pose(start+(end-start)*(f-1)/duration);key_pose(f)
  bake(action,duration)
if stage>=6:
 action=remove_action('AirStrike');duration=34
 for f in range(1,duration+2):
  t=(f-1)/duration;reset_pose();u=min(1,t/.70);height=1.85*(1-u)**1.35;accent=math.sin(math.pi*u)*(.55+.45*u);impact=math.exp(-((t-.72)/.065)**2)
  rig.pose.bones['body'].location.z=-.38*(1-smoothstep((t-.84)/.16))+height-.18*impact;rig.pose.bones['body'].rotation_euler.x=-.10*accent
  rig.pose.bones['chest'].rotation_euler.x=.10*accent;rig.pose.bones['neck'].rotation_euler.x=.34*accent+.14*impact;rig.pose.bones['head'].rotation_euler.x=-.23*accent-.04*impact
  secondary(t*math.tau,1.15)
  for name,(joints,leg,side) in leg_specs.items():
   lift=max(0,height+(.08 if leg=='hind' else -.09)*accent);reach=(-.28 if leg=='fore' else .12)*accent
   target_leg(name,reach,lift,.10*accent)
  key_pose(f)
 bake(action,duration)
if stage>=7:
 action=remove_action('Bark');duration=23
 for f in range(1,duration+2):
  t=(f-1)/duration;reset_pose();hold=math.sin(math.pi*t)**.8;pulse=math.exp(-((t-.46)/.095)**2)
  rig.pose.bones['body'].location.z=-.66*hold;rig.pose.bones['body'].location.y=.10*hold;rig.pose.bones['chest'].location.z=-.24*hold;rig.pose.bones['hips'].location.z=.04*hold
  rig.pose.bones['neck'].rotation_euler.x=-.12*hold-.05*pulse;rig.pose.bones['head'].rotation_euler.x=-.025*hold;rig.pose.bones['jaw'].rotation_euler.x=.26*pulse
  secondary(t*math.tau,.8)
  for name,(joints,leg,side) in leg_specs.items():target_leg(name,-.10*hold if leg=='fore' else .03*hold,0,0,(.20 if side=='L' else -.20)*hold)
  key_pose(f)
 bake(action,duration)
for bone in rig.pose.bones:
 for constraint in list(bone.constraints):bone.constraints.remove(constraint)
# Correct only verified high-strain seams, preserving approved gait timing.
repair_log=[]
for iteration in range(8):
 rig.animation_data.action=bpy.data.actions['Run'];suspects=set()
 rest_positions=[v.co.copy() for v in coat.data.vertices]
 for sample in [(name,frame) for name in ['Run','Jump','Bark'] for frame in np.linspace(*bpy.data.actions[name].frame_range,25)]:
  name,frame=sample;rig.animation_data.action=bpy.data.actions[name];scene.frame_set(int(frame),subframe=float(frame%1));mesh=coat.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
  for edge in coat.data.edges:
   a,b=edge.vertices;length=(rest_positions[a]-rest_positions[b]).length
   if length>.015 and (mesh.vertices[a].co-mesh.vertices[b].co).length/length>2.65:suspects.add((int(a),int(b)))
 weights=[read_weights(v) for v in coat.data.vertices];neighbours={}
 for a,b in suspects:neighbours.setdefault(a,[]).append(b);neighbours.setdefault(b,[]).append(a)
 for a,linked in neighbours.items():
  mixed={n:w*.85 for n,w in weights[a].items()}
  for b in linked:
   for n,w in weights[b].items():mixed[n]=mixed.get(n,0)+w*.15/len(linked)
  set_weights(coat.data.vertices[a],mixed)
 repair_log.append({'iteration':iteration+1,'high_strain_edges':len(suspects)})
print('SEAM_REPAIR',json.dumps(repair_log),flush=True)
assert idle_hash==action_hash(bpy.data.actions['Idle']),'Approved idle keys changed'
# Strong deformation checks compare physical mesh edges, not only bone values.
rest_new=[v.co.copy() for v in coat.data.vertices];stretch={}
for name in ['Run','Walk','Jump','AirStrike','Bark']:
 if not bpy.data.actions.get(name):continue
 rig.animation_data.action=bpy.data.actions[name];start,end=rig.animation_data.action.frame_range;max_ratio=0;bad_count=0;worst=[]
 for f in np.linspace(start,end,13):
  scene.frame_set(int(f),subframe=float(f%1));mesh=coat.evaluated_get(bpy.context.evaluated_depsgraph_get()).data
  for edge in coat.data.edges:
   a,b=edge.vertices;length=(rest_new[a]-rest_new[b]).length
   if length<.015:continue
   ratio=(mesh.vertices[a].co-mesh.vertices[b].co).length/length
   max_ratio=max(max_ratio,ratio)
   if ratio>3:bad_count+=1
 stretch[name]={'max_edge_stretch':max_ratio,'edge_spikes_over_3x':bad_count}
# Verify how little the untouched idle is affected by repairing incorrect bindings.
kd=KDTree(len(coat.data.vertices))
for vertex in coat.data.vertices:kd.insert(vertex.co,vertex.index)
kd.balance();mapping=[kd.find(Vector(v))[1] for v in rest];idle_delta=0
rig.animation_data.action=bpy.data.actions['Idle']
for f,old in idle_poses.items():
 scene.frame_set(f);mesh=coat.evaluated_get(bpy.context.evaluated_depsgraph_get()).data;new=np.array([tuple(mesh.vertices[i].co) for i in mapping]);idle_delta=max(idle_delta,float(np.max(np.linalg.norm(new-old,axis=1))))
if stage>=8:exec(compile((root/'authoring'/'paint.py').read_text(),str(root/'authoring'/'paint.py'),'exec'))
rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);coat.select_set(True);bpy.context.view_layer.objects.active=rig
if stage==1:bpy.ops.wm.save_as_mainfile(filepath='/tmp/wolf-polish-weight-study.blend')
path=review/f'pass-{stage:02}.glb';bpy.ops.export_scene.gltf(filepath=str(path),use_selection=True,export_animations=True,export_nla_strips=True,export_anim_slide_to_zero=True)
exec(compile((root/'authoring'/'idle_binding.py').read_text(),str(root/'authoring'/'idle_binding.py'),'exec'));embed_idle_binding(path,root.parent/'wolf-animation-viewer'/'public'/'models'/'wolf.glb')
scene.cycles.samples=16;scene.render.resolution_x=900;scene.render.resolution_y=650;scene.camera.location=(13,.2,5.4);scene.camera.rotation_euler=(Vector((0,.1,2.65))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=10.5
rig.animation_data.action=bpy.data.actions['Run'];scene.frame_set(13);scene.render.filepath=str(review/f'pass-{stage:02}.png');bpy.ops.render.render(write_still=True)
record={'pass':stage,'asset_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'original_rest_mesh_sha256':rest_hash,'rebound_vertices':rebound,'idle_animation_hash':idle_hash,'idle_change_before_preserved_viewer_bindings_metres':idle_delta*.34,'viewer_idle_bindings':'original approved weights embedded' ,'stretch':stretch,'extra_fur_joints':len(extra_fur),'extra_tail_joints':len(extra_tail)}
(review/f'pass-{stage:02}.json').write_text(json.dumps(record,indent=2));print('PASS_RESULT',json.dumps(record),flush=True)
if stage==10:
 import shutil;shutil.copyfile(path,root/'public'/'models'/'wolf.glb');rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(root/'authoring'/'wolf.blend'));(root/'public'/'motion.json').write_text(json.dumps(motion,indent=2))

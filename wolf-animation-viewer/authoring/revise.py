"""Ten cumulative, exported animation reviews. Approved rest-mesh anatomy is untouched."""
import bpy,bmesh,math,os,json,hashlib
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];stage=int(os.environ.get('WOLF_PASS','1'))
review=root/'review'/'drafts';review.mkdir(parents=True,exist_ok=True)
baseline=root/'authoring'/'baseline.blend'
if not baseline.exists():baseline=root.parent/'wolf-art-rebuild'/'wolf.blend'
bpy.ops.wm.open_mainfile(filepath=str(baseline))
rig=bpy.data.objects['DivineWolfRig'];coat=bpy.data.objects['Wolf ivory coat'];scene=bpy.context.scene
import struct
rest_hash=hashlib.sha256(b''.join(struct.pack('<fff',*v.co) for v in coat.data.vertices)).hexdigest()
rig.animation_data.action=None
for b in rig.pose.bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0);b.location=(0,0,0)
# Four deforming tail joints distribute the bend; root, body shape and UVs stay fixed.
if stage>=6:
 bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
 chain=[('tail',(0,2.55,3.15),(0,3.15,3.23),'hips'),('tailMid',(0,3.15,3.23),(0,3.70,3.58),'tail'),('tailTip',(0,3.70,3.58),(0,4.12,4.02),'tailMid'),('tailEnd',(0,4.12,4.02),(0,4.24,4.29),'tailTip')]
 for name,start,end,parent in chain:
  bone=rig.data.edit_bones.get(name) or rig.data.edit_bones.new(name);bone.head=start;bone.tail=end;bone.parent=rig.data.edit_bones[parent]
 bpy.ops.object.mode_set(mode='OBJECT')
 for pose_bone in rig.pose.bones:pose_bone.rotation_mode='XYZ'
 for n,_,_,_ in chain:
  if not coat.vertex_groups.get(n):coat.vertex_groups.new(name=n)
 for v in coat.data.vertices:
  x,y,z=v.co
  if y<2.61 or z<2.55 or abs(x)>.62:continue
  fade=max(0,min(1,(y-2.61)/.42));t=max(0,min(2.999,(y-2.70)/1.50*3))
  index=int(t);blend=t-index
  for assignment in list(v.groups):coat.vertex_groups[assignment.group].remove([v.index])
  weights={'hips':1-fade,chain[index][0]:fade*(1-blend),chain[index+1][0]:fade*blend}
  for n,w in weights.items():
   if w>0:coat.vertex_groups[n].add([v.index],w,'REPLACE')
leg_specs={}
for side,x in [('L',.61),('R',-.61)]:
 for leg in ['fore','hind']:
  joints=[(x,-1.42,3.02),(x,-1.20,1.68),(x,-1.36,.46),(x,-1.76,.18)] if leg=='fore' else [(x,2.35,3.08),(x,1.80,1.94),(x,2.22,.68),(x,1.82,.18)]
  leg_specs[leg+side]=(joints,leg,side)
# Restore evaluated IK. The exported result is ordinary per-joint animation.
source=(root.parents[0]/'wolf-art-rebuild'/'build.py').read_text();a=source.index('for name,(joints,leg,side) in leg_specs.items():');b=source.index('# Feet push back',a);exec(source[a:b])
metrics={};periods={'Idle':96,'Walk':36,'Run':24};stance={'Walk':.64,'Run':.40};stride={'Walk':2.0,'Run':2.70}
walk_offsets={('fore','L'):0,('hind','R'):.25,('fore','R'):.5,('hind','L'):.75}
run_offsets={('hind','L'):0,('hind','R'):.09,('fore','L'):.45,('fore','R'):.54}
fur_names=['ruffL','ruffR','shoulderFurL','shoulderFurR','foreFurL','foreFurR','hindFurL','hindFurR']
for clip,duration in periods.items():
 for track in list(rig.animation_data.nla_tracks):
  if track.name==clip:rig.animation_data.nla_tracks.remove(track)
 old=bpy.data.actions.get(clip)
 if old:bpy.data.actions.remove(old)
 action=bpy.data.actions.new(clip);rig.animation_data.action=action
 for f in range(1,duration+2):
  phase=(f-1)/duration*math.tau;cycle=(f-1)/duration
  for bone in rig.pose.bones:bone.rotation_euler=(0,0,0);bone.location=(0,0,0)
  running=clip=='Run';walking=clip=='Walk';moving=running or walking
  rig.pose.bones['body'].location.z=(-.56 if running else -.38)+(.065 if running else .035)*math.sin(phase*(1 if running else 2)) if moving else .010*math.sin(phase)
  if stage>=3:
   rig.pose.bones['body'].rotation_euler.x=(.035 if running else .012)*math.sin(phase*(1 if running else 2)-.4)
   rig.pose.bones['chest'].rotation_euler.x=(.12 if running else .030)*math.sin(phase-.35)
   rig.pose.bones['hips'].rotation_euler.x=(-.10 if running else -.022)*math.sin(phase-.55)
   rig.pose.bones['chest'].rotation_euler.y=(.032 if running else .050)*math.sin(phase)
   rig.pose.bones['hips'].rotation_euler.y=-(.023 if running else .040)*math.sin(phase-.25)
   rig.pose.bones['neck'].rotation_euler.x=-(.075 if running else .021)*math.sin(phase-.35)
   rig.pose.bones['head'].rotation_euler.x=.013*math.sin(phase-.7)
  tail_angles=[-1.62,-.30,.12,.13] if stage>=6 and not moving else [-1.08,-.20,-.08,.10] if stage>=7 and walking else [-.10,-.19,-.24,-.10] if stage>=8 and running else [-.48,-.12,0,0] if walking else [.08,-.28,0,0] if running else [-.95,-.32,0,0]
  names=['tail','tailMid','tailTip','tailEnd'] if stage>=6 else ['tail','tailTip']
  for i,name in enumerate(names):
   bone=rig.pose.bones[name];wind=.020 if not moving else .043 if walking else .075
   bone.rotation_euler.x=tail_angles[i]+wind*math.sin(phase-i*.65-.4)
   bone.rotation_euler.z=(.022 if not moving else .048 if walking else .065)*math.sin(phase-i*.75-.6)
  for i,name in enumerate(fur_names):
   bone=rig.pose.bones[name];lag=i*.6
   amount=.028 if not moving else .044 if walking else .065
   bone.rotation_euler=(amount*.6*math.sin(phase-lag),amount*.4*math.sin(phase-lag-.5),amount*math.sin(phase-lag-1.1))
  for name,(joints,leg,side) in leg_specs.items():
   if not moving:continue
   t=(cycle+(run_offsets if running and stage>=4 else walk_offsets)[leg,side])%1
   contact=stance[clip];length=stride[clip]
   if t<contact:
    u=t/contact;dy=-length/2+length*u;lift=0;curl=0
    if stage>=2:
     curl=.07*math.cos(math.pi*u)*max(0,1-abs(u-.5)*.8)
     lift=abs(curl)*.16
   else:
    u=(t-contact)/(1-contact);v=(1-contact)/contact
    dy=length*(.5+v*u-(1+v)*(10*u**3-15*u**4+6*u**5))
    lift=(.56 if walking else .78)*math.sin(math.pi*u)**(2 if stage>=5 else 3)
    curl=(.34 if walking else .48)*math.sin(math.pi*u)**2
   target=rig.pose.bones[name+'Target'];target.location=target.bone.matrix_local.to_3x3().inverted()@Vector((0,dy,lift));rig.pose.bones[name+'Level'].rotation_euler.x=-curl
  for bone in rig.pose.bones:bone.keyframe_insert('rotation_euler',frame=f);bone.keyframe_insert('location',frame=f)
 bpy.context.view_layer.objects.active=rig;rig.select_set(True)
 bpy.ops.nla.bake(frame_start=1,frame_end=duration+1,step=1,only_selected=False,visual_keying=True,clear_constraints=False,use_current_action=True,bake_types={'POSE'})
 track=rig.animation_data.nla_tracks.new();track.name=clip;track.strips.new(clip,1,action);track.mute=True
 # Verify planted ankle trajectories relative to a ground travelling at matching speed.
 contact_error=0;slip_error=0;previous={};bounds=[]
 for f in range(1,duration+1):
  scene.frame_set(f);bpy.context.view_layer.update();cycle=(f-1)/duration
  for name,(joints,leg,side) in leg_specs.items():
   if not moving:continue
   t=(cycle+(run_offsets if running and stage>=4 else walk_offsets)[leg,side])%1
   point=rig.pose.bones[leg+'Paw'+side].head.copy()
   if .10<t<stance[clip]-.05:
    contact_error=max(contact_error,abs(point.z-joints[2][2]))
    if name in previous:
     old_f,old=previous[name]
     if f==old_f+1:slip_error=max(slip_error,abs((point.y-old.y)-stride[clip]/stance[clip]/duration))
    previous[name]=(f,point)
   else:previous.pop(name,None)
  bounds.append(rig.pose.bones['head'].matrix.translation.z)
 metrics[clip]={'duration':duration/24,'ground_speed':(stride[clip]/stance[clip]/(duration/24)*.34 if moving else 0),'contact_error':contact_error,'slip_error_per_frame':slip_error,'head_motion':max(bounds)-min(bounds)}
# A complete jump arc keeps articulated legs open rather than folding into a ball.
if stage>=5:
 duration=42;action=bpy.data.actions.new('Jump');rig.animation_data.action=action
 for f in range(1,duration+2):
  t=(f-1)/duration
  flight=max(0,min(1,(t-.14)/.67));height=3.2*4*flight*(1-flight) if .14<t<.81 else 0
  compression=.17*math.sin(math.pi*t/.14)**2 if t<.14 else .22*math.sin(math.pi*(t-.81)/.19)**2 if t>.81 else 0
  for bone in rig.pose.bones:bone.rotation_euler=(0,0,0);bone.location=(0,0,0)
  rig.pose.bones['body'].location.z=-.38+height-compression
  rig.pose.bones['body'].rotation_euler.x=.045*math.sin(flight*math.tau)
  rig.pose.bones['neck'].rotation_euler.x=-.05*math.sin(flight*math.pi)
  for i,name in enumerate(fur_names):
   bone=rig.pose.bones[name];bone.rotation_euler=(.025*math.sin(t*math.tau-i*.6),.020*math.sin(t*math.tau-i*.6-.5),.050*math.sin(t*math.tau-i*.6-1.1))
  for name,(joints,leg,side) in leg_specs.items():
   tuck=.24*math.sin(math.pi*flight)**2 if leg=='fore' else .18*math.sin(math.pi*flight)**2
   reach=(-.12 if leg=='fore' else .10)*math.sin(math.pi*flight*2)
   target=rig.pose.bones[name+'Target'];target.location=target.bone.matrix_local.to_3x3().inverted()@Vector((0,reach,height+tuck))
   rig.pose.bones[name+'Level'].rotation_euler.x=-.15*math.sin(math.pi*flight)
  for bone in rig.pose.bones:bone.keyframe_insert('rotation_euler',frame=f);bone.keyframe_insert('location',frame=f)
 bpy.context.view_layer.objects.active=rig;bpy.ops.nla.bake(frame_start=1,frame_end=duration+1,step=1,only_selected=False,visual_keying=True,clear_constraints=False,use_current_action=True,bake_types={'POSE'})
 track=rig.animation_data.nla_tracks.new();track.name='Jump';track.strips.new('Jump',1,action);track.mute=True
for bone in rig.pose.bones:
 for constraint in list(bone.constraints):bone.constraints.remove(constraint)
# Existing attacks/jumps receive the same gravity-led tail and continuous fur, preserving action poses.
if stage>=6:
 for action in list(bpy.data.actions):
  if action.name in periods:continue
  rig.animation_data.action=action;start,end=action.frame_range;duration=max(1,end-start)
  for f in range(int(start),int(end)+1):
   phase=(f-start)/duration*math.tau
   for i,name in enumerate(['tail','tailMid','tailTip','tailEnd']):
    bone=rig.pose.bones[name];bone.rotation_euler.x=(-.85 if i==0 else -.12)+.045*math.sin(phase-i*.7);bone.keyframe_insert('rotation_euler',frame=f)
# Eye and vermilion edits are rebaked in passes 9 and 10, onto the unchanged UV skin.
if stage>=9:
 text=(root/'authoring'/'paint.py').read_text();exec(compile(text,str(root/'authoring'/'paint.py'),'exec'))
rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);coat.select_set(True);bpy.context.view_layer.objects.active=rig
asset_path=review/f'pass-{stage:02}.glb'
bpy.ops.export_scene.gltf(filepath=str(asset_path),use_selection=True,export_animations=True,export_nla_strips=True,export_anim_slide_to_zero=True)
scene.cycles.samples=16;scene.render.resolution_x=900;scene.render.resolution_y=650;scene.camera.location=(13,.2,5.4);scene.camera.rotation_euler=(Vector((0,.1,2.65))-scene.camera.location).to_track_quat('-Z','Y').to_euler();scene.camera.data.ortho_scale=10.5
rig.animation_data.action=bpy.data.actions['Walk'];scene.frame_set(12);scene.render.filepath=str(review/f'pass-{stage:02}.png');bpy.ops.render.render(write_still=True)
record={'pass':stage,'rest_mesh_sha256':rest_hash,'asset_sha256':hashlib.sha256(asset_path.read_bytes()).hexdigest(),'metrics':metrics}
(review/f'pass-{stage:02}.json').write_text(json.dumps(record,indent=2))
print('PASS_RESULT',json.dumps(record),flush=True)
if stage==10:
 import shutil;shutil.copyfile(asset_path,root/'public'/'models'/'wolf.glb');rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(root/'authoring'/'wolf.blend'))
 (root/'public'/'motion.json').write_text(json.dumps(metrics,indent=2))

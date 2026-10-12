"""Adapt the attributed artist-made canine and retain its authored locomotion.
Source/credits: THIRD_PARTY.md. Blender 4.3.2. No commercial game assets.
"""
import bpy, math, os, hashlib
from mathutils import Vector, Quaternion, Matrix
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
source=os.path.join(os.getcwd(),'tools/source/fox-reference.glb')
EXPECTED='d97044e701822bac5a62696459b27d7b375aada5de8574ed4362edbba94771f7'
assert hashlib.sha256(open(source,'rb').read()).hexdigest()==EXPECTED,'Source artifact checksum mismatch'
bpy.ops.import_scene.gltf(filepath=source)
for o in list(bpy.data.objects):
 if o.name.startswith('Icosphere'):bpy.data.objects.remove(o,do_unlink=True)
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');fox=next(o for o in bpy.data.objects if o.type=='MESH')
rig.name='SunwardWolfRig';fox.name='PaintedWolf'
# Refine the fox source into the wolf interpretation without changing its skin bind.
# The legs and skeleton are preserved, so the artist's planted locomotion remains intact.
for v in fox.data.vertices:
 x,y,z=v.co
 if y>43: # reduce the very large fox tail, keeping a tapered flowing shape
  v.co.x*=.72
  centre=52-(y-40)*.47
  v.co.z=centre+(z-centre)*.73
 elif -25<y<30 and z>34: # wider chest, tucked abdomen, level upper silhouette
  v.co.x*=1.10
  tuck=math.exp(-((y-10)/16)**2)*math.exp(-((z-35)/11)**2)*5
  v.co.z+=tuck
 if y<-25 and z>70:v.co.z=70+(z-70)*.86 # pointed, slightly shorter ears
fox.data.update()
# Ensure shading is clean; low-poly planes are intentional, not overlapping primitives.
for p in fox.data.polygons:p.use_smooth=False
# Preserve imported animations. Rename Survey to Idle and export each NLA track once.
clips={}
for action in list(bpy.data.actions):
 name=action.name.split('_')[0];action.name='Idle' if name=='Survey' else name;clips[action.name]=action
rig.animation_data_create()
for track in list(rig.animation_data.nla_tracks):rig.animation_data.nla_tracks.remove(track)
rig.animation_data.action=None
fps=30;bpy.context.scene.render.fps=fps
# Imported frames use 24 FPS. Rescale their keys to 30 FPS so cycle durations stay exact.
for action in clips.values():
 for fc in action.fcurves:
  for kp in fc.keyframe_points:kp.co.x*=30/24;kp.handle_left.x*=30/24;kp.handle_right.x*=30/24
# Additional deliberate whole-body clips are authored as key poses then sampled by glTF.
B=lambda name:next(pb for pb in rig.pose.bones if name in pb.name)
hip=B('Hip');back=B('Spine01');chest=B('Spine02');neck=B('Neck');head=B('Head')
def reset():
 for pb in rig.pose.bones:pb.rotation_mode='QUATERNION';pb.rotation_quaternion=(1,0,0,0);pb.location=(0,0,0);pb.scale=(1,1,1)
def global_rotate(pb,axis,angle):
 # Convert an armature-space bend to the bone's actual local axes.
 basis=pb.bone.matrix_local.to_quaternion();local=basis.inverted()@Vector(axis);pb.rotation_quaternion=Quaternion(local,angle)
def pose(name,t):
 reset();envelope=math.sin(t*math.pi)
 if name in ['Thrust','Sweep','Finish']:
  contact={'Thrust':.40,'Sweep':.46,'Finish':.49}[name];releaseStart=contact-.17
  smooth=lambda a,b,x:(lambda u:u*u*(3-2*u))(max(0,min(1,(x-a)/(b-a))))
  wind=math.sin(min(t/releaseStart,1)*math.pi/2)*(1-smooth(releaseStart,contact,t))
  drive=smooth(releaseStart,contact,t)*(1-smooth(contact+.14,1,t))
  if name=='Sweep':
   yaw=math.sin((t-.15)*math.pi*2)*.65*envelope
   global_rotate(hip,(0,0,1),yaw*.15);global_rotate(back,(0,0,1),yaw*.22);global_rotate(chest,(0,0,1),yaw*.36);global_rotate(neck,(0,0,1),yaw*.28);global_rotate(head,(0,0,1),yaw*.14)
   global_rotate(chest,(0,0,1),yaw*.36)
  else:
   global_rotate(back,(1,0,0),wind*.06-drive*.07);global_rotate(chest,(1,0,0),wind*.12-drive*(.15 if name=='Finish' else .07));global_rotate(neck,(1,0,0),-wind*.08+drive*.07);global_rotate(head,(1,0,0),-wind*.04)
   hip.location=hip.bone.matrix_local.to_quaternion().inverted()@Vector((0,0,-wind*(3.2 if name=='Finish' else .8)))
  for side in ['Left','Right']:
   global_rotate(B(side+'UpperArm'),(1,0,0),wind*.08-drive*.18)
   global_rotate(B(side+'ForeArm'),(1,0,0),wind*.10)
   global_rotate(B(side+'Leg01'),(1,0,0),wind*-.10+drive*.13)
  if name=='Sweep':
   global_rotate(B('LeftUpperArm'),(0,0,1),yaw*-.15);global_rotate(B('RightUpperArm'),(0,0,1),yaw*-.15)
 elif name in ['Jump','Dodge','Land']:
  crouch=envelope*(.7 if name=='Land' else 1)
  global_rotate(chest,(1,0,0),-.09*crouch);global_rotate(back,(1,0,0),.07*crouch)
  for side in ['Left','Right']:
   global_rotate(B(side+'UpperArm'),(1,0,0),-.30*crouch);global_rotate(B(side+'ForeArm'),(1,0,0),.50*crouch);global_rotate(B(side+'Leg01'),(1,0,0),.22*crouch);global_rotate(B(side+'Leg02'),(1,0,0),-.34*crouch)
  if name=='Land':hip.location=hip.bone.matrix_local.to_quaternion().inverted()@Vector((0,0,-3*crouch))
 for i,token in enumerate(['Tail01','Tail02','Tail03']):global_rotate(B(token),(0,0,1),math.sin(t*math.pi*2-i*.6)*.035*envelope)
for name,duration in [('Thrust',.46),('Sweep',.62),('Finish',.86),('Jump',.65),('Dodge',.28),('Land',.22)]:
 action=bpy.data.actions.new(name);rig.animation_data.action=action;frames=round(duration*fps)
 for f in range(frames+1):
  pose(name,f/frames)
  for pb in rig.pose.bones:
   pb.keyframe_insert(data_path='rotation_quaternion',frame=f);pb.keyframe_insert(data_path='location',frame=f);pb.keyframe_insert(data_path='scale',frame=f)
 clips[name]=action
rig.animation_data.action=None;reset()
for name,action in clips.items():
 track=rig.animation_data.nla_tracks.new();track.name=name;strip=track.strips.new(name,0,action)
 strip.action_frame_start=action.frame_range[0];strip.action_frame_end=action.frame_range[1];track.mute=False
out=os.path.join(os.getcwd(),'public/models/sunward-wolf.glb')
bpy.ops.export_scene.gltf(filepath=out,export_format='GLB',export_animations=True,export_animation_mode='NLA_TRACKS',export_force_sampling=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(os.getcwd(),'tools/source/sunward-wolf.blend'))
print('WOLF_PASS_1',out,'vertices',len(fox.data.vertices),'clips',list(clips))

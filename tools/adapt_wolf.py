"""Adapt the attributed artist-made canine and retain its authored locomotion.
Source/credits: THIRD_PARTY.md. Blender 4.3.2. No commercial game assets.
"""
import bpy, bmesh, math, os, hashlib
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
  v.co.x*=1.02
  tuck=math.exp(-((y-10)/16)**2)*math.exp(-((z-35)/11)**2)*5
  v.co.z+=tuck
 if y<-25 and z>70:v.co.z=70+(z-70)*.70 # pointed, slightly shorter ears
# Broader muzzle and strong shoulder line, narrower loin: a lean canine silhouette.
for v in fox.data.vertices:
 x,y,z=v.co
 if y < -45 and 46 < z < 65: v.co.x *= 1.22
 if -28 < y < -6 and 38 < z < 61: v.co.x *= 1.16
 if 4 < y < 25 and 35 < z < 58: v.co.x *= .91
# Sculpt an arched shoulder line and rounded neck/haunch surfaces rather than a boxy flank.
for v in fox.data.vertices:
 x,y,z=v.co
 if -31<y<30 and z>32:
  shoulder=math.exp(-((y+15)/13)**2)
  v.co.z += 2.8*shoulder*math.exp(-((z-56)/15)**2) - 1.7*(abs(x)/18)**1.5*math.exp(-((z-55)/10)**2)
 if -39<y<-17 and z>42: v.co.x*=1.12
# Round the torso cross section while keeping the tucked waist and long legs.
for v in fox.data.vertices:
 x,y,z=v.co
 if -27<y<29 and z>34:
  radius=math.sqrt((x/15.5)**2+((z-47.5)/16.5)**2)
  if radius>1:
   v.co.x=x/radius;v.co.z=47.5+(z-47.5)/radius
# The source has separate vertices for every triangle. Weld shared positions so
# smooth normals can actually soften the body; UVs remain per face corner.
bm=bmesh.new();bm.from_mesh(fox.data)
bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.0001)
bm.to_mesh(fox.data);bm.free()
fox.data.update()
# Ensure shading is clean; low-poly planes are intentional, not overlapping primitives.
for p in fox.data.polygons:p.use_smooth=p.center.z>30
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
# Average the authored walk cycle to obtain a natural neutral posture.
# Identity rotations erased the artist's knee/hock bends in the old action clips.
rig.animation_data.action=clips['Walk']
neutral={}
for pb in rig.pose.bones:
 samples=[];locations=[]
 for f in range(32):
  bpy.context.scene.frame_set(round(f*clips['Walk'].frame_range[1]/31))
  q=pb.rotation_quaternion.copy()
  if samples and q.dot(samples[0])<0:q.negate()
  samples.append(q);locations.append(pb.location.copy())
 q=Quaternion(tuple(sum(v[i] for v in samples)/len(samples) for i in range(4)));q.normalize()
 neutral[pb.name]=(q, sum(locations,Vector())/len(locations))
rig.animation_data.action=None
def reset():
 for pb in rig.pose.bones:
  pb.rotation_mode='QUATERNION';pb.rotation_quaternion=neutral[pb.name][0];pb.location=neutral[pb.name][1];pb.scale=(1,1,1)
def global_rotate(pb,axis,angle):
 # Convert an armature-space bend to the bone's actual local axes.
 basis=pb.bone.matrix_local.to_quaternion();local=basis.inverted()@Vector(axis);pb.rotation_quaternion=Quaternion(local,angle) @ pb.rotation_quaternion
def pose(name,t):
 reset();envelope=math.sin(t*math.pi)
 smooth=lambda a,b,x:(lambda u:u*u*(3-2*u))(max(0,min(1,(x-a)/(b-a))))
 if name in ['Thrust','Sweep','Finish']:
  contact={'Thrust':.40,'Sweep':.46,'Finish':.49}[name]
  wind=smooth(0,contact-.14,t)*(1-smooth(contact-.14,contact,t))
  drive=smooth(contact-.14,contact,t)*(1-smooth(.70,1,t))
  settle=math.sin(max(0,(t-.65)/.35)*math.pi)*.08 if t>.65 else 0
  if name=='Thrust': # short crosscut with an asymmetric step and coiled shoulders
   twist=-wind*.35+drive*.40
   global_rotate(hip,(0,0,1),twist*.22);global_rotate(back,(0,0,1),twist*.32)
   global_rotate(chest,(0,0,1),twist*.62);global_rotate(neck,(0,0,1),twist*.44)
   global_rotate(head,(1,0,0),-wind*.12+drive*.05)
   hip.location+=hip.bone.matrix_local.to_quaternion().inverted()@Vector((wind*1.5-drive*1.5,0,-wind*2))
  elif name=='Sweep': # weight transfers across the forepaws into an opposing broad arc
   twist=wind*.48-drive*.64
   global_rotate(hip,(0,0,1),twist*.40);global_rotate(back,(0,0,1),twist*.48)
   global_rotate(chest,(0,0,1),twist*.66);global_rotate(neck,(0,0,1),twist*.42)
   global_rotate(head,(1,0,0),-envelope*.08)
   hip.location+=hip.bone.matrix_local.to_quaternion().inverted()@Vector((-wind*2+drive*2,0,-envelope*2))
  else: # springing diagonal vault, spear extended with a strong landing recovery
   global_rotate(back,(1,0,0),wind*.13-drive*.16)
   global_rotate(chest,(1,0,0),wind*.14-drive*.23)
   global_rotate(neck,(1,0,0),-wind*.16+drive*.15)
   global_rotate(head,(0,0,1),-drive*.18)
   hip.location+=hip.bone.matrix_local.to_quaternion().inverted()@Vector((0,0,-wind*4+drive*4-settle*10))
  for i,side in enumerate(['Left','Right']):
   lead=1 if i==0 else -.55
   upper=wind*.18-drive*.34*lead if name!='Finish' else wind*-.25+drive*.32
   fore=wind*.34+drive*.32 if name!='Finish' else wind*.48+drive*.58
   global_rotate(B(side+'UpperArm'),(1,0,0),upper)
   global_rotate(B(side+'ForeArm'),(1,0,0),fore)
   global_rotate(B(side+'Hand'),(1,0,0),-fore*.55)
   global_rotate(B(side+'Leg01'),(1,0,0),wind*-.22+drive*.20*lead)
   global_rotate(B(side+'Leg02'),(1,0,0),-wind*.32-drive*.12)
 elif name in ['ChargedThrust','HeavyArc','HeavyReturn','ChargedHeavy','AirStrike']:
  smooth=lambda a,b,x:(lambda u:u*u*(3-2*u))(max(0,min(1,(x-a)/(b-a))))
  wind=smooth(0,.28,t)*(1-smooth(.30,.44,t));hit=smooth(.30,.44,t)*(1-smooth(.60,1,t))
  if name=='ChargedThrust': # coil low, then spring with raised forepaws and extended spear
   global_rotate(back,(1,0,0),wind*.28-hit*.18);global_rotate(chest,(1,0,0),wind*.34-hit*.35)
   global_rotate(neck,(1,0,0),-wind*.3+hit*.18);global_rotate(head,(1,0,0),-wind*.14+hit*.1)
   hip.location+=hip.bone.matrix_local.to_quaternion().inverted()@Vector((0,0,-wind*7+hit*3))
   for side in ['Left','Right']:
    global_rotate(B(side+'UpperArm'),(1,0,0),-wind*.45-hit*.62);global_rotate(B(side+'ForeArm'),(1,0,0),wind*.72+hit*.3)
    global_rotate(B(side+'Leg01'),(1,0,0),wind*.42-hit*.5);global_rotate(B(side+'Leg02'),(1,0,0),-wind*.66+hit*.2)
   recoil=math.sin(max(0,t-.44)*math.pi*5)*math.exp(-max(0,t-.44)*7) if t>.44 else 0
   global_rotate(head,(1,0,0),recoil*.06);global_rotate(chest,(0,0,1),recoil*.035)
  elif name in ['HeavyArc','ChargedHeavy']: # vertical overhead chop; no horizontal sweep
   strength=1.25 if name=='ChargedHeavy' else 1
   lift=smooth(0,.30,t)*(1-smooth(.32,.52,t));chop=smooth(.32,.52,t)*(1-smooth(.67,1,t))
   global_rotate(back,(1,0,0),(-lift*.14+chop*.05)*strength)
   global_rotate(chest,(1,0,0),(-lift*.35+chop*.08)*strength)
   global_rotate(neck,(1,0,0),(-lift*.58+chop*.12)*strength)
   global_rotate(head,(1,0,0),-lift*.16+chop*.04)
   hip.location+=hip.bone.matrix_local.to_quaternion().inverted()@Vector((0,0,lift*2-chop*3))
   for side in ['Left','Right']:
    global_rotate(B(side+'UpperArm'),(1,0,0),-lift*.65+chop*.25);global_rotate(B(side+'ForeArm'),(1,0,0),lift*.85+chop*.42)
    global_rotate(B(side+'Leg01'),(1,0,0),lift*.16+chop*.38);global_rotate(B(side+'Leg02'),(1,0,0),-chop*.58)
  elif name=='HeavyReturn': # low diagonal preparation into a rising whole-body uppercut
   coil=smooth(0,.24,t)*(1-smooth(.28,.46,t));rise=smooth(.28,.46,t)*(1-smooth(.66,1,t))
   yaw=coil*.28-rise*.42
   global_rotate(hip,(0,0,1),yaw*.38);global_rotate(back,(0,0,1),yaw*.46)
   global_rotate(chest,(1,0,0),coil*.06-rise*.23);global_rotate(neck,(1,0,0),coil*.10-rise*.36)
   global_rotate(head,(0,0,1),yaw*.25)
   hip.location+=hip.bone.matrix_local.to_quaternion().inverted()@Vector((rise*2,0,-coil*3+rise*2))
   for i,side in enumerate(['Left','Right']):
    global_rotate(B(side+'UpperArm'),(1,0,0),-rise*(.25 if i else .45))
    global_rotate(B(side+'ForeArm'),(1,0,0),coil*.32+rise*.55)
    global_rotate(B(side+'Leg01'),(1,0,0),coil*-.17+rise*.22)
    global_rotate(B(side+'Leg02'),(1,0,0),-coil*.3)
  else: # held tucked corkscrew into nose-down spike, then landing crouch
   tuck=1-smooth(.18,.45,t);dive=smooth(.18,.45,t)*(1-smooth(.68,1,t))
   global_rotate(hip,(1,0,0),dive*.65);global_rotate(back,(1,0,0),dive*.24)
   global_rotate(chest,(1,0,0),dive*.34);global_rotate(neck,(1,0,0),dive*.38)
   for side in ['Left','Right']:
    global_rotate(B(side+'UpperArm'),(1,0,0),tuck*.55+dive*.16);global_rotate(B(side+'ForeArm'),(1,0,0),tuck*.82+dive*.45)
    global_rotate(B(side+'Leg01'),(1,0,0),-tuck*.70+dive*.36);global_rotate(B(side+'Leg02'),(1,0,0),-tuck*.95-dive*.52)
 elif name in ['ChargeLight','ChargeHeavy']:
  weight=t*t*(3-2*t);global_rotate(chest,(1,0,0),weight*.15);global_rotate(neck,(1,0,0),-weight*.12);global_rotate(head,(1,0,0),weight*-.08)
  hip.location=hip.bone.matrix_local.to_quaternion().inverted()@Vector((0,0,-weight*(3.4 if name=='ChargeHeavy' else 1.5)))
  for side in ['Left','Right']:global_rotate(B(side+'UpperArm'),(1,0,0),weight*-.08);global_rotate(B(side+'ForeArm'),(1,0,0),weight*.18)
 elif name in ['Bark','Growl','Howl','Hurt']:
  pulse=math.sin(t*math.pi);global_rotate(neck,(1,0,0),pulse*({'Bark':.16,'Growl':-.10,'Howl':.45,'Hurt':-.15}[name]));global_rotate(head,(1,0,0),pulse*({'Bark':.13,'Growl':-.08,'Howl':.3,'Hurt':.15}[name]));global_rotate(chest,(1,0,0),pulse*.03)
 elif name in ['JumpRise','JumpFall']:
  # Keep knees folded through apex; only reach down during late descent.
  tuck=(.15+.48*smooth(0,1,t)) if name=='JumpRise' else (.63*(1-smooth(0,1,t)))
  global_rotate(chest,(1,0,0),-.18*tuck);global_rotate(back,(1,0,0),.08*tuck);global_rotate(neck,(1,0,0),.09*tuck)
  for side in ['Left','Right']:
   global_rotate(B(side+'UpperArm'),(1,0,0),  .55*tuck);global_rotate(B(side+'ForeArm'),(1,0,0),.82*tuck)
   global_rotate(B(side+'Hand'),(1,0,0),-.65*tuck)
   global_rotate(B(side+'Leg01'),(1,0,0),-.40*tuck);global_rotate(B(side+'Leg02'),(1,0,0),-.62*tuck)
 elif name in ['Jump','Dodge','Land']:
  crouch=envelope*(.7 if name=='Land' else 1)
  global_rotate(chest,(1,0,0),-.09*crouch);global_rotate(back,(1,0,0),.07*crouch)
  for side in ['Left','Right']:
   global_rotate(B(side+'UpperArm'),(1,0,0),-.30*crouch);global_rotate(B(side+'ForeArm'),(1,0,0),.50*crouch);global_rotate(B(side+'Leg01'),(1,0,0),.22*crouch);global_rotate(B(side+'Leg02'),(1,0,0),-.34*crouch)
  if name=='Land':hip.location=hip.bone.matrix_local.to_quaternion().inverted()@Vector((0,0,-3*crouch))
 for i,token in enumerate(['Tail01','Tail02','Tail03']):global_rotate(B(token),(0,0,1),math.sin(t*math.pi*2-i*.6)*.035*envelope)
for name,duration in [('Thrust',.54),('Sweep',.68),('Finish',.90),('Jump',.65),('Dodge',.28),('Land',.28),('JumpRise',.42),('JumpFall',.36),('ChargedThrust',.82),('HeavyArc',.78),('HeavyReturn',.92),('ChargedHeavy',1.08),('AirStrike',.74),('ChargeLight',.35),('ChargeHeavy',.42),('Bark',.55),('Growl',.9),('Howl',1.7),('Hurt',.45)]:
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

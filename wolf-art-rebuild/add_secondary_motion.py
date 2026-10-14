"""Attach deforming fur and authored action poses without repainting approved artwork."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(root/'wolf.blend'))
rig=bpy.data.objects['DivineWolfRig'];coat=bpy.data.objects['Wolf ivory coat'];scene=bpy.context.scene
rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_set(1)
base={b.name:(b.location.copy(),b.rotation_euler.copy()) for b in rig.pose.bones}
specs=[]
for side,x in [('L',1),('R',-1)]:
 specs += [(f'ruff{side}',(x*.64,-2.45,4.32),(x*.77,-1.83,3.90),'neck','ruff',x),(f'shoulderFur{side}',(x*.90,-1.47,3.53),(x*1.12,-.68,3.78),'chest','shoulder',x)]
 for leg,y in [('fore',-1.18),('hind',2.15)]:
  specs.append((f'{leg}Fur{side}',(x*.66,y,.78),(x*.79,y+.40,1.62),f'{leg}Shin{side}',leg,x))
bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
for name,start,end,parent,kind,sign in specs:
 b=rig.data.edit_bones.new(name);b.head=start;b.tail=end;b.parent=rig.data.edit_bones[parent]
bpy.ops.object.mode_set(mode='OBJECT')
counts={}
for name,start,end,parent,kind,sign in specs:
 group=coat.vertex_groups.new(name=name);counts[name]=0
 for v in coat.data.vertices:
  x,y,z=v.co
  if x*sign<.36:continue
  if kind=='ruff':w=max(0,1-abs(y+2.18)/.65)*max(0,1-abs(z-4.13)/.48)*max(0,min(1,(abs(x)-.48)/.24))*.62
  elif kind=='shoulder':w=max(0,1-abs(y+1.04)/.63)*max(0,1-abs(z-3.65)/.49)*max(0,min(1,(abs(x)-.72)/.28))*.75
  else:
   center=-.94 if kind=='fore' else 2.32
   w=max(0,1-abs(y-center)/.48)*max(0,min(1,(z-.76)/.56))*max(0,1-abs(z-1.45)/.68)*.70
   if z>2.1:w=0
  if w<.005:continue
  for assignment in list(v.groups):
   old=coat.vertex_groups[assignment.group];old.add([v.index],assignment.weight*(1-w),'REPLACE')
  group.add([v.index],w,'REPLACE');counts[name]+=1
print('FUR_WEIGHT_COUNTS',counts,flush=True)
# Low amplitude wind is present at rest; faster motion has more trailing bend.
def fur_keys(action,duration,speed):
 rig.animation_data.action=action
 for f in range(1,duration+2):
  phase=(f-1)/duration*math.tau
  for i,(name,*_) in enumerate(specs):
   b=rig.pose.bones[name];b.rotation_mode='XYZ'
   lag=i*.57
   b.rotation_euler=(.018*speed+.035*math.sin(phase-lag),.020*math.sin(phase-lag-.5),(.024+.017*speed)*math.sin(phase-lag-1.1))
   b.keyframe_insert('rotation_euler',frame=f)
for clip,duration,speed in [('Idle',96,.15),('Walk',48,.7),('Run',30,1.6)]:fur_keys(bpy.data.actions[clip],duration,speed)
# Combat poses have anticipation, an active accent, follow-through and recovery.
# Values are body pitch, chest twist, neck pitch, head yaw, foreleg tuck and hop.
actions={
 'Thrust':(.54,[(0,(0,0,0,0,0,0)),(.23,(-.10,-.18,.16,-.12,.20,0)),(.40,(.08,.12,-.18,.16,-.18,.03)),(.60,(.03,.23,-.09,.10,-.05,0)),(1,(0,0,0,0,0,0))]),
 'Sweep':(.68,[(0,(0,.15,0,.08,0,0)),(.22,(-.05,-.43,.10,-.55,.12,0)),(.46,(.04,.38,-.03,.62,.25,.02)),(.69,(0,.48,.07,.35,.10,0)),(1,(0,0,0,0,0,0))]),
 'Finish':(.90,[(0,(0,0,0,0,0,0)),(.24,(-.15,-.12,.19,-.15,.35,-.12)),(.49,(.15,.20,-.24,.12,.65,.24)),(.67,(.07,.25,-.09,.22,.18,.10)),(1,(0,0,0,0,0,0))]),
 'HeavyArc':(.78,[(0,(0,0,0,0,0,0)),(.28,(-.16,-.25,.34,-.23,.40,-.09)),(.51,(.12,.19,-.32,.20,.18,.06)),(.69,(.07,.27,-.16,.13,.07,-.08)),(1,(0,0,0,0,0,0))]),
 'HeavyReturn':(.92,[(0,(.06,.20,-.13,.12,.15,0)),(.22,(.13,.34,-.23,.27,.30,-.10)),(.46,(-.16,-.36,.35,-.40,.58,.17)),(.71,(-.08,-.22,.18,-.18,.23,.08)),(1,(0,0,0,0,0,0))]),
 'ChargedThrust':(.82,[(0,(-.13,0,.20,0,.30,-.09)),(.25,(-.22,-.14,.23,-.12,.45,-.16)),(.44,(.19,.15,-.29,.17,.36,.15)),(.65,(.07,.24,-.12,.18,.11,.04)),(1,(0,0,0,0,0,0))]),
 'ChargedHeavy':(1.08,[(0,(-.14,-.20,.28,-.15,.38,-.08)),(.29,(-.25,-.36,.43,-.25,.62,-.14)),(.52,(.23,.35,-.43,.39,.50,.22)),(.70,(.06,.25,-.19,.18,.23,-.10)),(1,(0,0,0,0,0,0))]),
 'AirStrike':(.85,[(0,(-.10,0,.20,0,.55,0)),(.25,(-.28,.1,.35,.12,.90,.08)),(.52,(.38,-.12,-.38,-.14,.18,-.07)),(.75,(.19,0,-.20,0,.10,-.10)),(1,(0,0,0,0,0,0))]),
 'JumpRise':(.40,[(0,(.05,0,-.06,0,.12,-.05)),(.55,(-.12,0,.12,0,.37,.02)),(1,(-.05,0,.06,0,.26,0))]),
 'JumpFall':(.40,[(0,(-.05,0,.06,0,.26,0)),(.60,(.08,0,-.10,0,.16,0)),(1,(.12,0,-.10,0,.05,0))]),
 'Land':(.28,[(0,(.09,0,-.10,0,.22,-.17)),(.35,(.05,0,-.05,0,.14,-.23)),(1,(0,0,0,0,0,0))]),
 'Dodge':(.50,[(0,(0,0,0,0,0,0)),(.35,(-.10,.15,.10,.15,.65,-.15)),(.65,(.06,-.10,-.04,-.10,.28,.02)),(1,(0,0,0,0,0,0))]),
 'ChargeLight':(1,[(0,(0,0,0,0,0,0)),(1,(-.14,-.12,.18,-.1,.28,-.08))]),
 'ChargeHeavy':(1,[(0,(0,0,0,0,0,0)),(1,(-.22,-.24,.38,-.18,.48,-.12))]),
 'Bark':(.55,[(0,(0,0,0,0,0,0)),(.32,(-.08,0,.23,0,.10,.04)),(.52,(.07,0,-.08,0,.03,0)),(1,(0,0,0,0,0,0))]),
 'Growl':(.8,[(0,(0,0,0,0,0,0)),(.4,(.04,.08,-.13,.06,.07,-.06)),(1,(0,0,0,0,0,0))]),
 'Howl':(1.7,[(0,(0,0,0,0,0,0)),(.25,(-.05,0,.25,0,.03,.02)),(.70,(-.03,0,.22,0,.02,.01)),(1,(0,0,0,0,0,0))]),
 'Hurt':(.4,[(0,(0,0,0,0,0,0)),(.25,(-.12,-.16,.10,-.2,.18,-.06)),(1,(0,0,0,0,0,0))]),
}
for name,(seconds,keys) in actions.items():
 action=bpy.data.actions.new(name);rig.animation_data.action=action;duration=round(seconds*24)
 for t,(pitch,twist,neck,yaw,tuck,hop) in keys:
  f=1+t*duration
  for b in rig.pose.bones:
   b.rotation_mode='XYZ';b.location=base.get(b.name,(Vector(),Vector()))[0];b.rotation_euler=base.get(b.name,(Vector(),Vector()))[1]
  rig.pose.bones['body'].rotation_euler.x+=pitch;rig.pose.bones['body'].location.z+=hop
  rig.pose.bones['chest'].rotation_euler.y+=twist;rig.pose.bones['neck'].rotation_euler.x+=neck;rig.pose.bones['head'].rotation_euler.z+=yaw
  for side,sign in [('L',1),('R',-1)]:
   rig.pose.bones['fore'+side].rotation_euler.x-=tuck*(1 if side=='L' else .78)
   rig.pose.bones['foreShin'+side].rotation_euler.x+=tuck*1.45
   rig.pose.bones['hind'+side].rotation_euler.x+=tuck*.30
   rig.pose.bones['hindShin'+side].rotation_euler.x-=tuck*.45
  for b in rig.pose.bones:
   if b.bone.use_deform:b.keyframe_insert('rotation_euler',frame=f);b.keyframe_insert('location',frame=f)
 fur_keys(action,duration,1.2)
 track=rig.animation_data.nla_tracks.new();track.name=name;track.strips.new(name,1,action);track.mute=True
rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_set(1)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);coat.select_set(True);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(root/'wolf.glb'),use_selection=True,export_animations=True,export_nla_strips=True)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'wolf.blend'))
(root/'review'/'motion-report.json').write_text(json.dumps({'fur_vertices':counts,'actions':list(actions),'tail_states':['Idle','Walk','Run']},indent=2))

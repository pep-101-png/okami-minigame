"""Existing original-wolf IK/pose helpers, reused without changing rig geometry.
Executed with the authoring context (r, s, feet, REF and REST) supplied by author_combat.
"""
def reset():
 r.animation_data.action=None
 for p in r.pose.bones:p.matrix_basis.identity()

def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)

def curve(nodes,t):
 for (a,x),(b,y)in zip(nodes,nodes[1:]):
  if t<=b:return x+(y-x)*smooth((t-a)/(b-a))
 return nodes[-1][1]

def soles():
 bpy.context.view_layer.update();ev=foot.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();out={}
 for k,d in feet.items():
  points=[ev.matrix_world@me.vertices[i].co for i in d['ids']];out[k]={'center':sum(points,Vector())/len(points),'z':min(p.z for p in points)}
 ev.to_mesh_clear();return out

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

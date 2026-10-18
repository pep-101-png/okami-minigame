"""Repair only the Unity-copy sleep clips. Source GLB/.blend remain read-only.
The imported bake has inverted knee/elbow planes. Reconstruct stable sagittal
joint planes, keep body/paw trajectories and re-bake FK transforms, not rig scales.
"""
import bpy, math, json, hashlib, sys
from pathlib import Path
from mathutils import Vector, Matrix
R=Path(__file__).resolve().parents[1]
path=R/'Assets/Sunward/Models/Amaterasu.fbx'
bpy.ops.wm.read_factory_settings(use_empty=True); s=bpy.context.scene; s.render.fps=60
source=Path(sys.argv[sys.argv.index("--")+1]) if "--" in sys.argv else path
bpy.ops.import_scene.fbx(filepath=str(source)); arm=next(o for o in s.objects if o.type=='ARMATURE')
original_hash=hashlib.sha256(source.read_bytes()).hexdigest()
for track in list(arm.animation_data.nla_tracks): arm.animation_data.nla_tracks.remove(track)
report={}
if any(a.name.split('|')[-1].endswith('_Legacy')for a in bpy.data.actions):raise RuntimeError('Input already contains repaired sleep actions. Supply the unrepaired original FBX copy to preserve rollback cleanly.')

def orient(p, start, end, reference):
 # The old pole flip also contaminated axial roll. Orient from the fixed
 # rest basis rather than transporting that broken twist into the new action.
 reference=p.bone.matrix_local.copy()
 direction=(end-start).normalized(); old=reference.to_3x3().col[1].normalized()
 mat=old.rotation_difference(direction).to_matrix().to_4x4() @ reference
 mat.translation=start; p.matrix=mat; bpy.context.view_layer.update()

for old in list(bpy.data.actions):
 name=old.name.split('|')[-1].replace('_WOLF_RIG','')
 if name not in ['Sleep_Down','Sleep_Loop','Sleep_Up']: continue
 old.name=name+'_Legacy'; old.use_fake_user=True
 repaired=old.copy();repaired.name=name;repaired.use_fake_user=True
 affected=[]
 for kind in ['front','rear']:
  for side in ['L','R']:
   for part in ['upper','lower','paw' if kind=='front' else 'hock']:
    affected.append('DEF_'+kind+'_'+part+'.'+side)
 for fc in list(repaired.fcurves):
  if any('pose.bones["'+n+'"]' in fc.data_path for n in affected): repaired.fcurves.remove(fc)
 saved_quat={}; min_joint=100; max_jump=0; prior={}; metrics=[]
 for frame in range(round(old.frame_range[0]),round(old.frame_range[1])+1):
  arm.animation_data.action=old;s.frame_set(frame);bpy.context.view_layer.update()
  target={n:arm.pose.bones[n].matrix.copy()for n in affected}
  # Compute joints before changing parents. Knees and elbows never rotate out
  # sideways into the torso; projected downward plane stays continuous.
  joints=[]
  for kind in ['front','rear']:
   for side in ['L','R']:
    un='DEF_'+kind+'_upper.'+side;ln='DEF_'+kind+'_lower.'+side;pn='DEF_'+kind+('_paw.'if kind=='front'else'_hock.')+side
    up,lo=arm.pose.bones[un],arm.pose.bones[ln]
    start=target[un].translation.copy();end=target[pn].translation.copy()
    compression=max(0,min(1,(2.8-start.z)/1.8)); compression=compression*compression*(3-2*compression)
    # Prone paws must reach forward as the chest settles; leaving them under
    # the torso makes a low shoulder incompatible with a ground-level elbow.
    prone=end.copy();prone.y=start.y-(2.05 if kind=='front' else 1.65);prone.z=max(.14,end.z)
    end=end.lerp(prone,compression);target[pn].translation=end
    delta=end-start;distance=delta.length;axis=delta.normalized(); l1=up.bone.length;l2=lo.bone.length
    distance=max(abs(l1-l2)+.001,min(distance,l1+l2-.001))
    along=(l1*l1-l2*l2+distance*distance)/(2*distance)
    radius=math.sqrt(max(0,l1*l1-along*along))
    # Match standing bend initially, then settle into a lower/forward folded
    # plane. Blend via joint direction vectors, never Euler angle wraps.
    stand=Vector((0,1 if kind=='front'else -1,0)); down=Vector((0,0,-1))
    plane=stand.copy()
    plane-=axis*plane.dot(axis)
    if plane.length<.01:plane=Vector((0,0,-1))-axis*axis.z*-1
    plane.normalize();center=start+axis*along;elbow=center+plane*radius
    if elbow.z < .18:
     upward=Vector((0,0,1))-axis*axis.z; upward.normalize()
     lateral=axis.cross(upward).normalized()
     # At floor contact use the outward branch, avoiding an inward knee pop.
     if lateral.x*(1 if side=='L'else -1)<0:lateral.negate()
     c=max(-1,min(1,(.18-center.z)/max(.00001,radius*upward.z)))
     elbow=center+radius*(upward*c+lateral*math.sqrt(max(0,1-c*c)))
    min_joint=min(min_joint,elbow.z)
    joints.append((un,ln,pn,start,elbow,end))
  for un,ln,pn,start,elbow,end in joints:
   orient(arm.pose.bones[un],start,elbow,target[un]);orient(arm.pose.bones[ln],elbow,end,target[ln]);arm.pose.bones[pn].matrix=target[pn];bpy.context.view_layer.update()
  # Capture local FK transforms after the whole chain is corrected.
  values={n:(arm.pose.bones[n].location.copy(),arm.pose.bones[n].rotation_quaternion.copy(),arm.pose.bones[n].scale.copy())for n in affected}
  arm.animation_data.action=repaired
  for n,(loc,quat,scale)in values.items():
   p=arm.pose.bones[n];p.rotation_mode='QUATERNION'
   if n in saved_quat and saved_quat[n].dot(quat)<0:quat.negate()
   saved_quat[n]=quat.copy();p.location=loc;p.rotation_quaternion=quat;p.scale=scale
   for prop in ['location','rotation_quaternion','scale']:p.keyframe_insert(prop,frame=frame,group=n)
   if n in prior:max_jump=max(max_jump,prior[n].rotation_difference(quat).angle)
   prior[n]=quat.copy()
  arm.animation_data.action=old
 for fc in repaired.fcurves:
  if any('pose.bones["'+n+'"]' in fc.data_path for n in affected):
   for k in fc.keyframe_points:k.interpolation='LINEAR'
 report[name]={'frames':int(old.frame_range[1]-old.frame_range[0]+1),'minimum_elbow_knee_z':min_joint,'max_joint_rotation_step_radians':max_jump}
 print('REPAIRED',name,report[name],flush=True)
arm.animation_data.action=None
for p in arm.pose.bones:p.matrix_basis.identity()
s.frame_set(0);bpy.context.view_layer.update()
# Export every existing action, including rollback copies of the three sleep clips.
bpy.ops.object.select_all(action='DESELECT')
for o in s.objects:
 if o==arm or o.type=='MESH':o.select_set(True)
bpy.context.view_layer.objects.active=arm
bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'ARMATURE','MESH'},add_leaf_bones=False,bake_anim=True,bake_anim_use_all_actions=True,bake_anim_use_nla_strips=False,bake_anim_force_startend_keying=True,bake_anim_step=1,bake_anim_simplify_factor=0,axis_forward='-Z',axis_up='Y',path_mode='STRIP')
report['input_fbx_sha256']=original_hash;report['note']='FK knee/elbow plane correction on Unity copy only. Blender render and Unity import review required.'
(R/'Review/sleep-repair.json').write_text(json.dumps(report,indent=2))

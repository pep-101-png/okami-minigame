"""Blender-only inspection of the existing wolf rig's procedural poses, not Unity rendering."""
import bpy,math,sys
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
ROOT=Path(__file__).resolve().parents[3];DEST=Path(__file__).parent/'previews';DEST.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=str(ROOT/'Sunward-Unity/Assets/Sunward/Models/Amaterasu.fbx'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
for o in list(bpy.data.objects):
 if o!=rig and (o.type!='MESH' or not o.find_armature()):bpy.data.objects.remove(o,do_unlink=True)
# Neutral inspection material isolates skin deformation from FBX material import.
inspection=bpy.data.materials.new('Neutral rig inspection only');inspection.diffuse_color=(.63,.61,.55,1);inspection.use_nodes=True;inspection.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.63,.61,.55,1)
for obj in bpy.data.objects:
 if obj.type=='MESH':
  obj.data.materials.clear();obj.data.materials.append(inspection)
rig.animation_data_clear()
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
rig.scale=(.34,)*3
for image in bpy.data.images:
 candidates=list((ROOT/'Sunward-Unity/Assets/Sunward/Textures').rglob(Path(image.filepath).name))
 if candidates:image.filepath=str(candidates[0])
bpy.context.view_layer.update()
rest={b.name:b.matrix_basis.copy() for b in rig.pose.bones}
forward=Vector((0,-1,0));up=Vector((0,0,1));right=Vector((1,0,0))
def point(pb):return rig.matrix_world@pb.head
def rotate(pb,rotation):
 m=rig.matrix_world@pb.matrix;loc=m.translation.copy();m=rotation.to_matrix().to_4x4()@m;m.translation=loc;pb.matrix=rig.matrix_world.inverted()@m;bpy.context.view_layer.update()
def move(pb,offset):
 m=rig.matrix_world@pb.matrix;m.translation+=offset;pb.matrix=rig.matrix_world.inverted()@m;bpy.context.view_layer.update()
def solve(a,b,c,target,pole):
 origin=point(a);v1=point(b)-origin;v2=point(c)-point(b);l1=v1.length;l2=v2.length;axis=(target-origin).normalized();d=max(abs(l1-l2)+.0001,min(l1+l2-.0001,(target-origin).length));x=(l1*l1-l2*l2+d*d)/(2*d);h=math.sqrt(max(0,l1*l1-x*x));side=(pole-axis*pole.dot(axis)).normalized();knee=origin+axis*x+side*h
 rotate(a,v1.rotation_difference(knee-origin));rotate(b,(point(c)-point(b)).rotation_difference(origin+axis*d-point(b)))

def pose(kind,phase=0,vertical=0,age=.35):
 rig.location=(0,0,-.82 if kind=='swim' else 0)
 for pb in rig.pose.bones:pb.matrix_basis=rest[pb.name]
 bpy.context.view_layer.update()
 limbs=[]
 for i in range(4):
  k='front' if i<2 else 'rear';s='L' if i%2==0 else 'R';a=rig.pose.bones[f'DEF_{k}_upper.{s}'];b=rig.pose.bones[f'DEF_{k}_lower.{s}'];c=rig.pose.bones[f'DEF_{k}_{"paw" if i<2 else "hock"}.{s}'];limbs.append((a,b,c,point(c).copy(),(rig.matrix_world@c.matrix).to_quaternion()))
 hips=rig.pose.bones['DEF_hips'];pitch=-22 if kind=='sit' else -5+math.sin(phase*2)*1.2 if kind=='swim' else max(-11,min(12,-vertical*1.7));rotate(hips,Quaternion(right,math.radians(pitch)))
 if kind=='sit':move(hips,-up*.43-forward*.12)
 if kind=='swim':move(hips,up*(math.sin(phase*2)*.018))
 for name,factor in [('DEF_neck_base',.35),('DEF_head',.25)]:rotate(rig.pose.bones[name],Quaternion(right,math.radians((-9 if factor==.35 else -5) if kind=='swim' else -pitch*factor)))
 for i,(a,b,c,p,foot_rotation) in enumerate(limbs):
  if kind=='sit':target=p+(Vector((0,0,0)) if i<2 else -up*.35+forward*.30)
  elif kind=='swim':
   ph=phase+(0 if i in [0,3] else math.pi);target=p+forward*(math.cos(ph)*(.3 if i<2 else .19))+up*(.18+math.sin(ph)*(.22 if i<2 else .16))
  else:
   tuck=math.sin(max(0,min(1,age/.7))*math.pi);reach=max(0,min(1,(-vertical-1)/5)) if vertical < -1 else 0;target=p+up*tuck*(.31 if i<2 else .39)+forward*((-.16*tuck+.16*reach) if i<2 else .23*tuck)
  solve(a,b,c,target,forward*(-1 if i<2 else 1))
  if kind=='sit':
   m=rig.matrix_world@c.matrix;loc=m.translation.copy();m=Matrix.LocRotScale(loc,foot_rotation,m.to_scale());c.matrix=rig.matrix_world.inverted()@m;bpy.context.view_layer.update()

# Neutral studio lighting. Does not substitute for actual Unity skinning/shaders.
bpy.ops.object.camera_add(location=(4,-6,2.5));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,.65))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4.1;bpy.context.scene.camera=cam
for pos,power in [((2,-4,6),600),((-3,1,3),400)]:
 bpy.ops.object.light_add(type='AREA',location=pos);bpy.context.object.data.energy=power;bpy.context.object.data.size=5
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=20;scene.cycles.use_denoising=False;scene.world.color=(.3,.3,.3);scene.render.resolution_x=950;scene.render.resolution_y=700;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='JPEG'
for kind in (['sit'] if '--sit-only' in sys.argv else ['swim','jump','sit']):
 pose(kind,phase=.7);cam.location=(4,-6,1.9 if kind=='swim' else 2.5);cam.rotation_euler=(Vector((0,0,.05 if kind=='swim' else .65))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(DEST/(kind+'-blender.jpg'));bpy.ops.render.render(write_still=True)
print('BLENDER_POSE_PREVIEWS_ONLY',DEST)

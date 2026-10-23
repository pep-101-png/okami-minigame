"""Sample target rig poses in Blender. Not Unity blending or a live animation test."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
src=(ROOT/'tools/living-world/movement/render_pose_preview.py').read_text().split('# Neutral studio lighting')[0]
src=src.replace('parents[3]','parents[2]').replace("rig.location=(0,0,-.82 if kind=='swim' else 0)","rig.location=(0,0,-1.06 if kind=='swim' else 0)")
src=src.replace('tuck=math.sin(max(0,min(1,age/.7))*math.pi)','q=max(0,min(1,(vertical+5)/10));q=q*q*(3-2*q);v=max(0,min(1,age/.13));tuck=q*v*v*(3-2*v)')
exec(compile(src,str(__file__),'exec'),globals())
DEST=ROOT/'tools/player-review3/previews';DEST.mkdir(exist_ok=True)
meshes=[o for o in bpy.data.objects if o.type=='MESH'];snapshots=[]
def neutral():
 rig.location=(0,0,0)
 for pb in rig.pose.bones:pb.matrix_basis=rest[pb.name]
 bpy.context.view_layer.update()
def limbs():
 out=[]
 for i in range(4):
  k='front' if i<2 else 'rear';s='L' if i%2==0 else 'R';a=rig.pose.bones[f'DEF_{k}_upper.{s}'];b=rig.pose.bones[f'DEF_{k}_lower.{s}'];c=rig.pose.bones[f'DEF_{k}_{"paw" if i<2 else "hock"}.{s}'];out.append((a,b,c,point(c).copy()))
 return out
def gait(phase,speed):
 neutral();feet=limbs();g=max(0,min(1,(speed-4.3)/2.2));g=g*g*(3-2*g);w=1-max(0,min(1,(speed-.9)/1.6));stride=.68+(1.60-.68)*max(0,min(1,(speed-.8)/6.4))
 move(rig.pose.bones['DEF_hips'],up*math.sin(phase*math.tau*2)*(.010+.013*g))
 for i,(a,b,c,p) in enumerate(feet):
  trot=0 if i in [0,3] else .5;walk=[0,.5,.75,.25][i];run=[0,.14,.53,.67][i];offset=(trot+(walk-trot)*w)*(1-g)+run*g;q=(phase+offset)%1
  if q<.6:z=stride*(.3-q);lift=0
  else:
   u=(q-.6)/.4;ss=u*u*(3-2*u);z=stride*(-.3+.6*ss);lift=math.sin(u*math.pi)*(.065+.085*g)
  solve(a,b,c,p+forward*z+up*lift,forward*(-1 if i<2 else 1))
def combat(progress):
 neutral();feet=limbs();anticipation=math.sin(min(1,progress/.32)*math.pi);sweep=math.sin(max(0,min(1,(progress-.2)/.8))*math.pi);weight=math.sin(progress*math.pi);yaw=-anticipation*9+sweep*16
 move(rig.pose.bones['DEF_hips'],-up*(anticipation*.045+weight*.025));rotate(rig.pose.bones['DEF_hips'],Quaternion(up,math.radians(yaw)));rotate(rig.pose.bones['DEF_neck_base'],Quaternion(up,math.radians(-yaw*.45)))
 for i,(a,b,c,p) in enumerate(feet):solve(a,b,c,p+(forward*sweep*.12+up*sweep*.055 if i==0 else Vector((0,0,0))),forward*(-1 if i<2 else 1))
def freeze(x):
 dep=bpy.context.evaluated_depsgraph_get()
 for obj in meshes:
  e=obj.evaluated_get(dep);m=bpy.data.meshes.new_from_object(e,depsgraph=dep);copy=bpy.data.objects.new('Sampled target pose',m);bpy.context.collection.objects.link(copy);copy.matrix_world=obj.matrix_world.copy();copy.location.x+=x;snapshots.append(copy)
for i,q in enumerate([0,.25,.5]):gait(q,6.4);freeze((i-2.5)*2.7)
pose('jump',vertical=3,age=.2);rig.location.z=.5;bpy.context.view_layer.update();freeze(.5*2.7)
pose('jump',vertical=-4,age=.6);rig.location.z=.4;bpy.context.view_layer.update();freeze(1.5*2.7)
combat(.60);freeze(2.5*2.7)
for obj in meshes:obj.hide_render=True
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.02));floor=bpy.context.object
for p,power in [((0,-5,8),1200),((-5,4,6),900)]:bpy.ops.object.light_add(type='AREA',location=p);bpy.context.object.data.energy=power;bpy.context.object.data.size=7
bpy.ops.object.camera_add(location=(7,-17,6));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=18.2
s=bpy.context.scene;s.camera=cam;s.render.engine='CYCLES';s.cycles.samples=10;s.cycles.use_denoising=False;s.world.color=(.3,.3,.3);s.render.resolution_x=1800;s.render.resolution_y=800;s.render.resolution_percentage=100;s.render.image_settings.file_format='JPEG';s.render.filepath=str(DEST/'run-jump-attack-target-poses.jpg');bpy.ops.render.render(write_still=True)

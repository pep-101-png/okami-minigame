"""Read-only Blender rehearsal of new fixed-length sleep solve; NOT Unity validation."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector,Quaternion
R=Path(__file__).resolve().parents[1];bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(R/'Assets/Sunward/Models/Amaterasu.fbx'));s=bpy.context.scene
arm=next(o for o in s.objects if o.type=='ARMATURE');arm.animation_data.action=None
for tr in list(arm.animation_data.nla_tracks):arm.animation_data.nla_tracks.remove(tr)
for p in arm.pose.bones:p.matrix_basis.identity()
bpy.context.view_layer.update();bones=list(arm.pose.bones);rest={p.name:p.matrix_basis.copy()for p in bones}
feet={k+d:arm.pose.bones['DEF_'+k+'_paw.'+d].matrix.copy()for k in ['front','rear']for d in ['L','R']}
tips={k+d:arm.pose.bones['DEF_'+k+('_paw.'if k=='front'else'_hock.')+d].matrix.copy()for k in ['front','rear']for d in ['L','R']}
lengths={p.name:p.matrix_basis.to_scale().copy()for p in bones};metrics=[]
def rotate(p,quat):
 m=p.matrix.copy();rot=quat.to_matrix()@m.to_3x3();n=rot.to_4x4();n.translation=m.translation;p.matrix=n;bpy.context.view_layer.update()
def orient(p,child,end):rotate(p,(child-p.matrix.translation).normalized().rotation_difference((end-p.matrix.translation).normalized()))
for phase in [0,.25,.5,.75,1]:
 q=phase*phase*(3-2*phase)
 for p in bones:p.matrix_basis=rest[p.name]
 bpy.context.view_layer.update();hips=arm.pose.bones['DEF_hips'];m=hips.matrix.copy();m.translation.z-=(3.03-.43/.34)*q;hips.matrix=m;bpy.context.view_layer.update()
 for n in ['DEF_spine_mid','DEF_chest','DEF_neck_base','DEF_neck_upper','DEF_head']:
  rotate(arm.pose.bones[n],Quaternion((1,0,0),math.radians((12 if n=='DEF_head'else 18 if 'neck'in n else 2)*q)))
 rotate(arm.pose.bones['DEF_tail_01'],Quaternion((1,0,0),math.radians(8*q)))
 for k in ['front','rear']:
  for side in ['L','R']:
   key=k+side;up=arm.pose.bones['DEF_'+k+'_upper.'+side];lo=arm.pose.bones['DEF_'+k+'_lower.'+side];tip=arm.pose.bones['DEF_'+k+('_paw.'if k=='front'else'_hock.')+side];paw=arm.pose.bones['DEF_'+k+'_paw.'+side]
   target=feet[key].translation+Vector((0,-(.65 if k=='front'else .45)/.34*q,0));end=target+tips[key].translation-feet[key].translation
   start=up.matrix.translation.copy();a=(lo.matrix.translation-start).length;b=(tip.matrix.translation-lo.matrix.translation).length
   axis=(end-start).normalized();d=max(abs(a-b)+.0001,min((end-start).length,a+b-.0001));x=(a*a-b*b+d*d)/(2*d);h=math.sqrt(max(0,a*a-x*x))
   p=lo.matrix.translation-start;p-=axis*p.dot(axis);p.normalize()
   folded=Vector((.18 if side=='L'else -.18,.1 if k=='front'else -.1,-.9));folded-=axis*folded.dot(axis);folded.normalize()
   pole=p.slerp(folded,q);center=start+axis*x;joint=center+pole*h
   if joint.z<.14/.34 and h>.0001:
    upv=Vector((0,0,1));upv-=axis*upv.dot(axis);upv.normalize();lat=axis.cross(upv).normalized()
    if lat.x*(1 if side=='L'else -1)<0:lat.negate()
    c=max(-1,min(1,(.14/.34-center.z)/max(.00001,h*upv.z)))
    pole=upv*c+lat*math.sqrt(max(0,1-c*c));joint=center+pole*h
   orient(up,lo.matrix.translation,joint);orient(lo,tip.matrix.translation,start+axis*d)
   for bone,matrix in [(tip,tips[key]),(paw,feet[key])]:
    m=matrix.copy();m.translation=bone.matrix.translation;bone.matrix=m;bpy.context.view_layer.update()
 row={'phase':phase,'max_basis_scale_error':max(max(abs(v-1)for v in p.matrix_basis.to_scale())for p in bones),'paw_heights':[round(arm.pose.bones['DEF_'+k+'_paw.'+d].head.z*.34,4)for k in ['front','rear']for d in ['L','R']]};metrics.append(row)
 if phase==1:
  s.render.engine='CYCLES';s.cycles.samples=12;s.cycles.use_denoising=False;s.render.resolution_x=1000;s.render.resolution_y=650;s.render.resolution_percentage=100
  s.world=bpy.data.worlds.new('Neutral diagnostic world');s.world.color=(.4,.4,.4)
  mat=bpy.data.materials.new('Neutral clay audit');mat.diffuse_color=(.73,.72,.66,1)
  for o in list(s.objects):
   if o.type=='MESH':o.data.materials.clear();o.data.materials.append(mat)
  bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,.01));bpy.context.object.data.materials.append(mat)
  bpy.ops.object.camera_add(location=(10,-9,6));cam=bpy.context.object;cam.rotation_euler=(Vector((0,-.2,1.6))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=10;s.camera=cam
  bpy.ops.object.light_add(type='AREA',location=(2,-4,10));bpy.context.object.data.energy=1600;bpy.context.object.data.size=7
  s.render.filepath=str(R/'Review/sleep-solve-clay-diagnostic.png');bpy.ops.render.render(write_still=True)
(R/'Review/sleep-solve-rehearsal.json').write_text(json.dumps({'type':'Blender geometric rehearsal, not Unity clip/skin validation','samples':metrics,'native_unity':'UNRUN'},indent=2))

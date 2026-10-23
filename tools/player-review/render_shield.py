"""Offline actual mesh fit check; the shader and live animation require Unity."""
from pathlib import Path
import bpy,sys,re,math,struct,numpy as np
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/village'))
from native import *
from build import Sources
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.fbx(filepath=str(ASSETS/'Models/Amaterasu.fbx'))
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data_clear();rig.scale=(.34,)*3
for pb in rig.pose.bones:pb.matrix_basis=Matrix.Identity(4)
for o in list(bpy.data.objects):
 if o!=rig and (o.type!='MESH' or not o.find_armature()):bpy.data.objects.remove(o,do_unlink=True)
neutral=bpy.data.materials.new('Neutral wolf - geometry inspection only');neutral.diffuse_color=(.70,.68,.61,1)
for o in bpy.data.objects:
 if o.type=='MESH':o.data.materials.clear();o.data.materials.append(neutral)
s=Scene(ASSETS/'Scenes/Windflower.unity');src=Sources(s)
anchor=bpy.data.objects.new('Motor-frame mount - never legacy socket',None);bpy.context.collection.objects.link(anchor);anchor.location=(0,.10,1.46);anchor.rotation_euler=(math.radians(55),0,0);anchor.scale=(.85,)*3
for n in range(1102,1108):
 raw=src.native[n];v=src.positions(n);v=np.column_stack([v[:,0],-v[:,2],v[:,1]]);ix=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([a-fA-F0-9]+)',raw)[1]),dtype='<u4' if 'm_IndexFormat: 1' in raw else '<u2').reshape(-1,3)
 mesh=bpy.data.meshes.new('Actual Sundial '+str(n));mesh.from_pydata(v,[],ix);mesh.update();obj=bpy.data.objects.new(mesh.name,mesh);bpy.context.collection.objects.link(obj);obj.parent=anchor
 mat=bpy.data.materials.new('Engraved gold' if n>1103 else 'Vermilion disc');mat.diffuse_color=(.73,.44,.12,1) if n>1103 else (.40,.12,.055,1);mesh.materials.append(mat)
for i in range(10):
 curve=bpy.data.curves.new('Spectral tongue','CURVE');curve.dimensions='3D';curve.bevel_depth=.018;curve.bevel_resolution=1;poly=curve.splines.new('POLY');poly.points.add(23)
 for j,point in enumerate(poly.points):
  u=j/23;a=1.2*(1.3 if i%2==0 else -.95)+i*math.tau/10+u*.85;r=.49+u*.31+math.sin(u*7+3.6+i)*.018*u;z=-.18-u*.10+math.sin(u*5+2.4+i)*.075*u
  point.co=(math.cos(a)*r,-z,math.sin(a)*r,1);point.radius=max(.02,math.sin(math.pi*u))
 ob=bpy.data.objects.new('Spectral tongue',curve);bpy.context.collection.objects.link(ob);ob.parent=anchor
 mat=bpy.data.materials.new('Emission ember');mat.use_nodes=True;bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(1,.28,.015,1) if i%3 else (.1,.65,1,1);bs.inputs['Emission Color'].default_value=bs.inputs['Base Color'].default_value;bs.inputs['Emission Strength'].default_value=2;curve.materials.append(mat)
bpy.ops.mesh.primitive_plane_add(size=100);bpy.context.object.location.z=-.01
for p,e in [((2,-5,6),800),((-4,3,5),600)]:bpy.ops.object.light_add(type='AREA',location=p);bpy.context.object.data.energy=e;bpy.context.object.data.size=4
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=False;scene.world.color=(.3,.3,.3);scene.render.resolution_x=1100;scene.render.resolution_y=800;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='JPEG'
bpy.ops.object.camera_add(location=(4,6,3.5));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,1))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4.6;scene.camera=cam
out=ROOT/'tools/player-review/previews';out.mkdir(exist_ok=True);scene.render.filepath=str(out/'shield-back-fit-blender.jpg');bpy.ops.render.render(write_still=True)

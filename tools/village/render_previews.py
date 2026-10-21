"""Blender-only asset previews; explicitly not renders of the Unity game.
Run after build.py: blender -b -t 4 -P tools/village/render_previews.py
"""
import bpy,math
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
DEST=ROOT/'tools/village/previews';DEST.mkdir(exist_ok=True)
def reset():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def add(name,position=(0,0,0)):
 p=np.load('/tmp/sunward-'+name+'.npz');v=p['vertices'];v=np.column_stack([v[:,0],-v[:,2],v[:,1]])
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(v,[],p['triangles']);mesh.update();obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);obj.location=position
 attr=mesh.color_attributes.new(name='Pigment',type='FLOAT_COLOR',domain='POINT')
 for datum,col in zip(attr.data,p['colors']):datum.color=(*np.clip(col,0,1),1)
 mat=bpy.data.materials.new(name);mat.use_nodes=True;nodes=mat.node_tree.nodes;bs=nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.75;vc=nodes.new('ShaderNodeVertexColor');vc.layer_name='Pigment';mat.node_tree.links.new(vc.outputs['Color'],bs.inputs['Base Color']);mesh.materials.append(mat)
 for poly in mesh.polygons:poly.use_smooth=True
 return obj
def render(name,look,camera,scale,res=(1500,750)):
 bpy.ops.mesh.primitive_plane_add(size=200);floor=bpy.context.object;mat=bpy.data.materials.new('Neutral preview floor');mat.diffuse_color=(.16,.19,.16,1);floor.data.materials.append(mat)
 bpy.ops.object.camera_add(location=camera);cam=bpy.context.object;cam.rotation_euler=(Vector(look)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale;bpy.context.scene.camera=cam
 for pos,power,size in [((-3,-5,9),1400,7),((4,2,5),700,6)]:
  bpy.ops.object.light_add(type='AREA',location=pos);bpy.context.object.data.energy=power;bpy.context.object.data.size=size
 scene=bpy.context.scene;scene.world.color=(.3,.3,.3);scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False;scene.render.resolution_x=res[0];scene.render.resolution_y=res[1];scene.render.resolution_percentage=100;scene.render.image_settings.file_format='JPEG';scene.render.image_settings.quality=88;scene.render.filepath=str(DEST/(name+'.jpg'));bpy.ops.render.render(write_still=True)
reset()
for i,name in enumerate(['Elder','Merchant','ShrineMaiden','Samurai','Chef','Geisha','Gardener']):add('Resident-'+name,((i-3)*1.4,0,0))
render('villagers-blender',(0,0,1.0),(4,-15,7),11.6,(1800,720))
reset()
for part in ['joined','recessed','laid','closed']:add('House-24-'+part)
render('house-blender',(0,0,1.7),(9,-12,8),10)
reset()
for i in range(4):
 o=add('Carved-rock-'+str(i),((i-1.5)*1.45,0,0));o.scale=(1.1,1.1,.9)
render('rocks-blender',(0,0,.5),(4,-9,5),7)
reset();add('Tree-0-bark');add('Tree-0-canopy');render('cherry-blender',(0,0,2.6),(6,-9,6),7.3,(950,950))
reset()
for i in range(4):add('flower-'+str(i),((i-1.5)*.6,0,0))
add('Bamboo-0',(1.65,.25,0));render('plants-blender',(0,0,.9),(4,-7,4),4.6,(1200,800))

reset()
for part in ['joined','cast','hanging']:add('Arena-'+part)
render('bell-blender',(0,0,1.4),(4,-7,4),3.9,(900,1100))

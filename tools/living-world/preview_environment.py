"""Render actual authored environment meshes, independent of Unity (clearly labeled)."""
from pathlib import Path
import bpy,numpy as np,math,json,sys
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'tools/living-world/previews';OUT.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
material=bpy.data.materials.new('Authored vertex paint');material.use_nodes=True;n=material.node_tree.nodes;l=material.node_tree.links;bs=n.get('Principled BSDF');v=n.new('ShaderNodeVertexColor');v.layer_name='Paint';l.new(v.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.86

def load(name,offset=(0,0,0),scale=(1,1,1)):
 d=np.load('/tmp/sunward-'+name+'.npz');verts=d['vertices']*scale+offset;v=np.column_stack([verts[:,0],-verts[:,2],verts[:,1]])
 m=bpy.data.meshes.new(name);m.from_pydata(v,[],d['triangles']);m.update();a=m.color_attributes.new(name='Paint',type='FLOAT_COLOR',domain='POINT');c=np.column_stack([d['colors'][:,:3],np.ones(len(v))]);a.data.foreach_set('color',c.ravel());o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o);m.materials.append(material)
 return o
load('Bamboo-1-culms',(-4,0,0));load('Bamboo-1-leaf-fans',(-4,0,0));load('Bamboo-5-culms',(-1.5,0,0));load('Bamboo-5-leaf-fans',(-1.5,0,0))
load('Arena-cedar-grain-0',(1,1.2,0),(.36,2.2,.36));load('Arena-cedar-grain-1',(2.5,1.2,0),(.36,2.2,.36))
load('Bridge-sawn-planks',(7,0,0),(.60,.75,.90))
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.05));floor=bpy.context.object;floor.data.materials.append(bpy.data.materials.new('Paper ground'));floor.data.materials[0].diffuse_color=(.23,.25,.17,1)
bpy.ops.object.light_add(type='SUN',location=(0,-10,20));bpy.context.object.rotation_euler=(.38,-.45,-.50);bpy.context.object.data.energy=2.5;bpy.context.object.data.angle=.2
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False;scene.world.use_nodes=True;bg=scene.world.node_tree.nodes.get('Background');bg.inputs['Color'].default_value=(.55,.60,.65,1);bg.inputs['Strength'].default_value=.7
bpy.ops.object.camera_add(location=(12,-16,11));cam=bpy.context.object;target=Vector((1,0,1.8));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=17.5;scene.camera=cam
text=bpy.data.curves.new('Preview limitation','FONT');text.body='BLENDER ASSET PREVIEW — NOT UNITY';text.size=.18;obj=bpy.data.objects.new('Preview label',text);bpy.context.collection.objects.link(obj);obj.parent=cam;obj.location=(-8.2,4.3,-4)
mat=bpy.data.materials.new('Label');mat.use_nodes=True;nodes=mat.node_tree.nodes;nodes.clear();e=nodes.new('ShaderNodeEmission');e.inputs['Color'].default_value=(1,.94,.73,1);o=nodes.new('ShaderNodeOutputMaterial');mat.node_tree.links.new(e.outputs[0],o.inputs[0]);text.materials.append(mat)
scene.render.resolution_x=1440;scene.render.resolution_y=840;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='JPEG';scene.render.filepath=str(OUT/'environment-details-blender.jpg');scene.view_settings.view_transform='Standard'
if '--waterfall-only' not in sys.argv:bpy.ops.render.render(write_still=True)
# Separate close view of the spillway and source cleft, using the same saved meshes.
for ob in list(bpy.context.scene.objects):
 if ob.type=='MESH' and ob!=floor:ob.hide_render=True
load('Cascade-sculpted-source-cliff');load('Cascade-layered-sheet');load('Cascade-upper-feeder')
cam.location=(8,13,9);target=Vector((0,-.7,2.6));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=13.6
obj.location=(-6.4,3.6,-4);text.size=.13;text.body='BLENDER GEOMETRY PREVIEW — WATER MOTION REQUIRES UNITY'
scene.render.filepath=str(OUT/'waterfall-source-blender.jpg');bpy.ops.render.render(write_still=True)

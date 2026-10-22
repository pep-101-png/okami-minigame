"""Offline Blender art preview of authored spirit geometry (not Unity footage)."""
import bpy,math,sys
from pathlib import Path
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/living-world'))
from combat import parts,PALETTES
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for i,kind in enumerate(PALETTES):
 for name,(source,p) in parts(kind).items():
  v=np.array(source.v)+p;v=np.column_stack([v[:,0],-v[:,2],v[:,1]])
  mesh=bpy.data.meshes.new(kind+' '+name);mesh.from_pydata(v,[],source.tri);mesh.update()
  o=bpy.data.objects.new(kind+' '+name,mesh);bpy.context.collection.objects.link(o);o.location.x=(i-2.5)*1.7
  c=mesh.color_attributes.new(name='Pigment',type='FLOAT_COLOR',domain='POINT')
  for d,col in zip(c.data,source.c):d.color=(*np.clip(col,0,1),1)
  mat=bpy.data.materials.new(kind+' paint');mat.use_nodes=True;nodes=mat.node_tree.nodes;bs=nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.8;vc=nodes.new('ShaderNodeVertexColor');vc.layer_name='Pigment';mat.node_tree.links.new(vc.outputs['Color'],bs.inputs['Base Color']);mesh.materials.append(mat)
  for f in mesh.polygons:f.use_smooth=True
bpy.ops.mesh.primitive_plane_add(size=200);floor=bpy.context.object;mat=bpy.data.materials.new('Neutral');mat.diffuse_color=(.18,.17,.13,1);floor.data.materials.append(mat)
bpy.ops.object.camera_add(location=(1,-15,6));cam=bpy.context.object;cam.rotation_euler=(Vector((0,0,.8))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=11.2;bpy.context.scene.camera=cam
for pos,power,size in [((-3,-5,9),1500,7),((4,2,5),700,6)]:
 bpy.ops.object.light_add(type='AREA',location=pos);bpy.context.object.data.energy=power;bpy.context.object.data.size=size
scene=bpy.context.scene;scene.world.color=(.3,.3,.3);scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False;scene.render.resolution_x=1800;scene.render.resolution_y=700;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='JPEG';scene.render.image_settings.quality=90
out=ROOT/'tools/living-world/previews';out.mkdir(exist_ok=True);scene.render.filepath=str(out/'spirits-blender.jpg');bpy.ops.render.render(write_still=True)

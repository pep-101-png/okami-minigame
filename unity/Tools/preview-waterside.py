"""Inspect exported C# repair geometry in Blender. This is not a Unity render."""
import bpy
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=str(R/'Review/waterside-geometry.obj'),forward_axis='Y',up_axis='Z')
for mat in bpy.data.materials:
 mat.use_nodes=True;p=mat.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.86
 if mat.name.startswith('water'):
  p.inputs['Base Color'].default_value=(.16,.36,.30,1);p.inputs['Roughness'].default_value=.22;p.inputs['Transmission Weight'].default_value=.25;p.inputs['IOR'].default_value=1.33
 else:
  noise=mat.node_tree.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=12
  bump=mat.node_tree.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.12;bump.inputs['Distance'].default_value=.04;mat.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);mat.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=24;s.cycles.use_denoising=False;s.render.resolution_x=1400;s.render.resolution_y=900;s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('Neutral inspection');s.world.color=(.5,.5,.5)
bpy.ops.object.light_add(type='AREA',location=(-13,17,17));bpy.context.object.data.energy=3500;bpy.context.object.data.size=12
bpy.ops.object.camera_add(location=(-4,8,12));cam=bpy.context.object;cam.rotation_euler=(Vector((-20,23,-.2))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=27;s.camera=cam
s.render.filepath=str(R/'Review/waterside-geometry-diagnostic.png');bpy.ops.render.render(write_still=True)

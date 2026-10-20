"""Neutral geometry inspection only: not a Unity render or finished-art screenshot."""
import bpy
from pathlib import Path
from mathutils import Vector
r=Path(__file__).resolve().parents[1]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.wm.obj_import(filepath=str(r/'Review/bridge-relocation-geometry.obj'),forward_axis='Y',up_axis='Z')
s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=20;s.cycles.use_denoising=False;s.render.resolution_x=1400;s.render.resolution_y=900;s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('Neutral geometry review');s.world.color=(.55,.55,.55)
bpy.ops.object.light_add(type='AREA',location=(-28,0,19));bpy.context.object.data.energy=2800;bpy.context.object.data.size=13
bpy.ops.object.camera_add(location=(-11,-6,19));cam=bpy.context.object;cam.rotation_euler=(Vector((-28,12,0))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=29;s.camera=cam
s.render.filepath=str(r/'Review/bridge-clearance-geometry-diagnostic.png');bpy.ops.render.render(write_still=True)

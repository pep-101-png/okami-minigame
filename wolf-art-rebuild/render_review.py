"""Render detail and profile views from the finished authored model."""
import bpy
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(root/'wolf.blend'));scene=bpy.context.scene;camera=scene.camera;scene.frame_set(1)
scene.render.resolution_x=1000;scene.render.resolution_y=900;scene.cycles.samples=64
camera.location=(10,-6.5,5.9);camera.rotation_euler=(Vector((0,-2.7,4.37))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=3.8
scene.render.filepath=str(root/'review'/'face.png');bpy.ops.render.render(write_still=True)
camera.location=(13,.20,5.4);camera.rotation_euler=(Vector((0,-.10,2.75))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=10.4;scene.render.resolution_x=1200;scene.render.resolution_y=900;scene.cycles.samples=64
scene.render.filepath=str(root/'review'/'profile.png');bpy.ops.render.render(write_still=True)

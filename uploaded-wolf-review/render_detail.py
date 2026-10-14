from pathlib import Path
import bpy
from mathutils import Vector
root=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(root/'colored-rigged.blend'))
scene=bpy.context.scene;scene.frame_set(1);camera=scene.camera
camera.location=(10,-6.5,5.9);camera.rotation_euler=(Vector((0,-2.75,4.35))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=3.65
scene.render.resolution_x=1000;scene.render.resolution_y=900;scene.cycles.samples=96
scene.render.filepath=str(root/'face-detail.png');bpy.ops.render.render(write_still=True)

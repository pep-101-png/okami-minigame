"""Render all three authored tail states from the saved model."""
import bpy,os
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(root/'wolf.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['DivineWolfRig'];camera=scene.camera
camera.location=(13,.2,5.4);camera.rotation_euler=(Vector((0,.1,2.65))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.ortho_scale=10.4
scene.render.resolution_x=800;scene.render.resolution_y=600;scene.cycles.samples=20
full=os.environ.get('TAIL_FULL','0')=='1'
for clip,length in [('Idle',96),('Walk',48),('Run',30)]:
 rig.animation_data.action=bpy.data.actions[clip]
 for frame in (range(1,length+1,2 if clip=='Idle' else 1) if full else [1,length//3,2*length//3]):
  scene.frame_set(frame);scene.render.filepath=f'/tmp/soft-tail-{clip.lower()}-{frame:02}.png';bpy.ops.render.render(write_still=True)

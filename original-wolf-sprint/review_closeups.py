import bpy
from pathlib import Path
from mathutils import Vector
s=bpy.context.scene;r=bpy.data.objects['WOLF_RIG'];r.animation_data.action=bpy.data.actions['Sprint']
for o in bpy.data.collections['04 · Preview studio (not part of wolf)'].objects:o.hide_set(False)
s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=12;s.render.resolution_x=800;s.render.resolution_y=650;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';c=s.camera;c.data.type='ORTHO';c.data.ortho_scale=4.6;c.location=(-7,-10,2.7);c.rotation_euler=(Vector((0,-1.4,2.35))-c.location).to_track_quat('-Z','Y').to_euler();p=Path(__file__).resolve().parent/'review/shoulder';p.mkdir(exist_ok=True)
for f in [29,31,32]:
 s.frame_set(f);s.render.filepath=str(p/f'{f:03d}.png');bpy.ops.render.render(write_still=True)
print('SHOULDER_REVIEW_COMPLETE',flush=True)

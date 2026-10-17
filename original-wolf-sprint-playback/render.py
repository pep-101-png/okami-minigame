import bpy,os
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;s=bpy.context.scene;r=bpy.data.objects['WOLF_RIG'];bpy.context.window.view_layer=s.view_layers['FULL · Painted wind']
for o in bpy.data.collections['04 · Preview studio (not part of wolf)'].objects:o.hide_set(False)
bpy.ops.mesh.primitive_plane_add(size=40,location=(0,0,-.012));mat=bpy.data.materials.new('TEMP floor');mat.diffuse_color=(.20,.19,.18,1);bpy.context.object.data.materials.append(mat)
s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=12;s.render.resolution_x=900;s.render.resolution_y=620;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';cam=s.camera;cam.data.type='ORTHO'
for view,loc,target,scale in [('side',(15,1.5,4.5),(0,1.5,2.5),14.3),('neck',(9,-5.5,5),(0,-2.25,3.8),5.8),('front',(0,-14,4.5),(0,-.5,2.65),9.6)]:
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
 for action in ['Sprint_Polished','Sprint_Fluid']:
  r.animation_data.action=bpy.data.actions[action];out=R/'review/renders'/action/view;out.mkdir(parents=True,exist_ok=True)
  frames=range(1,33)if action=='Sprint_Fluid'and view!='front'else[1,5,9,13,17,21,25,29]
  for f in frames:
   path=out/f'{f:03}.png'
   if path.exists()and path.read_bytes()[-8:]==b'IEND\xaeB\x60\x82':continue
   s.frame_set(f);s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
print('REVIEW_RENDER_COMPLETE',flush=True)

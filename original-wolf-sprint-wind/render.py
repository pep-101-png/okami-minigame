import bpy,sys,os
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;s=bpy.context.scene;r=bpy.data.objects['WOLF_RIG'];r.animation_data.action=None
if r.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
for p in r.pose.bones:p.matrix_basis.identity()
bpy.context.view_layer.update()
for o in [o for o in s.objects if o.type=='MESH'and o.parent==r]:
 for m in list(o.modifiers):
  if m.type=='SUBSURF':bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name)
for o in bpy.data.collections['04 · Preview studio (not part of wolf)'].objects:o.hide_set(False)
bpy.ops.mesh.primitive_plane_add(size=40,location=(0,0,-.012));mat=bpy.data.materials.new('TEMP floor');mat.diffuse_color=(.20,.19,.18,1);bpy.context.object.data.materials.append(mat)
s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=8;s.render.resolution_x=960;s.render.resolution_y=640;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG';cam=s.camera;cam.data.type='ORTHO'
full=os.environ.get('FULL')=='1';views=[('side',(15,1.8,4.5),(0,1.8,2.5),15),('rear',(7,14,5),(0,2,2.7),12),('neck',(9,-5.5,5),(0,-2.25,3.8),5.8)]
for view,loc,target,scale in views:
 if os.environ.get('RENDER_VIEW')and view!=os.environ['RENDER_VIEW']:continue
 cam.location=loc;cam.rotation_euler=(Vector(target)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale
 for action in (['Sprint_Polished']if full else ['Sprint','Sprint_Polished']):
  r.animation_data.action=bpy.data.actions[action];out=R/'review'/('final2'if full else 'keys')/action/view;out.mkdir(parents=True,exist_ok=True)
  frames=range(1,33)if full else [1,9,17,25]
  for f in frames:
   if full and(out/f'{f:03}.png').exists()and(out/f'{f:03}.png').read_bytes()[-8:]==b'IEND\xaeB\x60\x82':continue
   s.frame_set(f);s.render.filepath=str(out/f'{f:03}.png');bpy.ops.render.render(write_still=True)
print('RENDERS_DONE',flush=True)

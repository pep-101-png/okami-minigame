import bpy,math,os,json
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;main=bpy.data.scenes['01 · Action inspection'];demo=bpy.data.scenes['02 · Movement showcase'];bpy.context.window.scene=main;r=bpy.data.objects['WOLF_RIG'];bpy.context.window.view_layer=main.view_layers['FULL · Painted wind'];main.view_layers['FAST · Lightweight wind'].use=False
for o in bpy.data.collections['04 · Preview studio (not part of wolf)'].objects:o.hide_set(False)
# A review-only stage; never saved into the character scene.
me=bpy.data.meshes.new('TEMP · review floor');me.from_pydata([(-30,-30,-.012),(30,-30,-.012),(30,30,-.012),(-30,30,-.012)],[],[(0,1,2,3)]);floor=bpy.data.objects.new('TEMP · review floor',me);main.collection.objects.link(floor);me.materials.append(bpy.data.materials['DEMO · parchment stage'])
cam=bpy.data.objects.new('TEMP · review camera',bpy.data.cameras.new('TEMP · review camera'));main.collection.objects.link(cam);cam.data.type='ORTHO';cam.data.ortho_scale=12.3;main.camera=cam
for sc in [main,demo]:sc.render.engine='BLENDER_EEVEE_NEXT';sc.eevee.taa_render_samples=8;sc.render.resolution_x=800;sc.render.resolution_y=580;sc.render.resolution_percentage=100;sc.render.image_settings.file_format='PNG'
def render(sc,f,path):
 path.parent.mkdir(parents=True,exist_ok=True)
 if path.exists()and path.read_bytes()[-8:]==b'IEND\xaeB\x60\x82':return
 bpy.context.window.scene=sc;sc.frame_set(int(f),subframe=f%1);sc.render.filepath=str(path);bpy.ops.render.render(write_still=True)
for kind in ['Walk','Jog','Sprint']:
 for side in ['L','R']:
  name=kind+'_Turn_'+side;a=bpy.data.actions[name];r.animation_data.action=None
  for p in r.pose.bones:p.matrix_basis.identity()
  r.animation_data.action=a;N=int(a['cycle_frames'])
  for view,loc in [('front',(12,-8,6)),('rear',(-11,8,5.5))]:
   cam.location=loc;cam.rotation_euler=(Vector((0,0,2.4))-cam.location).to_track_quat('-Z','Y').to_euler()
   for i in range(4):render(main,1+i*N/4,R/f'review/renders/{name}/{view}-{i}.png')
for side in ['L','R']:
 name='Idle_Turn_'+side+'90';r.animation_data.action=bpy.data.actions[name];cam.location=(12,-8,6);cam.rotation_euler=(Vector((0,0,2.4))-cam.location).to_track_quat('-Z','Y').to_euler()
 for i,f in enumerate([1,55,109,163,217]):render(main,f,R/f'review/renders/{name}/{i}.png')
r.animation_data.action=bpy.data.actions['Idle_Natural'];cam.location=(0,-14,5);cam.rotation_euler=(Vector((0,-.5,2.7))-cam.location).to_track_quat('-Z','Y').to_euler()
for i,f in enumerate([1,121,241,361]):render(main,f,R/f'review/renders/Idle_Natural/{i}.png')
for f in [1,265,577,781,1120,1355,1740,1855,2150,2260,1621,2001,2415,2517,2721]:render(demo,f,R/f'review/renders/Showcase/{f:04}.png')
print('ALL_DIRECTIONS_AND_SHOWCASE_RENDERED',flush=True)

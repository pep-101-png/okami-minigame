import bpy,json,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;s=bpy.data.scenes['01 · Action inspection'];bpy.context.window.scene=s;r=bpy.data.objects['WOLF_RIG'];bpy.context.window.view_layer=s.view_layers['FULL · Painted wind'];s.view_layers['FAST · Lightweight wind'].use=False
for o in bpy.data.collections['04 · Preview studio (not part of wolf)'].objects:o.hide_set(False)
stage=bpy.data.meshes.new('TEMP ground');stage.from_pydata([(-200,-200,-.012),(200,-200,-.012),(200,200,-.012),(-200,200,-.012)],[],[(0,1,2,3)]);o=bpy.data.objects.new('TEMP ground',stage);s.collection.objects.link(o);stage.materials.append(bpy.data.materials['DEMO · parchment stage'])
follow=bpy.data.objects.new('TEMP follow',None);s.collection.objects.link(follow);con=follow.constraints.new('COPY_LOCATION');con.target=r;con.subtarget='CTRL_root';con.use_z=False
for o in list(s.objects):
 if o.type=='LIGHT':o.parent=follow
cam=bpy.data.objects.new('TEMP camera',bpy.data.cameras.new('TEMP camera'));s.collection.objects.link(cam);cam.parent=follow;cam.data.type='ORTHO';cam.data.ortho_scale=14.5;s.camera=cam
s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.taa_render_samples=4;s.render.resolution_x=720;s.render.resolution_y=560;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
# The renderer explicitly samples the same wind level without transient Action=None driver relations.
r['movement_wind_level']=0.0
for o in list(bpy.data.collections['05 · Sprint wind — separate effect'].objects)+list(bpy.data.collections['06 · Lightweight wind preview (viewport only)'].objects):
 if o.animation_data:
  for fc in o.animation_data.drivers:
   for v in fc.driver.variables:
    if v.name=='gate':v.targets[0].data_path='["movement_wind_level"]'
report=json.load(open(R/'review/authoring.json'))['actions'];names=sys.argv[sys.argv.index('--')+1:]if'--'in sys.argv else list(report)
for name in names:
 a=bpy.data.actions[name];r.animation_data.action=None
 for p in r.pose.bones:p.matrix_basis.identity()
 r.animation_data.action=a;r['movement_wind_level']=float(a.get('movement_wind_level',0));d=report[name];N=d['N'];frames=sorted(set([1]+[1+round(N*v)for v in [.16,.32,.50,.68,.84,1]]))
 for view,loc in [('side',(12,0,4.7)),('rear',(-9,8,5.8))]:
  cam.location=loc;cam.rotation_euler=(Vector((0,0,2.7))-cam.location).to_track_quat('-Z','Y').to_euler()
  for i,f in enumerate(frames):
   path=R/f'review/final-renders/{name}/{view}-{i}.png';path.parent.mkdir(parents=True,exist_ok=True);s.frame_set(f);s.render.filepath=str(path);bpy.ops.render.render(write_still=True)
 print('REVIEW_RENDERED',name,flush=True)

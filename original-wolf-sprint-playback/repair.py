import bpy,math,time,statistics,hashlib,json
from pathlib import Path
from mathutils import Quaternion
R=Path(__file__).resolve().parent;src=R.parent/'original-wolf-sprint-wind/Amaterasu-Movement.blend';assert hashlib.sha256(src.read_bytes()).hexdigest()=='005c591cc810cfec7cc352c441ab3227d6e140ba578be9ef768b5750a488f57e'
bpy.ops.wm.open_mainfile(filepath=str(src));r=bpy.data.objects['WOLF_RIG'];s=bpy.context.scene
r.animation_data.action=None
if r.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
for p in r.pose.bones:p.matrix_basis.identity()
bpy.context.view_layer.update();headrest=r.pose.bones['CTRL_head'].matrix.to_quaternion().copy()
# Resolve the measured evaluation bottleneck without changing the already subdivided surface.
cache=[]
for o in [o for o in s.objects if o.type=='MESH'and o.parent==r]:
 for m in list(o.modifiers):
  if m.type=='SUBSURF':
   assert m.subdivision_type=='SIMPLE'and m.levels==1
   original=o.data;original.use_fake_user=True;original.name='ORIGINAL_BASE · '+o.name;o.data=original.copy();o.data.name='Cached existing bend resolution · '+o.name
   bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name);cache.append(o.name)
a=bpy.data.actions['Sprint_Polished'].copy();a.name='Sprint_Fluid';a.use_fake_user=True;a.asset_mark();allowed=['CTRL_neck_base','CTRL_neck_upper','CTRL_head']
for fc in list(a.fcurves):
 if any('"'+n+'"'in fc.data_path for n in allowed):a.fcurves.remove(fc)
r.animation_data.action=a
for f in range(1,34):
 t=((f-1)%32)/32;w=lambda p:math.sin(math.tau*(t-p));s.frame_set(f)
 # Counter-flexion creates changing curvature instead of rocking the neck as one rod.
 for n,base,amp,lag in [('CTRL_neck_base',6,13,.15),('CTRL_neck_upper',2,-10,.27)]:
  p=r.pose.bones[n];p.rotation_euler=(math.radians(base+amp*w(lag)),math.radians(.35*w(lag+.08)),math.radians(.6*w(lag+.12)));p.keyframe_insert('rotation_euler',frame=f)
 p=r.pose.bones['CTRL_head'];p.rotation_euler=(0,0,0);p.location=(0,0,0);p.scale=(1,1,1);bpy.context.view_layer.update();m=p.matrix.copy()
 # Partial gaze stabilisation retains natural neck inheritance; no exact world lock.
 goal=Quaternion((1,0,0),math.radians(3+3.2*w(.38)))@headrest;q=m.to_quaternion().slerp(goal,.58);target=q.to_matrix().to_4x4();target.translation=m.translation;p.matrix=target
 for path in ['rotation_euler','location','scale']:p.keyframe_insert(path,frame=f)
for fc in a.fcurves:
 if not any('"'+n+'"'in fc.data_path for n in allowed):continue
 points=fc.keyframe_points
 for i,k in enumerate(points):
  j=i%32;slope=(points[(j+1)%32].co.y-points[(j-1)%32].co.y)*.5;k.interpolation='BEZIER';k.handle_left_type='FREE';k.handle_right_type='FREE';k.handle_left=(k.co.x-1/3,k.co.y-slope/3);k.handle_right=(k.co.x+1/3,k.co.y+slope/3)
 if not any(m.type=='CYCLES'for m in fc.modifiers):fc.modifiers.new('CYCLES')
a['description']='Distributed counter-flexion and partial head stabilisation. Approved leg, tail, body and timing tracks retained.'
# Separate inexpensive viewport option. Finished wind stays unchanged and renderable.
full=bpy.data.collections['05 · Sprint wind — separate effect'];settings=bpy.data.collections.new('05a · Wind settings');s.collection.children.link(settings);ctrl=bpy.data.objects['SPRINT_WIND · speed control'];settings.objects.link(ctrl);full.objects.unlink(ctrl)
lite=bpy.data.collections.new('06 · Lightweight wind preview (viewport only)');s.collection.children.link(lite)
mat=bpy.data.materials.new('PREVIEW WIND · opaque pearl');mat.diffuse_color=(.73,.77,.76,1);mat.use_nodes=True;bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=mat.diffuse_color;bs.inputs['Roughness'].default_value=.95
for name in ['Wind ribbon 01','Wind ribbon 04','Wind ribbon 08']:
 o=bpy.data.objects[name];copy=o.copy();copy.data=o.data.copy();copy.name='PREVIEW · '+name;copy.data.materials.clear();copy.data.materials.append(mat);copy.hide_render=True;lite.objects.link(copy)
vl=s.view_layers[0];vl.name='FULL · Painted wind';vl.layer_collection.children[lite.name].exclude=True
fast=s.view_layers.new('FAST · Lightweight wind');fast.layer_collection.children[full.name].exclude=True
# Both layers retain the original textured wolf; only wind-preview quality differs.
bpy.context.window.view_layer=vl
s.render.fps=60;s.render.fps_base=1;s.sync_mode='FRAME_DROP';s.frame_set(1);s.frame_start=1;s.frame_end=1440
bpy.context.view_layer.objects.active=r;r.select_set(True);bpy.ops.object.mode_set(mode='POSE')
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':area.spaces.active.overlay.show_text=True
text=bpy.data.texts.new('SPRINT FLUID — START HERE');text.write('Sprint_Fluid is selected. Space plays. Top-right View Layer selector: FULL · Painted wind, or FAST · Lightweight wind (three opaque preview streaks). The original finished wind is retained for rendering. FPS is 60 with Frame Dropping. Neck controls now counter-flex, and head stabilisation is partial. Same visible subdivision has been precomputed on two meshes to remove per-frame subdivision work. Original base mesh datablocks remain packed as ORIGINAL_BASE; all previous Actions and the input project are preserved.\n')
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Amaterasu-Movement.blend'))
timing={}
for layer in s.view_layers:
 bpy.context.window.view_layer=layer;values=[]
 for j in range(76):
  start=time.perf_counter();s.frame_set(j%32+1);bpy.context.view_layer.update()
  if j>=12:values.append(1000*(time.perf_counter()-start))
 timing[layer.name]={'median_ms':statistics.median(values),'p95_ms':sorted(values)[60],'cpu_evaluation_only':True}
(R/'review/repair.json').write_text(json.dumps({'cached_subdivision':cache,'timing':timing,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest()},indent=2));print('REPAIRED',timing,flush=True)

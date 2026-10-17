import bpy,math,time,json,statistics,sys
from pathlib import Path
R=Path(__file__).resolve().parent
s=bpy.context.scene;r=bpy.data.objects['WOLF_RIG'];a=r.animation_data.action
out={'fps':s.render.fps,'fps_base':s.render.fps_base,'sync':s.sync_mode,'action':a.name,'range':list(a.frame_range),'interpolation':{},'bones':{},'weights':{},'viewport':[]}
for fc in a.fcurves:
 for k in fc.keyframe_points:out['interpolation'][k.interpolation]=out['interpolation'].get(k.interpolation,0)+1
for n in ['CTRL_chest','CTRL_neck_base','CTRL_neck_upper','CTRL_head','DEF_neck_base','DEF_neck_upper','DEF_head']:
 p=r.pose.bones[n];out['bones'][n]={'parent':p.parent.name if p.parent else None,'constraints':[{'type':c.type,'influence':c.influence,'target':getattr(c,'subtarget',''),'owner_space':getattr(c,'owner_space',''),'target_space':getattr(c,'target_space','')}for c in p.constraints],'rotation_mode':p.rotation_mode,'bbone_segments':p.bone.bbone_segments,'keys':{}}
 for f in [1,5,9,13,17,21,25,29]:
  s.frame_set(f);relative=p.parent.matrix.inverted()@p.matrix if p.parent else p.matrix
  out['bones'][n]['keys'][f]={'local_euler':list(p.rotation_euler),'relative_quat':list(relative.to_quaternion()),'head':list(p.head),'tail':list(p.tail)}
for o in [o for o in bpy.data.objects if o.type=='MESH'and o.parent==r]:
 rows=[]
 for v in o.data.vertices:
  p=o.matrix_world@v.co
  if -3.3<p.y<-1.4 and 2.8<p.z<4.9:
   rows.append({'xyz':list(p),'weights':{o.vertex_groups[g.group].name:round(g.weight,4)for g in v.groups if g.weight>.01}})
 out['weights'][o.name]=rows
for screen in bpy.data.screens:
 for area in screen.areas:
  if area.type=='VIEW_3D':out['viewport'].append({'screen':screen.name,'shading':area.spaces.active.shading.type,'scene_lights':area.spaces.active.shading.use_scene_lights,'scene_world':area.spaces.active.shading.use_scene_world,'overlay':area.spaces.active.overlay.show_overlays})
wind=bpy.data.collections['05 · Sprint wind — separate effect'];times={}
# CPU evaluation only, not GPU viewport FPS. Discard warm-up and keep frames identical.
for mode in ['full','hidden','no_drivers']:
 wind.hide_viewport=mode=='hidden'
 if mode=='no_drivers':
  wind.hide_viewport=False
  for seq in [bpy.data.objects,bpy.data.shape_keys]:
   for o in seq:
    if o.animation_data:
     for fc in o.animation_data.drivers:fc.mute=True
 samples=[]
 for j in range(76):
  start=time.perf_counter();s.frame_set(1+j%32);bpy.context.view_layer.update()
  if j>=12:samples.append(1000*(time.perf_counter()-start))
 times[mode]={'median_ms':statistics.median(samples),'p95_ms':sorted(samples)[int(len(samples)*.95)],'cpu_only':True}
out['timing']=times
out['drivers']=sum(len(o.animation_data.drivers)for seq in [bpy.data.objects,bpy.data.shape_keys]for o in seq if o.animation_data)
(R/'review/diagnosis.json').write_text(json.dumps(out,indent=2));print('DIAGNOSIS',json.dumps({k:v for k,v in out.items()if k not in ['weights','bones']}),flush=True)

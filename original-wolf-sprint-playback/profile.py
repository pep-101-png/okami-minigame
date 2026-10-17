import bpy,time,statistics,json
from pathlib import Path
R=Path(__file__).resolve().parent;results={}
for mode in ['baseline','no_subsurf','no_armature','no_mesh_modifiers','no_ik','wind_removed']:
 bpy.ops.wm.open_mainfile(filepath=str(R.parent/'original-wolf-sprint-wind/Amaterasu-Movement.blend'));s=bpy.context.scene;r=bpy.data.objects['WOLF_RIG'];meshes=[o for o in s.objects if o.type=='MESH'and o.parent==r]
 if mode=='wind_removed':
  for o in list(bpy.data.collections['05 · Sprint wind — separate effect'].objects):bpy.data.objects.remove(o,do_unlink=True)
 if mode=='no_ik':
  for p in r.pose.bones:
   for c in p.constraints:
    if c.type=='IK':c.mute=True
 for o in meshes:
  for m in o.modifiers:
   if(mode=='no_subsurf'and m.type=='SUBSURF')or(mode=='no_armature'and m.type=='ARMATURE')or mode=='no_mesh_modifiers':m.show_viewport=False
 timings=[]
 for j in range(40):
  start=time.perf_counter();s.frame_set(j%32+1);bpy.context.view_layer.update()
  if j>=8:timings.append(1000*(time.perf_counter()-start))
 results[mode]={'median_ms':statistics.median(timings),'p95_ms':sorted(timings)[30]};print('PROFILE',mode,results[mode],flush=True)
results['modifiers']={o.name:{'verts':len(o.data.vertices),'mods':[(m.name,m.type,m.show_viewport)for m in o.modifiers]}for o in meshes}
(R/'review/profile.json').write_text(json.dumps(results,indent=2))

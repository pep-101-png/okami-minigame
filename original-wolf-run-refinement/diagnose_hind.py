import bpy,json
from pathlib import Path
r=bpy.data.objects['WOLF_RIG'];r.animation_data.action=None;s=bpy.context.scene
if r.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
for p in r.pose.bones:p.matrix_basis.identity()
bpy.context.view_layer.update();meshes=[]
for name in ['Object_6','Object_2']:
 o=bpy.data.objects[name];bpy.context.view_layer.objects.active=o
 for m in list(o.modifiers):
  if m.type=='SUBSURF':bpy.ops.object.modifier_apply(modifier=m.name)
 rest=[o.matrix_world@v.co for v in o.data.vertices];edges=[]
 for e in o.data.edges:
  i,j=e.vertices;mid=(rest[i]+rest[j])/2;length=(rest[i]-rest[j]).length
  if .72<mid.y<1.95 and 1.7<mid.z<3.25 and length>.06:edges.append((i,j,length))
 meshes.append((o,edges))
results={}
for name in ['RUN','RUN_REFINED']:
 r.animation_data.action=bpy.data.actions[name];worst=(1,None);collapsed=[];critical=1
 for f in range(1,41):
  s.frame_set(f);dep=bpy.context.evaluated_depsgraph_get()
  for o,edges in meshes:
   ev=o.evaluated_get(dep);me=ev.to_mesh();ps=[ev.matrix_world@v.co for v in me.vertices]
   for i,j,length in edges:
    ratio=(ps[i]-ps[j]).length/length
    if o.name=='Object_6' and (i,j)==(1813,5761):critical=min(critical,ratio)
    if ratio<worst[0]:worst=(ratio,{'object':o.name,'frame':f,'edge':[i,j]})
    if ratio<.25:collapsed.append([o.name,f,i,j,ratio])
   ev.to_mesh_clear()
 results[name]={'minimum_relative_hip_edge_length':worst[0],'worst_sample':worst[1],'collapsed_hip_edge_samples':len(collapsed),'reported_thigh_collapse_edge_min_ratio':critical}
# A zero-compression hypothesis was tested earlier and was false: normal
# inner-knee creases remain. Check the actual reported collapsed thigh edge,
# while retaining the regional diagnostic rather than calling it perfect skinning.
assert results['RUN_REFINED']['reported_thigh_collapse_edge_min_ratio']>.25,results
Path(__file__).resolve().parent.joinpath('review/hind-deformation.json').write_text(json.dumps(results,indent=2));print('HIND_DEFORMATION',results,flush=True)

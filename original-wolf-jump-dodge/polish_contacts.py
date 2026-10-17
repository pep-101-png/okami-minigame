"""Sparse, local fixes for subframe paw/ground clearance; no original Actions touched."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;s=bpy.data.scenes['01 · Action inspection'];bpy.context.window.scene=s;r=bpy.data.objects['WOLF_RIG'];foot=bpy.data.objects['Object_11'];M=foot.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.copy();feet={}
for kind in ['front','rear']:
 for side,sign in [('L',1),('R',-1)]:feet[kind+'.'+side]=[v.index for v in foot.data.vertices if(p:=M@v.co).z<.17 and sign*p.x>.25 and(p.y<-.9 if kind=='front'else p.y>1)]
def soles():
 bpy.context.view_layer.update();ev=foot.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();out={k:min((ev.matrix_world@me.vertices[i].co).z for i in ids)for k,ids in feet.items()};ev.to_mesh_clear();return out
report={}
for name,d in json.load(open(R/'review/authoring.json'))['actions'].items():
 a=bpy.data.actions[name];r.animation_data.action=a;records={};bad=[]
 for j in range(d['N']*4+1):
  f=1+j*.25;s.frame_set(int(f),subframe=f%1);obs=soles();records[j]={k:r.pose.bones['CTRL_paw_'+k].location.copy()for k in feet}
  if min(obs.values())<.018:
   bad.append(j);pose={p.name:p.matrix_basis.copy()for p in r.pose.bones};r.animation_data.action=None
   for p in r.pose.bones:p.matrix_basis=pose[p.name]
   for repeat in range(3):
    z=soles()
    for key,value in z.items():
     if value<.035:p=r.pose.bones['CTRL_paw_'+key];m=p.matrix.copy();m.translation.z+=.035-value;p.matrix=m
   records[j]={k:r.pose.bones['CTRL_paw_'+k].location.copy()for k in feet};r.animation_data.action=a
 if bad:
  samples=sorted({max(0,min(d['N']*4,j+offset))for j in bad for offset in[-1,0,1]});r.animation_data.action=a
  for j in samples:
   f=1+j*.25
   for key,value in records[j].items():p=r.pose.bones['CTRL_paw_'+key];p.location=value;p.keyframe_insert('location',frame=f,group=p.name)
  for fc in a.fcurves:
   if 'CTRL_paw_'in fc.data_path and fc.data_path.endswith('location'):
    for p in fc.keyframe_points:p.interpolation='BEZIER';p.handle_left_type='AUTO_CLAMPED';p.handle_right_type='AUTO_CLAMPED'
  report[name]={'clearance_samples_corrected':len(bad),'local_samples_keyed':len(samples)}
  print('SPARSE_CLEARANCE_FIX',name,report[name],flush=True)
main=s;main.frame_set(1);main.animation_data if False else None
bpy.context.window.scene=bpy.data.scenes['03 · Jump and dodge showcase'];bpy.context.scene.frame_set(1)
(R/'review/contact-polish.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(R/'Amaterasu-Movement.blend'));print('M2_SUBFRAME_CLEARANCE_SAVED')

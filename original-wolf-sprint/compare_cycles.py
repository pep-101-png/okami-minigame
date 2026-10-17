"""Measure the pose/travel differences, rather than just comparing playback rates."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;r=bpy.data.objects['WOLF_RIG'];s=bpy.context.scene;o=bpy.data.objects['Object_11'];rest=[o.matrix_world@v.co for v in o.data.vertices];feet={}
for kind in ['front','rear']:
 for side,sgn in [('L',1),('R',-1)]:feet[kind+'.'+side]=[i for i,p in enumerate(rest)if p.z<.17 and sgn*p.x>.25 and(p.y<-.9 if kind=='front'else p.y>1)]
for ob in s.objects:
 if ob.type=='MESH'and ob!=o:
  for m in ob.modifiers:
   if m.type=='SUBSURF':m.show_viewport=False
out={}
for name,n in [('Jog',40),('Sprint',32)]:
 r.animation_data.action=bpy.data.actions[name];spans=[];air=0;arches=[]
 for i in range(4*n):
  f=1+i/4;s.frame_set(int(f),subframe=f-int(f));dep=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dep);me=ev.to_mesh();centers=[];zs=[]
  for ids in feet.values():
   ps=[ev.matrix_world@me.vertices[j].co for j in ids];centers.append(sum(ps,Vector())/len(ps));zs.append(min(p.z for p in ps))
  ev.to_mesh_clear();spans.append(max(p.y for p in centers)-min(p.y for p in centers));air+=int(all(z>.06 for z in zs))
  a=r.pose.bones['DEF_hips'].head;b=r.pose.bones['DEF_neck_base'].head;c=r.pose.bones['DEF_spine_mid'].head;t=(c.y-a.y)/(b.y-a.y);arches.append(c.z-(a.z+t*(b.z-a.z)))
 out[name]={'cycle_frames':n,'stride':r.animation_data.action['metres_per_second']*n/60,'ground_speed_source_units_per_second':r.animation_data.action['metres_per_second'],'maximum_fore_hind_paw_span':max(spans),'airborne_fraction':air/(4*n),'lumbar_arch_range':max(arches)-min(arches)}
assert out['Sprint']['maximum_fore_hind_paw_span']>out['Jog']['maximum_fore_hind_paw_span']*1.25,out
assert out['Sprint']['airborne_fraction']>out['Jog']['airborne_fraction']*1.5,out
assert out['Sprint']['lumbar_arch_range']>out['Jog']['lumbar_arch_range']*1.1,out
(ROOT/'review/movement-metrics.json').write_text(json.dumps(out,indent=2));print('DISTINCT_MOVEMENT_VERIFIED',out,flush=True)

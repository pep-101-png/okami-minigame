import bpy,json,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;r=bpy.data.objects['WOLF_RIG'];s=bpy.context.scene;r.animation_data.action=None
if r.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
for p in r.pose.bones:p.matrix_basis.identity()
bpy.context.view_layer.update();feet={};o=bpy.data.objects['Object_11'];rest=[o.matrix_world@v.co for v in o.data.vertices]
for kind in ['front','rear']:
 for side,sign in [('L',1),('R',-1)]:feet[kind+'.'+side]=[i for i,p in enumerate(rest)if p.z<.17 and sign*p.x>.25 and(p.y<-.9 if kind=='front'else p.y>1)]
# Disable unrelated geometry only on this throwaway review process.
for ob in s.objects:
 if ob.type=='MESH'and ob!=o:
  for mod in ob.modifiers:
   if mod.type=='SUBSURF':mod.show_viewport=False
r.animation_data.action=bpy.data.actions['Sprint']
def sample(f):
 s.frame_set(int(f),subframe=f-int(f));dep=bpy.context.evaluated_depsgraph_get();ev=o.evaluated_get(dep);me=ev.to_mesh();out={}
 for key,ids in feet.items():
  ps=[ev.matrix_world@me.vertices[i].co for i in ids];out[key]={'z':min(p.z for p in ps),'center':list(sum(ps,Vector())/len(ps))}
 ev.to_mesh_clear();return out
errors=[];slips=[];low=100;flight=[];old=None
for i in range(129):
 f=1+i/4;t=i/128;data=sample(f);all_air=True
 for key,v in data.items():
  offset={'front.R':0,'front.L':.09,'rear.R':.47,'rear.L':.56}[key];u=(t-offset)%1;d=.18 if key.startswith('front')else .16
  low=min(low,v['z']);all_air=all_air and v['z']>.06
  if u<d:
   errors.append(abs(v['z']-.035))
   if old:
    old_u=(t-1/128-offset)%1
    if old_u<u and old_u<d:slips.append(abs(v['center'][1]-old[key]['center'][1]-7.8/128))
 if all_air:flight.append(f)
 old=data
# Evaluate boundary velocity with matching fractional samples.
eps=.02;a=sample(33-eps);b=sample(33);c=sample(33+eps)
velocity={k:math.sqrt(sum(((c[k]['center'][j]-b[k]['center'][j])-(b[k]['center'][j]-a[k]['center'][j]))**2 for j in range(3)))/eps for k in feet}
report={'minimum_paw_z':low,'max_contact_floor_error_quarterframe':max(errors),'max_stance_slide_error_quarterframe':max(slips),'cycle_boundary_velocity_difference_per_frame':velocity,'airborne_samples':flight}
assert low>.02,report
assert max(errors)<.015,report
assert max(slips)<.01,report
assert max(velocity.values())<.01,report
(ROOT/'review/contacts.json').write_text(json.dumps(report,indent=2));print('CONTACT_AND_LOOP_CHECK',report,flush=True)

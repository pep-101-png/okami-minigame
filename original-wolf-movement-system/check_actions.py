import bpy,math,json
from pathlib import Path
from mathutils import Vector,Quaternion
R=Path(__file__).resolve().parent;bpy.context.window.scene=bpy.data.scenes['01 · Action inspection'];s=bpy.context.scene;s.frame_set(2);bpy.context.view_layer.update();s.frame_set(1);bpy.context.view_layer.update();r=bpy.data.objects['WOLF_RIG'];obj=bpy.data.objects['Object_11'];sp=json.loads((R/'review/authoring.json').read_text())['specs'];feet={}
for k in ['front','rear']:
 for side,sign in [('L',1),('R',-1)]:feet[k+'.'+side]=[v.index for v in obj.data.vertices if (p:=obj.matrix_world@v.co).z<.17 and sign*p.x>.25 and(p.y<-.9 if k=='front'else p.y>1)]
print('FOOT_IDS',{k:len(v)for k,v in feet.items()},flush=True)
def obs():
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();out={}
 for k,ids in feet.items():
  ps=[ev.matrix_world@me.vertices[i].co for i in ids];out[k]=(sum(ps,Vector())/len(ps),min(p.z for p in ps))
 ev.to_mesh_clear();return out
report={}
for name in ['Idle_Natural','Walk_Natural','Jog_Natural','Sprint_Fluid','Walk_Turn_L','Walk_Turn_R','Jog_Turn_L','Jog_Turn_R','Sprint_Turn_L','Sprint_Turn_R','Idle_Turn_L90','Idle_Turn_R90']:
 a=bpy.data.actions[name];r.animation_data.action=None
 for p in r.pose.bones:p.matrix_basis.identity()
 r.animation_data.action=a;N=int(a['cycle_frames']);samples=[];anchors={};slips=[];rotations={};ik=[]
 for j in range(4*N+1):
  f=1+j/4;s.frame_set(int(f),subframe=f%1);data=obs();row={'f':f,'min_z':min(v[1]for v in data.values())};samples.append(row)
  for key in feet:
   kind,side=key.split('.');p=r.pose.bones['DEF_'+kind+'_upper.'+side];q=p.matrix.to_quaternion();rotations.setdefault(key,[]).append(q.copy());lo=r.pose.bones['DEF_'+kind+'_lower.'+side];ik.append((lo.tail-r.pose.bones['MCH_target_'+key].head).length)
  if '_Turn_'in name and not name.startswith('Idle'):
   kind=name.split('_')[0];spec=sp[kind];t=(f-1)/N;seconds=t*N/60;w=a['yaw_rate_radians'];v=spec['v'];P=Vector((v/w*(1-math.cos(w*seconds)),-v/w*math.sin(w*seconds),0));Q=Quaternion((0,0,1),w*seconds)
   for key,(center,z)in data.items():
    u=(t-spec['offset'][key])%1;d=spec['d'][key.split('.')[0]]
    if .025<u<d-.025:
     pt=P+Q@center
     if key in anchors:slips.append((pt-anchors[key]).xy.length)
     anchors[key]=pt
    else:anchors.pop(key,None)
 loop=None
 if not a.get('one_shot',False):
  s.frame_set(1);first=obs();s.frame_set(N+1);last=obs();loop=max((first[k][0]-last[k][0]).length for k in feet)
 maxrot=max(math.degrees(2*math.acos(min(1,abs(q.dot(b)))))for vals in rotations.values()for q,b in zip(vals,vals[1:]))
 report[name]={'min_z':min(v['min_z']for v in samples),'max_quarter_frame_contact_drift':max(slips,default=0),'loop_error':loop,'max_quarter_frame_upper_leg_rotation_deg':maxrot,'max_ik_error':max(ik),'samples':len(samples)};print('ACTION_CHECK',name,report[name],flush=True)
(R/'review/action-checks.json').write_text(json.dumps(report,indent=2))

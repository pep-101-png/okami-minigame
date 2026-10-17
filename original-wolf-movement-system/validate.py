import bpy,ast,hashlib,json,math,time,statistics
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent
for file,names in [(R.parent/'original-wolf-run-refinement/refine_run.py',['action_hash']),(R.parent/'original-wolf-animation/animate.py',['geometry_hash','skeleton_hash','weight_hash'])]:
 for node in ast.parse(file.read_text()).body:
  if isinstance(node,ast.FunctionDef)and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),'<fingerprint>','exec'))
def preserved(path):
 global rig,meshes
 bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['WOLF_RIG'];meshes=[o for o in bpy.data.objects if o.type=='MESH'and o.parent==rig]
 return{'geometry':geometry_hash(),'rest_rig':skeleton_hash(),'weights':weight_hash(),'actions':{a.name:action_hash(a)for a in bpy.data.actions if a.name in ['Idle','Walk','Jog','Sprint','Sprint_Polished','Sprint_Fluid','Legacy_Run','Wind_Speed_Demo']},'textures':{i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest()for i in bpy.data.images if i.packed_file}}
old=preserved(R.parent/'original-wolf-sprint-playback/Amaterasu-Movement.blend');new=preserved(R/'Amaterasu-Movement.blend');assert old==new,[k for k in old if old[k]!=new[k]]
scene=bpy.data.scenes['02 · Movement showcase'];bpy.context.window.scene=scene;rig=bpy.data.objects['DEMO_WOLF_RIG'];obj=bpy.data.objects['DEMO · Object_11'];spec=json.loads((R/'review/authoring.json').read_text())['specs'];segments=json.loads((R/'review/demo.json').read_text())['segments'];feet={}
for kind in ['front','rear']:
 for side,sign in [('L',1),('R',-1)]:feet[kind+'.'+side]=[v.index for v in obj.data.vertices if(p:=obj.matrix_world@v.co).z<.17 and sign*p.x>.25 and(p.y<-.9 if kind=='front'else p.y>1)]
def observe():
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();out={}
 for key,ids in feet.items():
  ps=[ev.matrix_world@me.vertices[i].co for i in ids];out[key]=(sum(ps,Vector())/len(ps),min(p.z for p in ps))
 ev.to_mesh_clear();return out
def support(seg,f,key):
 family=seg['family'];phase=seg['phase']+(f-seg['start'])/seg['N']
 if family in spec:return float((phase-spec[family]['offset'][key])%1<spec[family]['d'][key.split('.')[0]])
 if family.startswith('Stand'):
  local=f-seg['start']+1;order=['front.L','rear.R','front.R','rear.L'];return 0. if any(order[j%4]==key and 13+j*16<=local<13+j*16+12.8 for j in range(12))else 1.
 return 1.
def smooth(u):u=max(0,min(1,u));return u*u*(3-2*u)
badik=[];rows=[];anchors={};slips=[];timing=[];scale_error=0;maxik=0;rotations={};wind=[]
for f in range(1,scene.frame_end+1):
 start=time.perf_counter();scene.frame_set(f);bpy.context.view_layer.update();timing.append((time.perf_counter()-start)*1000);data=observe();active=[seg for seg in segments if seg['start']<=f<=seg['end']];current=active[-1];i=segments.index(current);w=smooth((f-current['start'])/current['blend'])if current['blend']else 1;weights=[(segments[i-1],1-w),(current,w)]if i and w<1 else[(current,1)]
 for key,(pt,z)in data.items():
  conf=sum(wt*support(seg,f,key)for seg,wt in weights)
  if conf>.85 and z<.065:
   if key in anchors:slips.append({'f':f,'key':key,'distance':(pt-anchors[key]).xy.length})
   anchors[key]=pt.copy()
  else:anchors.pop(key,None)
  kind,side=key.split('.');up=rig.pose.bones['DEF_'+kind+'_upper.'+side];lo=rig.pose.bones['DEF_'+kind+'_lower.'+side];err=(lo.tail-rig.pose.bones['MCH_target_'+key].head).length;maxik=max(maxik,err)
  if err>.03:badik.append({'f':f,'key':key,'error':err,'action':current['action']})
  rotations.setdefault(key,[]).append(up.matrix.to_quaternion().copy())
 for n in ['CTRL_neck_base','CTRL_neck_upper','CTRL_head']:scale_error=max(scale_error,max(abs(x-1)for x in rig.pose.bones[n].scale))
 rows.append(min(v[1]for v in data.values()))
 if f%120==1:wind.append((f,rig['movement_wind_level']))
maxrotation=max(math.degrees(2*math.acos(min(1,abs(q.dot(b)))))for values in rotations.values()for q,b in zip(values,values[1:]));worst=sorted(slips,key=lambda x:x['distance'],reverse=True)[:20]
print('NUMERIC_SUMMARY',min(rows),scale_error,maxik,maxrotation,worst[:5],flush=True)
assert min(rows)>0, min(rows);assert scale_error<.001,scale_error
# Source actors and showcase actors really share geometry datablocks.
shared=all(bpy.data.objects['DEMO · '+o.name].data==o.data for o in meshes)
assert shared
out={'max_ik_by_action':{name:max((v['error']for v in badik if v['action']==name),default=0)for name in set(x['action']for x in badik)},'bad_ik':sorted(badik,key=lambda x:x['error'],reverse=True)[:30],'preserved':new,'demo_min_sole_z':min(rows),'demo_max_ik_error':maxik,'demo_max_frame_joint_rotation_deg':maxrotation,'neck_head_scale_error':scale_error,'worst_contact_step_drift':worst,'cpu_median_ms':statistics.median(timing[20:]),'cpu_p95_ms':sorted(timing[20:])[int(len(timing[20:])*.95)],'frames_tested':len(rows),'linked_geometry':shared,'wind_samples':wind}
(R/'review/validation.json').write_text(json.dumps(out,indent=2));assert maxik<.01, out['max_ik_by_action']
assert maxrotation<35,maxrotation
print('VALIDATION',json.dumps({k:v for k,v in out.items()if k not in ['preserved','wind_samples']}),flush=True)

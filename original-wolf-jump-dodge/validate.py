import bpy,math,ast,hashlib,json,time,statistics
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;SOURCE=R.parent/'original-wolf-movement-system/Amaterasu-Movement.blend'
for path,names in [(R.parent/'original-wolf-animation/animate.py',['geometry_hash','skeleton_hash','weight_hash','materials_hash']),(R.parent/'original-wolf-run-refinement/refine_run.py',['action_hash'])]:
 for node in ast.parse(path.read_text()).body:
  if isinstance(node,ast.FunctionDef)and node.name in names:exec(compile(ast.Module(body=[node],type_ignores=[]),'<existing fingerprints>','exec'))
def fingerprint(path):
 global rig,meshes
 bpy.ops.wm.open_mainfile(filepath=str(path));rig=bpy.data.objects['WOLF_RIG'];meshes=[o for o in bpy.data.objects if o.type=='MESH'and o.parent==rig]
 return{'geometry':geometry_hash(),'rig':skeleton_hash(),'weights':weight_hash(),'materials':materials_hash(),'textures':{i.name:hashlib.sha256(bytes(i.packed_file.data)).hexdigest()for i in bpy.data.images if i.packed_file},'actions':{a.name:action_hash(a)for a in bpy.data.actions}}
old=fingerprint(SOURCE);new=fingerprint(R/'Amaterasu-Movement.blend')
for k in ['geometry','rig','weights','materials','textures']:assert old[k]==new[k],k
for k,v in old['actions'].items():assert new['actions'][k]==v,k
s=bpy.data.scenes['01 · Action inspection'];bpy.context.window.scene=s;r=rig;foot=bpy.data.objects['Object_11'];r.animation_data.action=None
for p in r.pose.bones:p.matrix_basis.identity()
s.frame_set(2);bpy.context.view_layer.update();s.frame_set(1);bpy.context.view_layer.update();feet={}
RESTFOOT=foot.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.copy()
for kind in ['front','rear']:
 for side,sign in [('L',1),('R',-1)]:feet[kind+'.'+side]=[v.index for v in foot.data.vertices if(p:=RESTFOOT@v.co).z<.17 and sign*p.x>.25 and(p.y<-.9 if kind=='front'else p.y>1)]
print('FOOT MASKS',{k:len(v)for k,v in feet.items()},flush=True)
def points(obj=None):
 obj=foot if obj is None else obj
 ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();out={}
 for k,ids in feet.items():
  ps=[ev.matrix_world@me.vertices[j].co for j in ids];out[k]=(sum(ps,Vector())/len(ps),min(p.z for p in ps))
 ev.to_mesh_clear();return out
info=json.loads((R/'review/authoring.json').read_text())['actions'];rows={};problems=[]
for name,desc in info.items():
 r.animation_data.action=None
 for p in r.pose.bones:p.matrix_basis.identity()
 r.animation_data.action=bpy.data.actions[name];maxik=0;minimum=1e10;largest=0;prev={};bad=[];frames=0
 for step in range(desc['N']*4+1):
  f=1+step*.25;s.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update();pts=points();minimum=min(minimum,min(z for p,z in pts.values()))
  for key in feet:
   kind,side=key.split('.');up=r.pose.bones['DEF_'+kind+'_upper.'+side];lo=r.pose.bones['DEF_'+kind+'_lower.'+side];err=(lo.tail-r.pose.bones['MCH_target_'+key].head).length;maxik=max(maxik,err);q=up.matrix.to_quaternion()
   if key in prev:largest=max(largest,math.degrees(q.rotation_difference(prev[key]).angle))
   prev[key]=q.copy()
   if err>.012:bad.append({'frame':f,'key':key,'ik_error':err})
  frames+=1
 rows[name]={'sample_count':frames,'max_ik_error':maxik,'min_paw_z':minimum,'max_quarter_frame_upper_leg_rotation_deg':largest,'bad_reach_samples':bad[:12]};problems+=([{'action':name,'kind':'reach','error':maxik}]if maxik>.012 else[])+([{'action':name,'kind':'floor','height':minimum}]if minimum<-.012 else[])+([{'action':name,'kind':'joint_step','angle':largest}]if largest>45 else[]);print('ACTION_CHECK',name,rows[name],flush=True)
# Actual native NLA output, not ideal targets, across every displayed frame.
s=bpy.data.scenes['03 · Jump and dodge showcase'];bpy.context.window.scene=s;r=bpy.data.objects['JUMP_DEMO_WOLF_RIG'];foot=bpy.data.objects['M2 · Object_11'];timings=[];minz=1e10;maxik=0;maxstep=0;worstrotation=None;prev={};bad=[];drifts=[];anchors={}
for f in range(1,s.frame_end+1):
 start=time.perf_counter();s.frame_set(f);bpy.context.view_layer.update();timings.append((time.perf_counter()-start)*1000);pts=points(foot);minz=min(minz,min(z for p,z in pts.values()))
 for key,(pt,z)in pts.items():
  kind,side=key.split('.');up=r.pose.bones['DEF_'+kind+'_upper.'+side];lo=r.pose.bones['DEF_'+kind+'_lower.'+side];err=(lo.tail-r.pose.bones['MCH_target_'+key].head).length;maxik=max(maxik,err);q=up.matrix.to_quaternion()
  if key in prev:
   angle=math.degrees(q.rotation_difference(prev[key]).angle)
   if angle>maxstep:maxstep=angle;worstrotation={'frame':f,'key':key,'angle':angle,'up':list(up.head),'knee':list(up.tail),'target':list(r.pose.bones['MCH_target_'+key].head)}
  prev[key]=q.copy()
  if err>.015:bad.append({'frame':f,'key':key,'error':err})
  if z<.06:
   if key in anchors:drifts.append({'frame':f,'key':key,'distance':(pt-anchors[key]).xy.length})
   anchors[key]=pt.copy()
  else:anchors.pop(key,None)
 if f%500==1:print('DEMO_CHECK',f,'/',s.frame_end,flush=True)
summary={'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'original_geometry_rig_weights_materials_textures_exact':True,'all_previous_actions_exact':True,'previous_action_count':len(old['actions']),'actions':rows,'action_problems':problems,'demo':{'frames':s.frame_end,'minimum_paw_z':minz,'maximum_ik_error':maxik,'maximum_frame_upper_leg_rotation_deg':maxstep,'worst_rotation':worstrotation,'bad_reach_samples':bad[:20],'worst_grounded_xy_steps':sorted(drifts,key=lambda r:r['distance'],reverse=True)[:12],'cpu_median_ms':statistics.median(timings[10:]),'cpu_p95_ms':sorted(timings)[int(len(timings)*.95)]},'packed_textures':len(new['textures'])}
(R/'review/validation.json').write_text(json.dumps(summary,indent=2));print('FINAL_VALIDATION_SUMMARY',json.dumps({k:v for k,v in summary.items()if k!='actions'}),flush=True)
assert not problems,problems
assert minz>-.012 and maxik<.015 and maxstep<65,(minz,maxik,maxstep)
print('M2_VALIDATION_PASSED')

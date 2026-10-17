import bpy,math,json
from pathlib import Path
from mathutils import Vector,Quaternion
R=Path(__file__).resolve().parent;s=bpy.context.scene;r=bpy.data.objects['WOLF_RIG'];obj=bpy.data.objects['Object_11'];specs=json.loads((R/'review/authoring.json').read_text())['specs'];feet={}
for kind in ['front','rear']:
 for side,sign in [('L',1),('R',-1)]:feet[kind+'.'+side]=[v.index for v in obj.data.vertices if(p:=obj.matrix_world@v.co).z<.17 and sign*p.x>.25 and(p.y<-.9 if kind=='front'else p.y>1)]
def obs():
 bpy.context.view_layer.update();e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=e.to_mesh();out={}
 for key,ids in feet.items():
  ps=[e.matrix_world@me.vertices[i].co for i in ids];out[key]=(sum(ps,Vector())/len(ps),min(p.z for p in ps))
 e.to_mesh_clear();return out
report={}
for kind,sp in specs.items():
 start={}
 for key,off in sp['offset'].items():
  r.animation_data.action=bpy.data.actions[sp['base']];f=1+off*sp['N'];s.frame_set(int(f),subframe=f%1);start[key]=obs()[key][0]
 for side in ['L','R']:
  a=bpy.data.actions[kind+'_Turn_'+side];r.animation_data.action=a;N=sp['N'];omega=a['yaw_rate_radians'];frames=set(range(1,N+2,2));frames.add(N+1)
  for j in range(2*N+1):
   f=1+j/2;t=(f-1)/N
   if any((t-off)%1<sp['d'][key.split('.')[0]]+.035 for key,off in sp['offset'].items()):frames.add(f)
  rows={key:[]for key in feet};errors=[]
  for f in sorted(frames):
   r.animation_data.action=a;s.frame_set(int(f),subframe=f%1);raw=obs();r.animation_data.action=None;targets={}
   for key,(point,z)in raw.items():
    u=((f-1)/N-sp['offset'][key])%1;d=sp['d'][key.split('.')[0]]
    if u<d+1e-6:
     sec=u*N/60;theta=omega*sec;P=Vector((sp['v']/omega*(1-math.cos(theta)),-sp['v']/omega*math.sin(theta),0));goal=Quaternion((0,0,1),-theta)@(start[key]-P);targets[key]=(goal.x,goal.y,.035)
    else:targets[key]=(point.x,point.y,max(.035,z))
   for it in range(8):
    actual=obs()
    for key,(x,y,z)in targets.items():
     p=r.pose.bones['CTRL_paw_'+key];m=p.matrix.copy();m.translation+=Vector((x-actual[key][0].x,y-actual[key][0].y,z-actual[key][1]));p.matrix=m
    bpy.context.view_layer.update()
   actual=obs();errors.append(max(max(abs(actual[k][0].x-v[0]),abs(actual[k][0].y-v[1]),abs(actual[k][1]-v[2]))for k,v in targets.items()))
   for key in feet:rows[key].append((f,r.pose.bones['CTRL_paw_'+key].location.copy()))
  for key,values in rows.items():
   path='pose.bones["CTRL_paw_'+key+'"].location'
   for fc in list(a.fcurves):
    if fc.data_path==path:a.fcurves.remove(fc)
   for axis in range(3):
    fc=a.fcurves.new(path,index=axis,action_group='CTRL_paw_'+key)
    for f,p in values:k=fc.keyframe_points.insert(f,p[axis],options={'FAST'});k.interpolation='BEZIER';k.handle_left_type='AUTO_CLAMPED';k.handle_right_type='AUTO_CLAMPED'
    ps=fc.keyframe_points;dt=ps[1].co.x-ps[0].co.x+ps[-1].co.x-ps[-2].co.x;slope=(ps[1].co.y-ps[-2].co.y)/dt
    for k in [ps[0],ps[-1]]:k.handle_left_type='FREE';k.handle_right_type='FREE';k.handle_left=(k.co.x-1/3,k.co.y-slope/3);k.handle_right=(k.co.x+1/3,k.co.y+slope/3)
    fc.modifiers.new('CYCLES')
  report[a.name]={'max_solve_error':max(errors),'contact_keys_per_component':len(rows['front.L'])};print('CONTACT_POLISH',a.name,report[a.name],flush=True)
add=bpy.data.actions['ADD_LookAround']
for fc in list(add.fcurves):
 if not fc.data_path.endswith('rotation_euler'):add.fcurves.remove(fc)
r.animation_data.action=bpy.data.actions['Idle_Natural'];s.frame_set(1);(R/'review/contact-polish.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(R/'Amaterasu-Movement.blend'))

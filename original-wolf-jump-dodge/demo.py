"""Native NLA milestone showcase. Run on the authored checkpoint, once."""
import bpy,math,json,ast
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
R=Path(__file__).resolve().parent;main=bpy.data.scenes['01 · Action inspection'];bpy.context.window.scene=main;original=bpy.data.objects['WOLF_RIG'];info=json.loads((R/'review/authoring.json').read_text())['actions'];CTRL=[p.name for p in original.pose.bones if p.name.startswith('CTRL_')];rr=original.data.bones['CTRL_root'].matrix_local.copy();original.animation_data.action=None
for p in original.pose.bones:p.matrix_basis.identity()
main.frame_set(2);bpy.context.view_layer.update();main.frame_set(1);bpy.context.view_layer.update()
def smooth(u):u=max(0,min(1,u));return u*u*(3-2*u)
def reduce(rows,tolerance):
 keep={0,len(rows)-1};stack=[(0,len(rows)-1)]
 while stack:
  lo,hi=stack.pop()
  if hi-lo<2:continue
  a,x=rows[lo];b,y=rows[hi];error,index=max((abs(v-x-(y-x)*(f-a)/(b-a)),j)for j,(f,v)in enumerate(rows[lo+1:hi],lo+1))
  if error>tolerance:keep.add(index);stack.extend([(lo,index),(index,hi)])
 return[rows[i]for i in sorted(keep)]
# Source root samples: new standalone Actions carry true root motion.
rootcache={}
for name,d in info.items():
 a=bpy.data.actions[name];original.animation_data.action=a;rows=[]
 for t in range(d['N']+1):
  main.frame_set(t+1);rows.append(original.pose.bones['CTRL_root'].matrix.translation.copy())
 rootcache[name]=rows
original.animation_data.action=bpy.data.actions['Idle_Natural'];main.frame_set(1)
s=bpy.data.scenes.new('03 · Jump and dodge showcase');s.world=main.world;s.render.engine='BLENDER_EEVEE_NEXT';s.render.fps=60;s.sync_mode='FRAME_DROP';s.eevee.taa_render_samples=16;s.render.resolution_x=1100;s.render.resolution_y=760;s.render.resolution_percentage=100
col=bpy.data.collections.new('M2 · Linked character');s.collection.children.link(col);r=original.copy();r.name='JUMP_DEMO_WOLF_RIG';r.animation_data_clear();col.objects.link(r)
for p in r.pose.bones:
 p.matrix_basis.identity()
 for c in p.constraints:
  for field in ['target','pole_target']:
   if hasattr(c,field)and getattr(c,field)==original:setattr(c,field,r)
meshes=[]
for o in main.objects:
 if o.type!='MESH'or o.parent!=original:continue
 c=o.copy();c.name='M2 · '+o.name;c.data=o.data;c.parent=r;col.objects.link(c)
 for m in c.modifiers:
  if m.type=='ARMATURE':m.object=r
 meshes.append(c)
foot=bpy.data.objects['M2 · Object_11'];feet={}
for kind in ['front','rear']:
 for side,sign in [('L',1),('R',-1)]:feet[kind+'.'+side]={'ids':[v.index for v in foot.data.vertices if(p:=foot.matrix_world@v.co).z<.17 and sign*p.x>.25 and(p.y<-.9 if kind=='front'else p.y>1)],'ctrl':'CTRL_paw_'+kind+'.'+side}
def soles():
 bpy.context.view_layer.update();ev=foot.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();out={}
 for k,d in feet.items():
  ps=[ev.matrix_world@me.vertices[j].co for j in d['ids']];out[k]=(sum(ps,Vector())/len(ps),min(p.z for p in ps))
 ev.to_mesh_clear();return out
# Each case has a matching gait lead-in and exit. The root path is independent.
cases=[]
def case(label,parts):cases.append((label,parts))
def part(action,duration=None,phase=0,zbase=0,zfall=None):return{'action':action,'duration':duration or info[action]['N'],'phase':phase,'zbase':zbase,'zfall':zfall}
def gait(name,duration,phase):return{'action':name,'duration':duration,'phase':phase,'zbase':0,'zfall':None}
for name in ['Jump_Standing','Jump_Walk','Jump_Jog','Jump_Sprint']:
 d=info[name];base=d['gait'];dur=72 if base=='Walk_Natural'else 64 if base=='Sprint_Fluid'else 80 if base=='Jog_Natural'else 60;n=int(bpy.data.actions[base].get('cycle_frames',240));case(name,[gait(base,dur,d['phase']-dur/n),part(name),gait(base,dur,d['exit_phase'])])
# Airborne sequences enter from an actual jump, not a teleport to a drop height.
j=info['Jump_Standing'];apex=j['takeoff']+(j['land_front']-j['takeoff'])//2;alt=rootcache['Jump_Standing'][apex].z
case('Double jump + soft landing',[gait('Idle',48,0),part('Jump_Standing',apex),part('Jump_Double',zbase=alt),part('Air_Fall',40,zfall=[alt,.65]),part('Land_Soft'),gait('Idle',48,0)])
case('Falling + soft landing',[gait('Idle',48,0),part('Jump_Standing',apex),part('Air_Fall',44,zfall=[alt,.65]),part('Land_Soft'),gait('Idle',48,0)])
peak=40;high=alt+rootcache['Jump_Double'][peak].z
case('Large fall + heavy landing',[gait('Idle',48,0),part('Jump_Standing',apex),part('Jump_Double',peak,zbase=alt),part('Air_Fall',60,zfall=[high,1.5]),part('Land_Heavy'),gait('Idle',48,0)])
for name in ['Dodge_Left','Dodge_Right','Dodge_Back','Dodge_Forward','Dodge_Walk','Dodge_Jog','Dodge_Sprint']:
 d=info[name];base=d['gait'];dur=72 if base=='Walk_Natural'else 64 if base=='Sprint_Fluid'else 80 if base=='Jog_Natural'else 48;n=int(bpy.data.actions[base].get('cycle_frames',240));case(name,[gait(base,dur,d['phase']-dur/n),part(name),gait(base,dur,d['exit_phase'])])
r.animation_data_create();segments=[];cursor=1;casebounds=[]
for index,(label,parts)in enumerate(cases):
 start=cursor
 for k,item in enumerate(parts):
  a=bpy.data.actions[item['action']];N=int(a.get('duration_frames',a.get('cycle_frames',240)));duration=item['duration'];blend=0 if not segments else 6 if item['action']in info or segments[-1]['action']in info else 24
  begin=cursor-blend if segments else cursor;end=begin+duration;track=r.animation_data.nla_tracks.new();track.name=f'{index+1:02}.{k+1} '+item['action'];strip=track.strips.new(item['action'],int(begin),a);strip.action_frame_start=1;strip.action_frame_end=N+1;strip.frame_end=end;strip.extrapolation='NOTHING';strip.blend_type='REPLACE';strip.blend_in=0;strip.blend_out=0;strip.use_animated_time=True
  for f,t in [(begin,1+item['phase']*N),(end,1+item['phase']*N+duration)]:strip.strip_time=t;strip.keyframe_insert('strip_time',frame=f)
  for fc in strip.fcurves:
   for p in fc.keyframe_points:p.interpolation='LINEAR'
  strip.use_animated_influence=True
  for f,w in ([(begin,1),(end,1)]if not blend else[(begin,0),(begin+blend,1),(end,1)]):strip.influence=w;strip.keyframe_insert('influence',frame=f)
  for fc in strip.fcurves:
   if fc.data_path=='influence':
    ps=fc.keyframe_points
    for j,p in enumerate(ps):
     dl=p.co.x-ps[j-1].co.x if j else ps[1].co.x-p.co.x;dr=ps[j+1].co.x-p.co.x if j+1<len(ps)else dl;p.interpolation='BEZIER';p.handle_left_type='FREE';p.handle_right_type='FREE';p.handle_left=(p.co.x-dl/3,p.co.y);p.handle_right=(p.co.x+dr/3,p.co.y)
  seg=dict(item,start=begin,end=end,blend=blend,N=N,case=label);segments.append(seg);s.timeline_markers.new(label+' · '+item['action'],frame=int(begin));cursor=end
 casebounds.append({'name':label,'start':start,'end':cursor})
END=int(cursor);s.frame_start=1;s.frame_end=END
speeds={'Idle':0,'Idle_Natural':0,'Walk_Natural':1.6666667,'Jog_Natural':7.2,'Sprint_Fluid':14.625}
def local(seg,f):
 t=max(0,min(seg['duration'],f-seg['start']));name=seg['action']
 if name not in info:return Vector((0,-speeds[name]*t/60,0))
 if seg['zfall']is not None:
  a,b=seg['zfall'];return Vector((0,-1.8*t/60,a+(b-a)*(t/seg['duration'])**1.5))
 rows=rootcache[name];q=max(0,min(len(rows)-1,t));i=int(q);v=rows[i].lerp(rows[min(i+1,len(rows)-1)],q-i);v.z+=seg['zbase'];return v

def active(f):
 seg=next(seg for seg in reversed(segments)if seg['start']<=f<=seg['end']);i=segments.index(seg);w=smooth((f-seg['start'])/seg['blend'])if seg['blend']else 1
 return[(segments[i-1],1-w),(seg,w)]if i and w<1 else[(seg,1)]
path=bpy.data.actions.new('M2_ROOT · Continuous travel and wind');path.use_fake_user=True;r['movement_wind_level']=0.0;rootcurves={}
for prop in ['location','rotation_euler']:
 for axis in range(3):rootcurves[prop,axis]=path.fcurves.new('pose.bones["CTRL_root"].'+prop,index=axis,action_group='Continuous root motion')
wind=path.fcurves.new('["movement_wind_level"]',action_group='Wind speed');x=y=0
for f in range(1,END+1):
 pairs=active(f);vel=Vector();z=0;level=0
 for seg,w in pairs:
  # Endpoint derivatives use an inward finite difference.
  a=max(seg['start'],min(seg['end']-1,f-.5));b=a+1;vel+=(local(seg,b)-local(seg,a))*w;z+=local(seg,f).z*w;level+=float(bpy.data.actions[seg['action']].get('movement_wind_level',0))*w
 if f>1:x+=vel.x;y+=vel.y
 target=rr.copy();target.translation=(x,y,z);basis=rr.inverted()@target;loc,q,scale=basis.decompose();rot=q.to_euler('XYZ')
 for prop,value in [('location',loc),('rotation_euler',rot)]:
  for axis in range(3):rootcurves[prop,axis].keyframe_points.insert(f,value[axis],options={'FAST'})
 wind.keyframe_points.insert(f,level,options={'FAST'})
for fc in path.fcurves:
 for p in fc.keyframe_points:p.interpolation='LINEAR'
track=r.animation_data.nla_tracks.new();track.name='ROOT · Continuous travel and wind';strip=track.strips.new(path.name,1,path);strip.blend_type='REPLACE';strip.extrapolation='HOLD';strip.frame_end=END
stage=bpy.data.collections.new('M2 · Demonstration stage');s.collection.children.link(stage)
for name in ['DEMO · ground','DEMO · grid']:
 o=bpy.data.objects[name];c=o.copy();c.data=o.data;c.name='M2 · '+name;stage.objects.link(c)
follow=bpy.data.objects.new('M2 · Camera follows ground travel',None);stage.objects.link(follow);con=follow.constraints.new('COPY_LOCATION');con.target=r;con.subtarget='CTRL_root';con.use_z=False
camera=bpy.data.objects.new('M2 showcase camera',bpy.data.cameras.new('M2 showcase camera'));stage.objects.link(camera);camera.parent=follow;camera.location=(13,5,7);camera.rotation_euler=(Vector((0,0,3.2))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=15;s.camera=camera
for o in main.objects:
 if o.type=='LIGHT':c=o.copy();c.parent=follow;c.name='M2 · '+o.name;stage.objects.link(c)
# Native, camera-fixed labels. No frame handlers or external scripts.
for i,row in enumerate(casebounds):
 text=bpy.data.curves.new('M2 title '+str(i),'FONT');text.body=f'{i+1:02}  '+row['name'].replace('_',' ')+'\nAMATERASU · JUMP & DODGE STUDY';text.size=.29;text.space_line=1.25;o=bpy.data.objects.new('M2 title '+str(i),text);stage.objects.link(o);o.parent=camera;o.location=(-6.8,-4.5,-10);text.materials.append(bpy.data.materials['DEMO · ground reference'] if bpy.data.materials.get('DEMO · ground reference')else bpy.data.materials['DEMO · ground reference'] if False else bpy.data.materials['DEMO · parchment stage'])
 for f,v in [(1,0),(max(1,row['start']-1),0),(row['start'],1),(row['end'],1),(row['end']+1,0)]:o.scale=(v,v,v);o.keyframe_insert('scale',frame=f)
 for fc in o.animation_data.action.fcurves:
  for p in fc.keyframe_points:p.interpolation='CONSTANT'
fx=bpy.data.collections.new('M2 · Preserved speed wind');s.collection.children.link(fx);empty=bpy.data.objects.new('M2 · Wind follows root',None);fx.objects.link(empty);con=empty.constraints.new('COPY_TRANSFORMS');con.target=r;con.subtarget='CTRL_root'
fx.objects.link(bpy.data.objects['SPRINT_WIND · speed control'])
for o in bpy.data.collections['05 · Sprint wind — separate effect'].objects:
 c=o.copy();c.data=o.data;c.name='M2 · '+o.name;fx.objects.link(c);c.parent=empty;c.matrix_parent_inverse=rr.inverted()
 if c.animation_data:
  for fc in c.animation_data.drivers:
   for v in fc.driver.variables:
    if v.name=='gate':v.targets[0].id=r;v.targets[0].data_path='["movement_wind_level"]';v.targets[0].use_fallback_value=False
# Solve actual blended soles once, retaining sparse additive corrections.
bpy.context.window.scene=s;r.animation_data.action=None;states={k:{'anchor':None,'locked':False,'delta':Vector(),'release':-100}for k in feet};records={k:[]for k in feet};checks=[]
for f in range(1,END+1):
 r.animation_data.use_nla=True;s.frame_set(f);bpy.context.view_layer.update();obs=soles();raw={n:r.pose.bones[n].matrix_basis.copy()for n in CTRL};old={k:r.pose.bones[d['ctrl']].location.copy()for k,d in feet.items()};goals={}
 for key,(pt,z)in obs.items():
  st=states[key];ground=z<.075
  if ground and not st['locked']:st['anchor']=pt.copy()
  if ground:delta=st['anchor']-pt;delta.z=0;st['delta']=delta.copy();st['release']=f
  elif st['locked']:st['release']=f;delta=st['delta'].copy()
  else:delta=st['delta']*(1-smooth((f-st['release'])/4))
  st['locked']=ground;goals[key]=(pt+delta,.035 if ground else max(.035,z))
 r.animation_data.use_nla=False
 for n,m in raw.items():r.pose.bones[n].matrix_basis=m
 bpy.context.view_layer.update()
 for j in range(4):
  actual=soles()
  for key,d in feet.items():
   p=r.pose.bones[d['ctrl']];m=p.matrix.copy();pt,z=actual[key];goal,gz=goals[key];m.translation+=Vector((goal.x-pt.x,goal.y-pt.y,gz-z));p.matrix=m
  bpy.context.view_layer.update()
  for key,d in feet.items():
   kind,side=key.split('.');up=r.pose.bones['DEF_'+kind+'_upper.'+side];lo=r.pose.bones['DEF_'+kind+'_lower.'+side];target=r.pose.bones['MCH_target_'+key].head.copy();v=target-up.head;limit=(up.length+lo.length)*.985
   if v.length>limit:
    p=r.pose.bones[d['ctrl']];m=p.matrix.copy();m.translation+=up.head+v.normalized()*limit-target;p.matrix=m
  bpy.context.view_layer.update()
 for key,d in feet.items():records[key].append((f,r.pose.bones[d['ctrl']].location-old[key]))
 if f%120==1:checks.append({'frame':f,'min_sole_z':min(v[1]for v in soles().values())})
 if f%400==1:print('M2_CONTACTS',f,'/',END,flush=True)
cor=bpy.data.actions.new('M2_CONTACT · Blended paw support');cor.use_fake_user=True
for key,rows in records.items():
 for axis in range(3):
  fc=cor.fcurves.new('pose.bones["'+feet[key]['ctrl']+'"].location',index=axis,action_group=key)
  for f,v in reduce([(f,p[axis])for f,p in rows],.0005):p=fc.keyframe_points.insert(f,v,options={'FAST'});p.interpolation='LINEAR'
r.animation_data.use_nla=True;track=r.animation_data.nla_tracks.new();track.name='CONTACT · Blended paw support';strip=track.strips.new(cor.name,1,cor);strip.blend_type='ADD';strip.frame_end=END;strip.extrapolation='HOLD'
for fc in path.fcurves:
 values=[(p.co.x,p.co.y)for p in fc.keyframe_points];fc.keyframe_points.clear()
 for f,v in reduce(values,.0004):p=fc.keyframe_points.insert(f,v,options={'FAST'});p.interpolation='LINEAR'
main.frame_start=1;main.frame_end=180;original.animation_data.action=bpy.data.actions['Jump_Standing'];main.frame_set(1);s.frame_set(1)
for o in s.objects:o.select_set(False)
r.select_set(True);bpy.context.view_layer.objects.active=r
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.overlay.show_overlays=False
(R/'review/demo.json').write_text(json.dumps({'frames':END,'seconds':END/60,'cases':casebounds,'segments':segments,'contact_samples':checks,'contact_keys':sum(len(fc.keyframe_points)for fc in cor.fcurves)},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(R/'Amaterasu-Movement.blend'));print('MILESTONE_2_SHOWCASE_SAVED',END,flush=True)

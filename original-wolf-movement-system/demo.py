import bpy,math,json,time,statistics
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
R=Path(__file__).resolve().parent;s=bpy.context.scene;original=bpy.data.objects['WOLF_RIG'];originals=[o for o in s.objects if o.type=='MESH'and o.parent==original];spec=json.loads((R/'review/authoring.json').read_text())['specs'];rootrest=original.data.bones['CTRL_root'].matrix_local.copy();CTRL=[p.name for p in original.pose.bones if p.name.startswith('CTRL_')]
for fc in list(bpy.data.actions['ADD_LookAround'].fcurves):
 if not fc.data_path.endswith('rotation_euler'):bpy.data.actions['ADD_LookAround'].fcurves.remove(fc)
# The showcase uses linked mesh/armature data, not another copy of the wolf geometry.
demo=bpy.data.scenes.new('02 · Movement showcase');demo.world=s.world;demo.render.engine='BLENDER_EEVEE_NEXT';demo.render.fps=60;demo.sync_mode='FRAME_DROP';col=bpy.data.collections.new('SHOWCASE · linked character');demo.collection.children.link(col);rig=original.copy();rig.name='DEMO_WOLF_RIG';rig.animation_data_clear();col.objects.link(rig)
for p in rig.pose.bones:
 p.matrix_basis.identity()
 for c in p.constraints:
  for field in ['target','pole_target']:
   if hasattr(c,field)and getattr(c,field)==original:setattr(c,field,rig)
meshes=[]
for o in originals:
 c=o.copy();c.data=o.data;c.name='DEMO · '+o.name;col.objects.link(c);c.parent=rig
 for mod in c.modifiers:
  if mod.type=='ARMATURE':mod.object=rig
 meshes.append(c)
foot=next(o for o in meshes if o.name=='DEMO · Object_11');feet={}
for kind in ['front','rear']:
 for side,sign in [('L',1),('R',-1)]:feet[kind+'.'+side]={'ids':[v.index for v in foot.data.vertices if(p:=foot.matrix_world@v.co).z<.17 and sign*p.x>.25 and(p.y<-.9 if kind=='front'else p.y>1)],'ctrl':'CTRL_paw_'+kind+'.'+side}
def soles():
 bpy.context.view_layer.update();ev=foot.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();out={}
 for key,item in feet.items():
  pts=[ev.matrix_world@me.vertices[i].co for i in item['ids']];out[key]={'center':sum(pts,Vector())/len(pts),'z':min(p.z for p in pts)}
 ev.to_mesh_clear();return out
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
# NLA time is explicit and phase-continuous between straight and turning clips.
sequence=[('Idle','Idle',480,0),('.DEMO_Idle_Turn_L90','StandL',216,0),('.DEMO_Idle_Turn_R90','StandR',216,0),('Walk_Natural','Walk',216,0),('Walk_Turn_L','Walk',216,1),('Walk_Turn_R','Walk',216,-1),('Walk_Natural','Walk',144,0),('Jog_Natural','Jog',120,0),('Jog_Turn_L','Jog',120,1),('Jog_Turn_R','Jog',120,-1),('Jog_Natural','Jog',80,0),('Sprint_Fluid','Sprint',128,0),('Sprint_Turn_L','Sprint',128,1),('Sprint_Turn_R','Sprint',128,-1),('Sprint_Fluid','Sprint',96,0),('Jog_Natural','Jog',120,0),('Walk_Natural','Walk',216,0),('Idle_Natural','Idle',480,0)]
# Match foot pose when changing gait families; turns at the same speed keep phase.
mainfeet={}
sourceFoot=bpy.data.objects['Object_11']
for key,item in feet.items():mainfeet[key]=item['ids']
def source_points(action,phase):
 original.animation_data.action=None
 for p in original.pose.bones:p.matrix_basis.identity()
 original.animation_data.action=action;nf=int(action.get('cycle_frames',240));f=1+phase*nf;s.frame_set(int(f),subframe=f%1);bpy.context.view_layer.update();ev=sourceFoot.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();points={}
 for key,ids in mainfeet.items():
  vs=[ev.matrix_world@me.vertices[j].co for j in ids];points[key]=(sum(vs,Vector())/len(vs),min(v.z for v in vs))
 ev.to_mesh_clear();return points
def matched_phase(previous,action,start):
 old=source_points(bpy.data.actions[previous['action']],previous['phase']+(start-previous['start'])/previous['N'])
 choices=[]
 for j in range(32):
  phase=j/32;new=source_points(action,phase);score=sum(.25*(old[k][0]-new[k][0]).xy.length_squared+4*(old[k][1]-new[k][1])**2 for k in old);choices.append((score,phase))
 return min(choices)[1]
rig.animation_data_create();rig.animation_data.action=None;segments=[];prev=None
for index,(name,family,duration,turn)in enumerate(sequence):
 a=bpy.data.actions[name];N=int(a.get('cycle_frames',240));blend=0 if prev is None else(72 if (family=='Walk'and(prev['family'].startswith('Stand')or prev['family']=='Idle'))or(family=='Idle'and prev['family']=='Walk')else 24 if family!=prev['family']and family in spec and prev['family']in spec else 12)
 start=1 if prev is None else prev['end']-blend;phase=(prev['phase']+(start-prev['start'])/N)%1 if prev and family==prev['family']else 0
 if prev and family!=prev['family']and family in spec:phase=.45 if prev['family'].startswith('Stand')else matched_phase(prev,a,start)
 end=start+duration;track=rig.animation_data.nla_tracks.new();track.name=f'{index+1:02} · '+name;strip=track.strips.new(name,int(start),a);strip.action_frame_start=1;strip.action_frame_end=N+1;strip.frame_end=end;strip.extrapolation='NOTHING';strip.blend_type='REPLACE';strip.blend_in=0;strip.blend_out=0;strip.use_animated_time=True
 for f,value in [(start,1+phase*N),(end,1+phase*N+duration)]:strip.strip_time=value;strip.keyframe_insert('strip_time',frame=f)
 for fc in strip.fcurves:
  for k in fc.keyframe_points:k.interpolation='LINEAR'
 strip.use_animated_influence=True
 for f,value in([(start,1),(end,1)]if blend==0 else[(start,0),(start+blend,1),(end,1)]):strip.influence=value;strip.keyframe_insert('influence',frame=f)
 for fc in strip.fcurves:
  if fc.data_path=='influence':
   for i,k in enumerate(fc.keyframe_points):
    ps=fc.keyframe_points;dl=k.co.x-ps[i-1].co.x if i else (ps[1].co.x-k.co.x);dr=ps[i+1].co.x-k.co.x if i+1<len(ps)else dl;k.interpolation='BEZIER';k.handle_left_type='FREE';k.handle_right_type='FREE';k.handle_left=(k.co.x-dl/3,k.co.y);k.handle_right=(k.co.x+dr/3,k.co.y)
 seg={'action':name,'family':family,'start':start,'end':end,'blend':blend,'phase':phase,'N':N,'turn':turn};segments.append(seg);prev=seg;demo.timeline_markers.new(f'{index+1:02} '+name,frame=int(start))
# Show the reusable gaze layer explicitly over the original Idle clip.
track=rig.animation_data.nla_tracks.new();track.name='ADD · Reusable idle gaze';strip=track.strips.new('ADD_LookAround',1,bpy.data.actions['ADD_LookAround']);strip.frame_end=481;strip.blend_type='ADD';strip.extrapolation='NOTHING'
END=int(segments[-1]['end']);demo.frame_start=1;demo.frame_end=END

def contribution(seg,f):
 family=seg['family'];t=(f-seg['start'])/60
 if family in spec:return spec[family]['v'],seg['turn']*spec[family]['v']/spec[family]['radius'],1 if family=='Sprint'else .28 if family=='Jog'else 0
 if family.startswith('Stand'):
  u=(f-seg['start']-12)/192;rate=(1 if family=='StandL'else-1)*math.pi/2*6*u*(1-u)/(192/60)if 0<u<1 else 0;return 0,rate,0
 return 0,0,0

def state_at(f):
 active=[seg for seg in segments if seg['start']<=f<=seg['end']];current=active[-1];idx=segments.index(current);w=smooth((f-current['start'])/current['blend'])if current['blend']else 1
 if idx and w<1:
  previous=segments[idx-1];a=contribution(previous,f);b=contribution(current,f);values=list(x+(y-x)*w for x,y in zip(a,b))
  if previous['family'].startswith('Stand')and current['family']=='Walk':values[1]=a[1]+b[1]*w
  return tuple(values),[(previous,1-w),(current,w)]
 return contribution(current,f),[(current,1)]
# Root trajectory is separate from reusable in-place gait/steering Actions.
path=bpy.data.actions.new('DEMO_PathAndSpeed');path.use_fake_user=True;rig['movement_wind_level']=0.0
curves={}
for prop,count in [('location',3),('rotation_euler',3)]:
 for axis in range(count):curves[(prop,axis)]=path.fcurves.new('pose.bones["CTRL_root"].'+prop,index=axis,action_group='Root path')
windcurve=path.fcurves.new('["movement_wind_level"]',action_group='Speed wind')
x=y=heading=0;pathrows=[]
for f in range(1,END+1):
 (v,w,wind),_=state_at(f)
 if f>1:
  (pv,pw,_),_=state_at(f-.5);heading+=pw/60;mid=heading-pw/120;x+=pv*math.sin(mid)/60;y-=pv*math.cos(mid)/60
 target=Quaternion((0,0,1),heading).to_matrix().to_4x4()@rootrest;target.translation=(x,y,0);basis=rootrest.inverted()@target;loc,rot,scale=basis.decompose();euler=rot.to_euler('XYZ')
 for prop,value in [('location',loc),('rotation_euler',euler)]:
  for axis in range(3):curves[(prop,axis)].keyframe_points.insert(f,value[axis],options={'FAST'})
 windcurve.keyframe_points.insert(f,wind,options={'FAST'});pathrows.append((f,x,y,heading,v,w))
for fc in path.fcurves:
 for k in fc.keyframe_points:k.interpolation='LINEAR'
track=rig.animation_data.nla_tracks.new();track.name='ROOT · Continuous speed / curved path';strip=track.strips.new(path.name,1,path);strip.blend_type='ADD';strip.extrapolation='HOLD';strip.frame_end=END
# Independent wind, following the animated root. Mesh data is shared with the original effect.
windcol=bpy.data.collections.new('SHOWCASE · speed wind');demo.collection.children.link(windcol);empty=bpy.data.objects.new('DEMO · Wind root',None);windcol.objects.link(empty);con=empty.constraints.new('COPY_TRANSFORMS');con.target=rig;con.subtarget='CTRL_root';windctrl=bpy.data.objects['SPRINT_WIND · speed control'];windcol.objects.link(windctrl)
for o in bpy.data.collections['05 · Sprint wind — separate effect'].objects:
 c=o.copy();c.data=o.data;c.name='DEMO · '+o.name;windcol.objects.link(c);c.parent=empty;c.matrix_parent_inverse=rootrest.inverted()
 if c.animation_data:
  for fc in c.animation_data.drivers:
   for var in fc.driver.variables:
    if var.name=='gate':var.targets[0].id=rig;var.targets[0].data_path='["movement_wind_level"]';var.targets[0].use_fallback_value=False
# Only simple stage helpers, separate from the character assets.
stage=bpy.data.collections.new('SHOWCASE · stage and camera');demo.collection.children.link(stage)
def material(name,color):
 m=bpy.data.materials.new(name);m.diffuse_color=color;m.use_nodes=True;m.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value=color;return m
floorMat=material('DEMO · parchment stage',(.27,.25,.21,1));lineMat=material('DEMO · ground reference',(.15,.16,.15,1))
me=bpy.data.meshes.new('DEMO · stage');me.from_pydata([(-300,-300,-.012),(300,-300,-.012),(300,300,-.012),(-300,300,-.012)],[],[(0,1,2,3)]);floor=bpy.data.objects.new('DEMO · ground',me);stage.objects.link(floor);me.materials.append(floorMat)
verts=[];faces=[]
for axis in [0,1]:
 for n in range(-250,251,5):
  points=[(n-.012,-300,0),(n+.012,-300,0),(n+.012,300,0),(n-.012,300,0)]if axis==0 else[(-300,n-.012,0),(300,n-.012,0),(300,n+.012,0),(-300,n+.012,0)];i=len(verts);verts+=points;faces.append(tuple(range(i,i+4)))
me=bpy.data.meshes.new('DEMO · grid');me.from_pydata(verts,[],faces);o=bpy.data.objects.new('DEMO · grid',me);stage.objects.link(o);me.materials.append(lineMat)
follow=bpy.data.objects.new('DEMO · camera follow',None);stage.objects.link(follow);c=follow.constraints.new('COPY_LOCATION');c.target=rig;c.subtarget='CTRL_root'
data=bpy.data.cameras.new('Showcase camera');camera=bpy.data.objects.new('Showcase camera',data);stage.objects.link(camera);camera.parent=follow;camera.location=(12,10,7.2);camera.rotation_euler=(Vector((0,0,2.3))-camera.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=13.5;demo.camera=camera
for source in s.objects:
 if source.type=='LIGHT':c=source.copy();stage.objects.link(c);c.parent=follow;c.hide_set(False)
original.animation_data.action=bpy.data.actions['Idle_Natural'];s.frame_set(1);s.frame_end=1440
# Evaluate the actual NLA blend, then solve only additive paw-contact deltas.
bpy.context.window.scene=demo;rig.animation_data.action=None;contacts={k:{'locked':False,'anchor':None,'release':0,'delta':Vector()}for k in feet};records={k:[]for k in feet};diagnostics=[]
def foot_support(seg,f,key):
 family=seg['family'];phase=seg['phase']+(f-seg['start'])/seg['N']
 if family in spec:
  q=(phase-spec[family]['offset'][key])%1;return 1.0 if q<spec[family]['d'][key.split('.')[0]]else 0.0
 if family.startswith('Stand'):
  local=f-seg['start']+1;order=['front.L','rear.R','front.R','rear.L']
  return 0.0 if any(order[j%4]==key and 13+j*16<=local<13+j*16+12.8 for j in range(12))else 1.0
 return 1.0
for f in range(1,END+1):
 rig.animation_data.use_nla=True;demo.frame_set(f);bpy.context.view_layer.update();raw=soles();pose={n:rig.pose.bones[n].matrix_basis.copy()for n in CTRL};oldloc={key:rig.pose.bones[item['ctrl']].location.copy()for key,item in feet.items()};(_,_,_),active=state_at(f);goals={};support={}
 for key,value in raw.items():
  st=contacts[key];weight=sum(w*foot_support(seg,f,key)for seg,w in active);support[key]=weight
  locked=weight>.68 and value['z']<.085
  if locked and not st['locked']:st['anchor']=value['center'].copy()
  if locked:delta=st['anchor']-value['center'];delta.z=0;st['delta']=delta.copy();st['release']=f
  elif st['locked']:st['release']=f;delta=st['delta'].copy()
  else:delta=st['delta']*(1-smooth((f-st['release'])/6))
  st['locked']=locked;goals[key]={'x':value['center'].x+delta.x,'y':value['center'].y+delta.y,'z':.035 if locked else max(.035,value['z'])}
 rig.animation_data.use_nla=False
 for n in CTRL:rig.pose.bones[n].matrix_basis=pose[n]
 bpy.context.view_layer.update()
 for it in range(4):
  actual=soles()
  for key,item in feet.items():
   m=rig.pose.bones[item['ctrl']].matrix.copy();g=goals[key];m.translation+=Vector((g['x']-actual[key]['center'].x,g['y']-actual[key]['center'].y,g['z']-actual[key]['z']));rig.pose.bones[item['ctrl']].matrix=m
  bpy.context.view_layer.update()
 actual=soles();error=max(max(abs(actual[k]['center'].x-goals[k]['x']),abs(actual[k]['center'].y-goals[k]['y']),abs(actual[k]['z']-goals[k]['z']))for k in feet)
 for key,item in feet.items():records[key].append((f,rig.pose.bones[item['ctrl']].location-oldloc[key]))
 if f%30==1:diagnostics.append({'f':f,'max_error':error,'min_z':min(v['z']for v in actual.values()),'support':support})
 if f%300==1:print('CONTACT_SOLVE',f,'/',END,'error',error,flush=True)
# Adaptive linear correction keys, with a sub-millimetre positional tolerance.
def reduce(rows,tolerance):
 keep={0,len(rows)-1};stack=[(0,len(rows)-1)]
 while stack:
  lo,hi=stack.pop()
  if hi-lo<2:continue
  a,x=rows[lo];b,y=rows[hi];err,index=max((abs(v-(x+(y-x)*(f-a)/(b-a))),i)for i,(f,v)in enumerate(rows[lo+1:hi],lo+1))
  if err>tolerance:keep.add(index);stack.extend([(lo,index),(index,hi)])
 return[rows[i]for i in sorted(keep)]
cor=bpy.data.actions.new('DEMO_PawContactCorrection');cor.use_fake_user=True
for key,rows in records.items():
 for axis in range(3):
  fc=cor.fcurves.new('pose.bones["'+feet[key]['ctrl']+'"].location',index=axis,action_group=key)
  for f,v in reduce([(f,p[axis])for f,p in rows],.0007):k=fc.keyframe_points.insert(f,v,options={'FAST'});k.interpolation='LINEAR'
rig.animation_data.use_nla=True;track=rig.animation_data.nla_tracks.new();track.name='CONTACT · Grounded paws through blends';strip=track.strips.new(cor.name,1,cor);strip.blend_type='ADD';strip.extrapolation='HOLD';strip.frame_end=END
# Reduce root path keys without changing the sampled trajectory visibly.
for fc in path.fcurves:
 values=[(k.co.x,k.co.y)for k in fc.keyframe_points];fc.keyframe_points.clear()
 for f,v in reduce(values,.00025 if 'rotation' in fc.data_path else .001):k=fc.keyframe_points.insert(f,v,options={'FAST'});k.interpolation='LINEAR'
demo.frame_set(1);demo.render.resolution_x=1000;demo.render.resolution_y=700;demo.render.resolution_percentage=100;demo.eevee.taa_render_samples=16
for obj in demo.objects:obj.select_set(False)
rig.select_set(True);bpy.context.view_layer.objects.active=rig
# Default viewport follows the showcase camera; the inspection scene remains independent.
for area in bpy.context.screen.areas:
 if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA';area.spaces.active.overlay.show_overlays=False
(R/'review/demo.json').write_text(json.dumps({'frames':END,'duration_seconds':END/60,'segments':segments,'contact_diagnostics':diagnostics,'correction_keys':sum(len(fc.keyframe_points)for fc in cor.fcurves),'root_keys':sum(len(fc.keyframe_points)for fc in path.fcurves),'linked_geometry':all(c.data==o.data for c,o in zip(meshes,originals))},indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(R/'Amaterasu-Movement.blend'));print('SHOWCASE_SAVED',END,flush=True)

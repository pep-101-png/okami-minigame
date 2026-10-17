import bpy,math,hashlib,json
from pathlib import Path
from mathutils import Quaternion,Vector
R=Path(__file__).resolve().parent;src=R.parent/'original-wolf-sprint/Amaterasu-Movement.blend'
assert hashlib.sha256(src.read_bytes()).hexdigest()=='4eb07c832ae5e43f232599c96a8d2e1fb20f58e898931a665d57c56a09b3f2e8'
bpy.ops.wm.open_mainfile(filepath=str(src));s=bpy.context.scene;r=bpy.data.objects['WOLF_RIG'];old=r.animation_data.action
r.animation_data.action=None
for p in r.pose.bones:p.matrix_basis.identity()
bpy.context.view_layer.update();resthead=r.pose.bones['CTRL_head'].matrix.to_quaternion().copy();resttail=r.pose.bones['CTRL_tail_01'].matrix.to_quaternion().copy()
allowed=['CTRL_neck_base','CTRL_neck_upper','CTRL_head']+[f'CTRL_tail_{i:02}'for i in range(1,6)]
a=bpy.data.actions['Sprint'].copy();a.name='Sprint_Polished';a.use_fake_user=True;r.animation_data.action=a
# Sample approved poses before replacing just the allowed tracks.
samples={}
for f in range(1,33):
 s.frame_set(f);samples[f]={n:r.pose.bones[n].rotation_euler.copy()for n in allowed}
for fc in list(a.fcurves):
 if any('"'+n+'"'in fc.data_path for n in allowed):a.fcurves.remove(fc)
for f in range(1,34):
 t=((f-1)%32)/32;wave=lambda phase:math.sin(math.tau*(t-phase));s.frame_set(f)
 for n,base,amp,lag in [('CTRL_neck_base',8,8.0,.11),('CTRL_neck_upper',0,5.8,.26)]:
  p=r.pose.bones[n];p.rotation_euler=(math.radians(base+amp*wave(lag)),math.radians(.5*wave(lag+.1)),math.radians(.7*wave(lag+.12)));p.keyframe_insert('rotation_euler',frame=f)
 p=r.pose.bones['CTRL_head'];p.location=(0,0,0);p.scale=(1,1,1);bpy.context.view_layer.update();m=p.matrix.copy()
 # A stabilised but living gaze: small delayed pitch rather than rigid cancellation.
 goal=Quaternion((1,0,0),math.radians(3+5.4*wave(.34)))@resthead
 q=goal;m=q.to_matrix().to_4x4();m.translation=p.matrix.translation;p.matrix=m;p.keyframe_insert('rotation_euler',frame=f);p.keyframe_insert('location',frame=f);p.keyframe_insert('scale',frame=f)
 # Dampen inherited pelvis pitch at the tail root, then propagate a soft travelling wave.
 p=r.pose.bones['CTRL_tail_01'];p.location=(0,0,0);p.scale=(1,1,1);bpy.context.view_layer.update();m=p.matrix.copy();q=Quaternion((0,0,1),math.radians(2.0*wave(.28)))@Quaternion((1,0,0),math.radians(18+6.5*wave(.25)))@resttail
 m=q.to_matrix().to_4x4();m.translation=p.matrix.translation;p.matrix=m
 for i in range(1,6):
  p=r.pose.bones[f'CTRL_tail_{i:02}']
  if i>1:p.rotation_euler=(math.radians([0,7,2,-1,-2][i-1]+(5.0+i*.9)*wave(.25+(i-1)*.085)),math.radians(.7*wave(.4+(i-1)*.085)),math.radians((2+i*.65)*wave(.37+(i-1)*.085)))
  p.keyframe_insert('rotation_euler',frame=f)
  if i==1:p.keyframe_insert('location',frame=f);p.keyframe_insert('scale',frame=f)
# Match derivative across the cyclic seam on the newly authored curves only.
for fc in a.fcurves:
 if not any('"'+n+'"'in fc.data_path for n in allowed):continue
 pts=fc.keyframe_points
 for i,k in enumerate(pts):
  j=i%32;prev=pts[(j-1)%32].co.y;nxt=pts[(j+1)%32].co.y;slope=(nxt-prev)*.5;k.interpolation='BEZIER';k.handle_left_type='FREE';k.handle_right_type='FREE';k.handle_left=(k.co.x-1/3,k.co.y-slope/3);k.handle_right=(k.co.x+1/3,k.co.y+slope/3)
 if not any(m.type=='CYCLES'for m in fc.modifiers):fc.modifiers.new('CYCLES')
a.pose_markers.new('SPRINT_WIND_ENABLE').frame=1
col=bpy.data.collections.new('05 · Sprint wind — separate effect');s.collection.children.link(col)
control=bpy.data.objects.new('SPRINT_WIND · speed control',None);col.objects.link(control);control['speed']=14.625;control['strength']=1.0
control.id_properties_ui('speed').update(min=0,max=20,description='Wind-only speed. Keyframe for a smooth fade. Does not retime the wolf.')
control.id_properties_ui('strength').update(min=0,max=1)
def drive(ob,path,index,expression,frame=False):
 fc=ob.driver_add(path,index)if index is not None else ob.driver_add(path);d=fc.driver;d.type='SCRIPTED'
 for name,obj,pth in [('speed',control,'["speed"]'),('strength',control,'["strength"]'),('gate',r,'animation_data.action.pose_markers["SPRINT_WIND_ENABLE"].frame')]:
  v=d.variables.new();v.name=name;v.type='SINGLE_PROP';v.targets[0].id=obj;v.targets[0].data_path=pth
  if name=='gate':v.targets[0].use_fallback_value=True;v.targets[0].fallback_value=0
 d.expression=expression
 return fc
mats=[]
for name,color in [('Pearl wash',(.84,.86,.82,1)),('Pale ash',(.58,.64,.64,1)),('Dilute ink',(.25,.31,.32,1))]:
 m=bpy.data.materials.new('WIND · '+name);m.use_nodes=True;m.diffuse_color=color;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=color;bs.inputs['Roughness'].default_value=.94;
 nodes=m.node_tree.nodes;links=m.node_tree.links;tex=nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=26;tex.inputs['Detail'].default_value=2
 ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=.15;ramp.color_ramp.elements[0].color=tuple(c*.72 for c in color[:3])+(1,);ramp.color_ramp.elements[1].position=.8;ramp.color_ramp.elements[1].color=color
 links.new(tex.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs[0],bs.inputs['Base Color'])
 attr=nodes.new('ShaderNodeAttribute');attr.attribute_name='brush_wash';mix=nodes.new('ShaderNodeMath');mix.operation='MULTIPLY';links.new(attr.outputs['Fac'],mix.inputs[0]);links.new(mix.outputs[0],bs.inputs['Alpha']);info=nodes.new('ShaderNodeObjectInfo');links.new(info.outputs['Alpha'],mix.inputs[1]);m.surface_render_method='DITHERED';mats.append(m)
# Fine, curved ribbons have tapered tips and a few narrower dry-brush companions.
for j in range(11):
 side=1 if j%2==0 else -1;start=.5+(j%3)*.65;length=4.2+(j%4)*.7;z=1.5+(j%5)*.68;x=side*(1.35+(j%3)*.16)
 verts=[];faces=[];count=38;width=.065+(j%3)*.03
 for i in range(count):
  u=i/(count-1);y=start+length*u;zz=z+.48*math.sin(u*math.pi*2+j*.8)+.22*u;xx=x+side*.16*math.sin(u*math.pi)
  w=width*(math.sin(math.pi*u)**.8)*(1-.32*u)
  verts.extend([(xx-w,y,zz-w*.55),(xx+w,y,zz+w*.55)])
 for i in range(count-1):faces.append((2*i,2*i+1,2*i+3,2*i+2))
 me=bpy.data.meshes.new('Wind brush ribbon');me.from_pydata(verts,[],faces);me.materials.append(mats[2 if j==10 else j%2]);wash=me.attributes.new('brush_wash','FLOAT','POINT')
 for k,d in enumerate(wash.data):
  u=(k//2)/(count-1);d.value=(.18 if j==10 else .66)*(math.sin(math.pi*u)**.4)
 o=bpy.data.objects.new(f'Wind ribbon {j+1:02}',me);col.objects.link(o)
 o.shape_key_add(name='Basis');key=o.shape_key_add(name='Drift')
 for i,v in enumerate(key.data):
  u=(i//2)/(count-1);v.co.x+=.12*u*math.sin(u*math.tau+j);v.co.z+=.16*u*math.sin(u*math.tau+j*.8)
 fc=key.driver_add('value');fc.driver.expression=f'0.5+0.5*sin(2*pi*(frame-1)/32+{j*.71})'
 gain='gate*strength*min(1,max(0,speed/14.625))*min(1,max(0,speed/14.625))*(3-2*min(1,max(0,speed/14.625)))'
 drive(o,'color',3,gain)
 for axis in range(3):drive(o,'scale',axis,gain if axis!=1 else f'({gain})*(0.55+0.45*min(1.4,speed/14.625))')
 drive(o,'location',2,f'({gain})*0.07*sin(2*pi*(frame-1)/32+{j*.65})')
# Optional independent effect-only fade demonstration, not assigned by default.
for f,value in [(1,0),(17,14.625),(97,14.625),(129,0)]:control['speed']=value;control.keyframe_insert('["speed"]',frame=f)
demo=control.animation_data.action;demo.name='Wind_Speed_Demo';demo.use_fake_user=True;control.animation_data.action=None;control['speed']=14.625
for fc in demo.fcurves:
 for k in fc.keyframe_points:k.handle_left_type='AUTO_CLAMPED';k.handle_right_type='AUTO_CLAMPED'
a['description']='Approved Sprint gallop retained exactly; isolated overlapping neck, head and five-control tail polish.'
a.asset_mark();s.frame_set(1);r.animation_data.action=a
text=bpy.data.texts.new('SPRINT WIND — START HERE');text.write('Select WOLF_RIG. Lower Action Editor: Sprint_Polished. Space plays. Previous Sprint, Idle, Walk, Jog untouched. Wind appears only on Sprint_Polished. Select SPRINT_WIND · speed control in collection 05; Object Custom Properties: speed 0–20 and strength 0–1. Speed changes wind only. Keyframe speed for fades, or select Wind_Speed_Demo on that empty for a 129-frame fade demonstration. Curves/ribbons and procedural drivers need recreating in Three.js, not directly exporting as GLTF effects. No scripts need enabling.\n')
a['effect_note']='The SPRINT_WIND_ENABLE pose marker gates the isolated effect via native driver fallback; retained Actions have no such marker.'
s.tool_settings.use_keyframe_insert_auto=False
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Amaterasu-Movement.blend'));print('POLISH_SAVED',flush=True)

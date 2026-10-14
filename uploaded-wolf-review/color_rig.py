import bpy,math
from mathutils import Vector
from pathlib import Path
root=Path(__file__).resolve().parent
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(root/'source'/'scene.gltf'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in meshes:
 world=o.matrix_world.copy();o.parent=None;o.matrix_world=world
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
# The uploaded body's UVs collapse to the texture margin: author replacement surface colours.
for o in meshes:
 old=o.data.materials[0].name
 m=bpy.data.materials.new(o.name+' painted');m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.85
 if old in ['Material__200','Material__201','Material__209','Material__230']:
  bs.inputs['Base Color'].default_value=(.94,.91,.8,1)
 else:
  attr=o.data.color_attributes.new(name='DivinePaint',type='FLOAT_COLOR',domain='POINT')
  for v in o.data.vertices:
   x,y,z=v.co;r=math.hypot(y+1.1,z-3.25);a=math.atan2(z-3.25,y+1.1)
   spiral=abs((a-r*12+math.pi)%(2*math.pi)-math.pi)<.21 and .1<r<.63 and abs(x)>.5
   brow=y<-2.45 and z>3.85 and abs(abs(x)-(.24+(z-3.85)*.5))<.09
   flank=abs(z-(3.35+.13*math.sin(y*1.2)))<.065 and -.6<y<2.25 and abs(x)>.65
   ankle=z<.8 and abs(z-(.45+.13*math.sin(y*6)))<.06
   color=(.92,.88,.75,1)
   if y<-4.0 and z>3.6:color=(.025,.02,.018,1)
   attr.data[v.index].color=color
  node=m.node_tree.nodes.new('ShaderNodeVertexColor');node.layer_name='DivinePaint';m.node_tree.links.new(node.outputs['Color'],bs.inputs['Base Color'])
 o.data.materials.clear();o.data.materials.append(m)
# Crisp, surface-fitted ink ribbons avoid blurred per-vertex markings.
from mathutils.bvhtree import BVHTree
verts_all=[];polys_all=[]
for obj in meshes:
 offset=len(verts_all);verts_all.extend([v.co.copy() for v in obj.data.vertices]);polys_all.extend([[offset+i for i in p.vertices] for p in obj.data.polygons])
bvh=BVHTree.FromPolygons(verts_all,polys_all)
red=bpy.data.materials.new('Vermilion ink');red.diffuse_color=(.72,.015,.006,1)
def ribbon(name,points,width,side):
 verts=[];faces=[]
 for i,(y,z) in enumerate(points):
  prev=Vector(points[max(0,i-1)]);nxt=Vector(points[min(len(points)-1,i+1)]);d=(nxt-prev).normalized();normal=Vector((-d.y,d.x))
  for sign in [-1,1]:
   q=Vector((y,z))+normal*width*sign/2
   hit=bvh.ray_cast(Vector((side*4,q.x,q.y)),Vector((-side,0,0)))[0]
   verts.append((hit.x+side*.028,q.x,q.y) if hit else (side*.8,q.x,q.y))
  if i:faces.append((i*2-2,i*2-1,i*2+1,i*2))
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);o.data.materials.append(red);meshes.append(o)
for side in [-1,1]:
 points=[]
 for i in range(130):
  a=i/129*math.tau*1.65;r=.045+.45*i/129;points.append((-1.45+r*math.cos(a),3.35+r*math.sin(a)))
 ribbon('Shoulder spiral',points,.055,side)
 ribbon('Flowing flank',[(y,3.38+.23*math.sin((y+.5)*.8)) for y in [-.9+i*.025 for i in range(120)]],.065,side)
 ribbon('Brow marking',[(-3.5+i*.015,4.35-.28*math.sin(i/45*math.pi)) for i in range(46)],.06,side)

for side in [-1,1]:
 hit=bvh.ray_cast(Vector((side*4,-3.12,4.3)),Vector((-side,0,0)))[0]
 if hit:
  for label,shift,scale,color in [('Eye ink',.035,(.035,.135,.07),(.012,.009,.006,1)),('Eye amber',.061,(.018,.06,.043),(.85,.42,.03,1)),('Eye pupil',.077,(.01,.018,.037),(.006,.005,.004,1))]:
   bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,location=(hit.x+side*shift,-3.12,4.3));o=bpy.context.object;o.name=label;o.scale=scale;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);mat=bpy.data.materials.new(label);mat.diffuse_color=color;o.data.materials.append(mat);meshes.append(o)

# A genuine deforming skeleton, with independent upper/lower leg articulation.
bpy.ops.object.armature_add();rig=bpy.context.object;rig.name='DivineWolfRig';bpy.ops.object.mode_set(mode='EDIT');rig.data.edit_bones.remove(rig.data.edit_bones[0])
def bone(name,head,tail,parent=None):
 b=rig.data.edit_bones.new(name);b.head=head;b.tail=tail
 if parent:b.parent=rig.data.edit_bones[parent]
 return b
bone('body',(0,1,3),(0,-1.5,3))
bone('head',(0,-1.9,3.4),(0,-3.4,4.2),'body')
bone('tail',(0,2.4,3),(0,3.8,2.6),'body')
for side,x in [('L',.72),('R',-.72)]:
 for leg,y in [('fore',-2),('hind',2)]:
  bone(leg+side,(x,y,2.8),(x,y,1.5),'body');bone(leg+'Shin'+side,(x,y,1.5),(x,y,.4),leg+side)
bpy.ops.object.mode_set(mode='OBJECT')
for o in meshes:
 groups={b.name:o.vertex_groups.new(name=b.name) for b in rig.data.bones}
 for v in o.data.vertices:
  x,y,z=v.co;side='L' if x>=0 else 'R'
  weights={'body':1}
  if z<2.6 and abs(x)>.28 and abs(y)>1:
   leg='fore' if y<0 else 'hind';t=max(0,min(1,(2.8-z)/.55));k=max(0,min(1,(1.75-z)/.45));weights={'body':1-t,leg+side:t*(1-k),leg+'Shin'+side:t*k}
  elif y<-2.1 and z>2.8:
   t=min(1,(-y-2.1)/.65);weights={'body':1-t,'head':t}
  elif y>2.6:
   t=min(1,(y-2.6)/.6);weights={'body':1-t,'tail':t}
  for n,w in weights.items():
   if w>0:groups[n].add([v.index],w,'REPLACE')
 mod=o.modifiers.new('Wolf skeleton','ARMATURE');mod.object=rig;o.parent=rig
# Idle breathing / head and tail movement, followed by an articulated walk loop.
for name,duration in [('Idle',80),('Walk',32)]:
 rig.animation_data_create();act=bpy.data.actions.new(name);rig.animation_data.action=act
 for f in range(1,duration+2):
  phase=(f-1)/duration*math.tau
  for b in rig.pose.bones:
   b.rotation_mode='XYZ';b.rotation_euler=(0,0,0);b.location=(0,0,0)
  rig.pose.bones['body'].location.y=.035*math.sin(phase*2)
  rig.pose.bones['head'].rotation_euler.x=.025*math.sin(phase)
  rig.pose.bones['tail'].rotation_euler.z=.08*math.sin(phase)
  if name=='Walk':
   for side in ['L','R']:
    for leg in ['fore','hind']:
     p=phase+(math.pi if (side=='R')^(leg=='hind') else 0)
     rig.pose.bones[leg+side].rotation_euler.x=.35*math.sin(p)
     rig.pose.bones[leg+'Shin'+side].rotation_euler.x=.42*max(0,math.cos(p))
  for b in rig.pose.bones:
   b.keyframe_insert('rotation_euler',frame=f);b.keyframe_insert('location',frame=f)
 track=rig.animation_data.nla_tracks.new();track.name=name;track.strips.new(name,1,act);track.mute=True
rig.animation_data.action=bpy.data.actions['Walk']
# Bake surface colours to a local atlas for reliable glTF interchange.
for o in meshes:
 if o.data.color_attributes:o.data.color_attributes.active_color=o.data.color_attributes['DivinePaint']
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(root/'colored-rigged.glb'),use_selection=True,export_animations=True,export_nla_strips=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=48;scene.cycles.use_denoising=False
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.55,.55,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.8
scene.view_settings.view_transform='AgX'
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.05));floor=bpy.context.object;m=bpy.data.materials.new('Backdrop');m.diffuse_color=(.25,.28,.3,1);floor.data.materials.append(m)
for pos,power in [((5,-6,10),2000),((-5,1,8),1500)]:
 bpy.ops.object.light_add(type='AREA',location=pos);l=bpy.context.object;l.data.energy=power;l.data.size=7;l.rotation_euler=(Vector((0,0,2.5))-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(13,-7,7));camera=bpy.context.object;camera.rotation_euler=(Vector((0,0,2.5))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=11;scene.camera=camera
scene.render.resolution_x=1000;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.frame_set(1);scene.render.filepath=str(root/'colored-preview.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'colored-rigged.blend'))
scene.render.resolution_x=500;scene.render.resolution_y=400;scene.cycles.samples=8
for f in range(1,33,2):
 scene.frame_set(f);scene.render.filepath=str(root/f'walk-{f:02}.png');bpy.ops.render.render(write_still=True)
print('COLOR_AND_RIG_COMPLETE')

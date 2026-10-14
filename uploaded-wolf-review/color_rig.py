import bpy,math,bmesh
from mathutils import Vector
from pathlib import Path
root=Path(__file__).resolve().parent
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(root/'source'/'scene.gltf'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in meshes:
 world=o.matrix_world.copy();o.parent=None;o.matrix_world=world
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 if o.data.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
# Layered ivory coat: warm dorsal planes, cool underfur, irregular brush grain.
fur=bpy.data.materials.new('Ivory fur - warm light cool shadow');fur.use_nodes=True
nodes=fur.node_tree.nodes;links=fur.node_tree.links;bs=nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.9;bs.inputs['Specular IOR Level'].default_value=.18
geo=nodes.new('ShaderNodeNewGeometry');sep=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Normal'],sep.inputs[0])
ramp=nodes.new('ShaderNodeValToRGB');links.new(sep.outputs['Z'],ramp.inputs[0]);ramp.color_ramp.elements.remove(ramp.color_ramp.elements[1])
for i,(pos,col) in enumerate([(0,(.43,.46,.46,1)),(.28,(.67,.68,.65,1)),(.57,(.82,.8,.7,1)),(1,(.95,.88,.73,1))]):
 e=ramp.color_ramp.elements[0] if i==0 else ramp.color_ramp.elements.new(pos);e.position=pos;e.color=col
tex=nodes.new('ShaderNodeTexNoise');tex.inputs['Scale'].default_value=3.5;tex.inputs['Detail'].default_value=3;links.new(geo.outputs['Position'],tex.inputs['Vector'])
variation=nodes.new('ShaderNodeValToRGB');variation.color_ramp.elements[0].color=(.65,.68,.7,1);variation.color_ramp.elements[1].color=(1,1,.96,1);links.new(tex.outputs['Fac'],variation.inputs[0])
mix=nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.35;links.new(ramp.outputs[0],mix.inputs[1]);links.new(variation.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],bs.inputs['Base Color'])
scale=nodes.new('ShaderNodeVectorMath');scale.operation='MULTIPLY';scale.inputs[1].default_value=(28,4,70);links.new(geo.outputs['Position'],scale.inputs[0]);grain=nodes.new('ShaderNodeTexNoise');grain.inputs['Scale'].default_value=1;grain.inputs['Detail'].default_value=2;links.new(scale.outputs[0],grain.inputs[0]);bump=nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.15;bump.inputs['Distance'].default_value=.016;links.new(grain.outputs['Fac'],bump.inputs['Height']);links.new(bump.outputs[0],bs.inputs['Normal'])
for o in meshes:
 o.data.materials.clear();o.data.materials.append(fur)
 for face in o.data.polygons:face.use_smooth=True
# Crisp, surface-fitted ink ribbons avoid blurred per-vertex markings.
from mathutils.bvhtree import BVHTree
verts_all=[];polys_all=[]
for obj in meshes:
 offset=len(verts_all);verts_all.extend([v.co.copy() for v in obj.data.vertices]);polys_all.extend([[offset+i for i in p.vertices] for p in obj.data.polygons])
bvh=BVHTree.FromPolygons(verts_all,polys_all)
red=bpy.data.materials.new('Vermilion ink');red.diffuse_color=(.72,.015,.006,1)
from PIL import Image,ImageDraw
mask=Image.new('RGBA',(2048,1280),(0,0,0,0));draw=ImageDraw.Draw(mask)
def ribbon(name,points,width,side):
 if side<0:return
 left=[];right=[]
 for i,(y,z) in enumerate(points):
  t=i/max(1,len(points)-1);w=width*(.025+.975*math.sin(math.pi*t)**.65)
  prev=Vector(points[max(0,i-1)]);nxt=Vector(points[min(len(points)-1,i+1)]);d=(nxt-prev).normalized();normal=Vector((-d.y,d.x))
  for sign,edge in [(-1,left),(1,right)]:
   q=Vector((y,z))+normal*w*sign/2;edge.append(((q.x+4.5)/9*2048,(1-q.y/5.6)*1280))
 draw.polygon(left+right[::-1],fill=(185,22,10,255))
def smoothpath(control):
 result=[]
 for i in range(len(control)-1):
  p0=Vector(control[max(0,i-1)]);p1=Vector(control[i]);p2=Vector(control[i+1]);p3=Vector(control[min(len(control)-1,i+2)])
  for j in range(35):
   t=j/35;v=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t);result.append(tuple(v))
 result.append(control[-1]);return result
for side in [-1,1]:
 points=[]
 for i in range(240):
  a=i/239*math.tau*1.22;r=.06+.52*i/239;points.append((-1.35+r*math.cos(a),3.85+r*math.sin(a)))
 ribbon('Shoulder - broad vermilion spiral',points,.17,side)
 for name,controls,width in [
 ('Brow rising flame',[(-3.56,4.60),(-3.32,4.80),(-3.00,4.94),(-2.78,5.13)],.17),
 ('Eye swept mask',[(-3.5,4.58),(-3.28,4.50),(-3.01,4.61),(-2.83,4.77)],.13),
 ('Cheek tapered stroke',[(-3.56,4.33),(-3.37,4.32),(-3.12,4.40),(-2.90,4.57)],.12),
 ('Back flame',[(-1.0,4.25),(-.35,4.08),(.65,3.91),(1.55,3.83),(2.20,4.00)],.16),
 ('Flank returning flame',[(-.15,3.75),(.60,3.59),(1.25,3.46),(1.75,3.62),(1.50,3.78)],.12),
 ('Forepaw curved paint',[(-2.20,.48),(-2.06,.70),(-1.91,.55),(-1.85,.31)],.09),
 ('Hindpaw curved paint',[(1.75,.39),(1.85,.68),(2.02,.60),(2.12,.36)],.09)]:ribbon(name,smoothpath(controls),width,side)
 # Upper eye placement, seated against the actual head surface.
 eye_y=-3.20;eye_z=4.64
 hit=bvh.ray_cast(Vector((side*4,eye_y,eye_z)),Vector((-side,0,0)))[0]
 if hit:
  for label,shift,scale,color in [('Eye ink',.018,(.022,.12,.047),(.012,.009,.006,1)),('Eye amber',.036,(.012,.047,.034),(.60,.27,.018,1)),('Eye pupil',.048,(.008,.016,.031),(.006,.005,.004,1)),('Eye glint',.052,(.007,.011,.008),(.95,.91,.72,1))]:
   pos=(hit.x+side*shift,eye_y+(.017 if label=='Eye glint' else 0),eye_z+(.012 if label=='Eye glint' else 0))
   bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=pos);o=bpy.context.object;o.name=label;o.scale=scale;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);mat=bpy.data.materials.new(label);mat.diffuse_color=color;o.data.materials.append(mat);meshes.append(o)
# Paint projected onto the real surface; no raised geometry or shadow gaps.
mask.save(root/'vermilion-markings.png');paint_image=bpy.data.images.load(str(root/'vermilion-markings.png'));paint_image.pack()
paint_tex=nodes.new('ShaderNodeTexImage');paint_tex.image=paint_image;paint_tex.extension='CLIP'
position=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Position'],position.inputs[0]);uv=nodes.new('ShaderNodeCombineXYZ')
for component,offset,span,target_socket in [('Y',4.5,9,'X'),('Z',0,5.6,'Y')]:
 add=nodes.new('ShaderNodeMath');add.operation='ADD';add.inputs[1].default_value=offset;links.new(position.outputs[component],add.inputs[0]);divide=nodes.new('ShaderNodeMath');divide.operation='DIVIDE';divide.inputs[1].default_value=span;links.new(add.outputs[0],divide.inputs[0]);links.new(divide.outputs[0],uv.inputs[target_socket])
links.new(uv.outputs[0],paint_tex.inputs[0]);ink_mix=nodes.new('ShaderNodeMixRGB');ink_mix.inputs[2].default_value=(.48,.009,.003,1);links.new(paint_tex.outputs['Alpha'],ink_mix.inputs[0]);links.new(mix.outputs[0],ink_mix.inputs[1]);links.new(ink_mix.outputs[0],bs.inputs['Base Color'])
# Nose pigment placed on the tip, rather than darkening the entire muzzle.
bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=16,location=(0,-4.15,4.10));nose=bpy.context.object;nose.name='Ink nose';nose.scale=(.20,.10,.14);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True);ink=bpy.data.materials.new('Nose charcoal');ink.diffuse_color=(.025,.02,.017,1);nose.data.materials.append(ink);meshes.append(nose)

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
# Bake the coat into a portable texture so GLB and Blender carry the same tones.
coat=[o for o in meshes if o.data.materials[0]==fur]
bpy.ops.object.select_all(action='DESELECT')
for o in coat:o.select_set(True)
bpy.context.view_layer.objects.active=coat[0];bpy.ops.object.join();combined=bpy.context.object;combined.name='Wolf ivory coat'
meshes=[o for o in meshes if o not in coat]+[combined]
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.025);bpy.ops.object.mode_set(mode='OBJECT')
atlas=bpy.data.images.new('Painted ivory fur atlas',width=4096,height=4096);target=nodes.new('ShaderNodeTexImage');target.image=atlas;nodes.active=target
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=False;scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True;scene.render.bake.margin=4
active=rig.animation_data.action;rig.animation_data.action=None
for b in rig.pose.bones:b.rotation_euler=(0,0,0);b.location=(0,0,0)
bpy.context.view_layer.update();bpy.ops.object.bake(type='DIFFUSE')
atlas.filepath_raw=str(root/'fur-tones.png');atlas.file_format='PNG';atlas.save();atlas.pack();links.new(target.outputs['Color'],bs.inputs['Base Color'])
rig.animation_data.action=active
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(root/'colored-rigged.glb'),use_selection=True,export_animations=True,export_nla_strips=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=96;scene.cycles.use_denoising=False
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.55,.55,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.28
scene.view_settings.view_transform='AgX'
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.05));floor=bpy.context.object;m=bpy.data.materials.new('Backdrop');m.diffuse_color=(.25,.28,.3,1);floor.data.materials.append(m)
for pos,power in [((5,-6,10),1700),((-5,1,8),650)]:
 bpy.ops.object.light_add(type='AREA',location=pos);l=bpy.context.object;l.data.energy=power;l.data.size=5;l.rotation_euler=(Vector((0,0,2.5))-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(13,-7,7));camera=bpy.context.object;camera.rotation_euler=(Vector((0,0,2.5))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=11;scene.camera=camera
scene.render.resolution_x=1000;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.frame_set(1);scene.render.filepath=str(root/'colored-preview.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'colored-rigged.blend'))
scene.render.resolution_x=500;scene.render.resolution_y=400;scene.cycles.samples=8
for f in range(1,33,2):
 scene.frame_set(f);scene.render.filepath=str(Path('/tmp')/f'polished-walk-{f:02}.png');bpy.ops.render.render(write_still=True)
print('COLOR_AND_RIG_COMPLETE')

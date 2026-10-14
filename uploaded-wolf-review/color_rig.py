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
mask=Image.new('RGBA',(4096,2560),(0,0,0,0));draw=ImageDraw.Draw(mask)
def ribbon(name,points,width,side):
 if side<0:return
 left=[];right=[]
 for i,(y,z) in enumerate(points):
  t=i/max(1,len(points)-1);w=width*(.025+.975*math.sin(math.pi*t)**.65)
  prev=Vector(points[max(0,i-1)]);nxt=Vector(points[min(len(points)-1,i+1)]);d=(nxt-prev).normalized();normal=Vector((-d.y,d.x))
  for sign,edge in [(-1,left),(1,right)]:
   q=Vector((y,z))+normal*w*sign/2;edge.append(((q.x+4.5)/9*4096,(1-q.y/5.6)*2560))
 draw.polygon(left+right[::-1],fill=(185,22,10,255))
def smoothpath(control):
 result=[]
 for i in range(len(control)-1):
  p0=Vector(control[max(0,i-1)]);p1=Vector(control[i]);p2=Vector(control[i+1]);p3=Vector(control[min(len(control)-1,i+2)])
  for j in range(35):
   t=j/35;v=.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t);result.append(tuple(v))
 result.append(control[-1]);return result
# Tapered ink shapes use the surface itself: no eyeball or nose meshes.
def polygon(points,color):
 draw.polygon([((y+4.5)/9*4096,(1-z/5.6)*2560) for y,z in points],fill=color)
for side in [1]:
 points=[]
 for i in range(260):
  a=i/259*math.tau*1.10;r=.045+.46*i/259;points.append((-1.12+r*math.cos(a),3.83+r*math.sin(a)))
 ribbon('Flank spiral',points,.10,side)
 for name,controls,width in [
 ('Chest ascending flame',[(-2.02,3.10),(-1.91,3.56),(-1.64,3.94),(-1.36,4.16)],.12),
 ('Flank sickle',[(-.25,3.36),(.24,3.28),(.71,3.39),(1.12,3.70)],.13),
 ('Foreleg sweep',[(-1.63,.35),(-1.36,.57),(-1.20,.83),(-1.23,1.04)],.085),
 ('Hock sweep',[(1.83,.29),(2.06,.48),(2.13,.79),(2.03,.96)],.075)]:ribbon(name,smoothpath(controls),width,side)
 # Forked, angular eye mask and forehead flame; no three parallel cheek bars.
 polygon([(-3.62,4.46),(-3.37,4.63),(-3.20,4.83),(-2.87,5.04),(-3.08,4.80),(-3.21,4.67),(-3.46,4.49)],(185,22,10,255))
 polygon([(-3.44,4.49),(-3.18,4.52),(-2.91,4.75),(-3.07,4.46),(-3.24,4.37)],(185,22,10,255))
 polygon([(-3.24,4.84),(-3.13,4.96),(-2.98,5.08),(-3.01,4.86),(-3.11,4.76)],(185,22,10,255))
 # Small ink almond, inclined with the brow and painted flush to the head.
 polygon([(y-.04,z+.035) for y,z in [(-3.40,4.58),(-3.30,4.64),(-3.12,4.64),(-3.24,4.57),(-3.34,4.56)]],(15,13,10,255))

# Paint projected onto the real surface; no raised geometry or shadow gaps.
mask.save(root/'vermilion-markings.png');paint_image=bpy.data.images.load(str(root/'vermilion-markings.png'));paint_image.pack()
paint_tex=nodes.new('ShaderNodeTexImage');paint_tex.image=paint_image;paint_tex.extension='CLIP'
position=nodes.new('ShaderNodeSeparateXYZ');links.new(geo.outputs['Position'],position.inputs[0]);uv=nodes.new('ShaderNodeCombineXYZ')
for component,offset,span,target_socket in [('Y',4.5,9,'X'),('Z',0,5.6,'Y')]:
 add=nodes.new('ShaderNodeMath');add.operation='ADD';add.inputs[1].default_value=offset;links.new(position.outputs[component],add.inputs[0]);divide=nodes.new('ShaderNodeMath');divide.operation='DIVIDE';divide.inputs[1].default_value=span;links.new(add.outputs[0],divide.inputs[0]);links.new(divide.outputs[0],uv.inputs[target_socket])
links.new(uv.outputs[0],paint_tex.inputs[0]);ink_mix=nodes.new('ShaderNodeMixRGB');links.new(paint_tex.outputs['Alpha'],ink_mix.inputs[0]);links.new(paint_tex.outputs['Color'],ink_mix.inputs[2]);links.new(mix.outputs[0],ink_mix.inputs[1]);links.new(ink_mix.outputs[0],bs.inputs['Base Color'])
# Pigment on the original muzzle tip, not an added spherical nose.
y_tip=nodes.new('ShaderNodeMath');y_tip.operation='LESS_THAN';y_tip.inputs[1].default_value=-4.06;links.new(position.outputs['Y'],y_tip.inputs[0])
z_tip=nodes.new('ShaderNodeMath');z_tip.operation='GREATER_THAN';z_tip.inputs[1].default_value=4.03;links.new(position.outputs['Z'],z_tip.inputs[0])
nose_mask=nodes.new('ShaderNodeMath');nose_mask.operation='MULTIPLY';links.new(y_tip.outputs[0],nose_mask.inputs[0]);links.new(z_tip.outputs[0],nose_mask.inputs[1]);nose_mix=nodes.new('ShaderNodeMixRGB');nose_mix.inputs[2].default_value=(.016,.012,.009,1);links.new(nose_mask.outputs[0],nose_mix.inputs[0]);links.new(ink_mix.outputs[0],nose_mix.inputs[1]);links.new(nose_mix.outputs[0],bs.inputs['Base Color'])

# A genuine deforming skeleton, with independent upper/lower leg articulation.
bpy.ops.object.armature_add();rig=bpy.context.object;rig.name='DivineWolfRig';bpy.ops.object.mode_set(mode='EDIT');rig.data.edit_bones.remove(rig.data.edit_bones[0])
def bone(name,head,tail,parent=None):
 b=rig.data.edit_bones.new(name);b.head=head;b.tail=tail
 if parent:b.parent=rig.data.edit_bones[parent]
 return b
bone('body',(0,1,3),(0,-1.5,3))
bone('head',(0,-1.9,3.4),(0,-3.4,4.2),'body')
bone('tail',(0,2.4,3),(0,3.8,2.6),'body')
leg_specs={}
for side,x in [('L',.61),('R',-.61)]:
 for leg in ['fore','hind']:
  name=leg+side
  if leg=='fore':joints=[(x,-1.42,3.02),(x,-1.20,1.68),(x,-1.36,.46),(x,-1.76,.18)]
  else:joints=[(x,2.35,3.08),(x,1.80,1.94),(x,2.22,.68),(x,1.82,.18)]
  bone(name,joints[0],joints[1],'body');bone(leg+'Shin'+side,joints[1],joints[2],name);bone(leg+'Paw'+side,joints[2],joints[3],leg+'Shin'+side)
  level=bone(name+'Level',joints[2],joints[3]);level.use_deform=False
  target=bone(name+'Target',joints[2],(x,joints[2][1],joints[2][2]+.2));target.use_deform=False
  pole=bone(name+'Pole',(x,(4 if leg=='fore' else -5),1.5),(x,(4 if leg=='fore' else -5),1.8));pole.use_deform=False
  leg_specs[name]=(joints,leg,side)
bpy.ops.object.mode_set(mode='OBJECT')
# Smooth anatomical joint zones; toes follow their own paw bone.
def smoothstep(v):
 t=max(0,min(1,v));return t*t*(3-2*t)
for o in meshes:
 groups={b.name:o.vertex_groups.new(name=b.name) for b in rig.data.bones if b.use_deform}
 for v in o.data.vertices:
  x,y,z=v.co;side='L' if x>=0 else 'R';weights={'body':1}
  if o.name=='Object_7' or y>2.85:
   weights={'tail':1}
  elif z<2.95 and abs(x)>.26 and (y<-1.00 or y>1.30):
   leg='fore' if y<0 else 'hind';attach=smoothstep((2.95-z)/.60)
   knee=1.68 if leg=='fore' else 1.94;lower=smoothstep((knee+.22-z)/.48);paw=smoothstep((.66-z)/.35)
   weights={'body':1-attach,leg+side:attach*(1-lower),leg+'Shin'+side:attach*lower*(1-paw),leg+'Paw'+side:attach*lower*paw}
  elif y<-2.10 and z>2.8:
   t=smoothstep((-y-2.10)/.65);weights={'body':1-t,'head':t}
  elif y>2.75 and z>1:
   t=smoothstep((y-2.75)/.55);weights={'body':1-t,'tail':t}
  for n,w in weights.items():
   if w>0:groups[n].add([v.index],w,'REPLACE')
 mod=o.modifiers.new('Wolf skeleton','ARMATURE');mod.object=rig;o.parent=rig
for name,(joints,leg,side) in leg_specs.items():
 ik=rig.pose.bones[leg+'Shin'+side].constraints.new('IK');ik.target=rig;ik.subtarget=name+'Target';ik.chain_count=2;ik.pole_target=rig;ik.pole_subtarget=name+'Pole';ik.pole_angle=-math.pi/2
 # Calibrate pole rotation against the imported rest pose instead of guessing it.
 best=(float('inf'),0)
 for angle in [-math.pi,-math.pi/2,0,math.pi/2]:
  ik.pole_angle=angle;bpy.context.view_layer.update();distance=(rig.pose.bones[leg+'Shin'+side].head-Vector(joints[1])).length
  if distance<best[0]:best=(distance,angle)
 ik.pole_angle=best[1]
 level=rig.pose.bones[leg+'Paw'+side].constraints.new('COPY_ROTATION');level.target=rig;level.subtarget=name+'Level';level.target_space='WORLD';level.owner_space='WORLD'
 print('REST_JOINT_ERROR',name,best[0])
# Feet push back on the ground, then flex and recover during the swing.
for clip,duration in [('Idle',96),('Walk',48)]:
 rig.animation_data_create();action=bpy.data.actions.new(clip);rig.animation_data.action=action
 for f in range(1,duration+2):
  cycle=(f-1)/duration;phase=cycle*math.tau
  for b in rig.pose.bones:b.rotation_mode='XYZ';b.rotation_euler=(0,0,0);b.location=(0,0,0)
  rig.pose.bones['body'].location.z=-.12+.015*math.sin(phase*2) if clip=='Walk' else .012*math.sin(phase)
  rig.pose.bones['body'].rotation_euler.x=.008*math.sin(phase*2)
  rig.pose.bones['head'].rotation_euler.x=.012*math.sin(phase*2+.6)
  rig.pose.bones['tail'].rotation_euler.z=.065*math.sin(phase-.7)
  for name,(joints,leg,side) in leg_specs.items():
   offset={('fore','L'):0,('hind','R'):.16,('fore','R'):.5,('hind','L'):.66}[(leg,side)]
   t=(cycle+offset)%1
   stride=.95 if leg=='fore' else .84
   if clip=='Walk':
    if t<.62:
     u=t/.62;dy=-stride/2+stride*u;lift=0;curl=0
    else:
     u=(t-.62)/.38;v=.38/.62;dy=stride*(.5-3*u*u+2*u*u*u+v*(2*u*u*u-3*u*u+u));lift=(.31 if leg=='fore' else .27)*math.sin(math.pi*u)**2;curl=.32*math.sin(math.pi*u)**2
    target=rig.pose.bones[name+'Target'];target.location=target.bone.matrix_local.to_3x3().inverted() @ Vector((0,dy,lift))
    # Paw counter-rotation keeps the sole level during contact.
    rig.pose.bones[name+'Level'].rotation_euler.x=-curl
   for suffix in ['Target','Pole','Level']:
    b=rig.pose.bones[name+suffix];b.keyframe_insert('location',frame=f);b.keyframe_insert('rotation_euler',frame=f)
  for b in rig.pose.bones:
   if b.bone.use_deform:b.keyframe_insert('rotation_euler',frame=f);b.keyframe_insert('location',frame=f)
 # Bake evaluated IK into ordinary joint keys for portable GLB animation.
 bpy.context.view_layer.objects.active=rig;rig.select_set(True)
 bpy.ops.nla.bake(frame_start=1,frame_end=duration+1,step=1,only_selected=False,visual_keying=True,clear_constraints=False,use_current_action=True,bake_types={'POSE'})
 track=rig.animation_data.nla_tracks.new();track.name=clip;strip=track.strips.new(clip,1,action);track.mute=True
for b in rig.pose.bones:
 for constraint in list(b.constraints):b.constraints.remove(constraint)
rig.animation_data.action=bpy.data.actions['Idle']
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
scene.render.use_freestyle=True;scene.render.line_thickness=1.3
line=scene.view_layers[0].freestyle_settings.linesets[0];line.select_crease=False;line.select_contour=False;line.select_external_contour=True;line.linestyle.color=(.04,.035,.03);line.linestyle.alpha=.90
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.05));floor=bpy.context.object;m=bpy.data.materials.new('Backdrop');m.diffuse_color=(.25,.28,.3,1);floor.data.materials.append(m)
for pos,power in [((5,-6,10),1700),((-5,1,8),650)]:
 bpy.ops.object.light_add(type='AREA',location=pos);l=bpy.context.object;l.data.energy=power;l.data.size=5;l.rotation_euler=(Vector((0,0,2.5))-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(13,-7,7));camera=bpy.context.object;camera.rotation_euler=(Vector((0,0,2.5))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=11;scene.camera=camera
scene.render.resolution_x=1000;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.frame_set(1);scene.render.filepath=str(root/'colored-preview.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'colored-rigged.blend'))
rig.animation_data.action=bpy.data.actions['Walk']
scene.render.resolution_x=600;scene.render.resolution_y=480;scene.cycles.samples=12
for f in range(1,49):
 scene.frame_set(f);scene.render.filepath=str(Path('/tmp')/f'soft-walk-{f:02}.png');bpy.ops.render.render(write_still=True)
print('COLOR_AND_RIG_COMPLETE')

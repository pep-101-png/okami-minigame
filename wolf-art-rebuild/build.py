import bpy,math,bmesh,os,numpy as np
from mathutils import Vector
from pathlib import Path
root=Path(__file__).resolve().parent
revision=os.environ.get('WOLF_REVISION','final');draft=os.environ.get('WOLF_DRAFT','1')=='1'
review=root/'review';review.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
bpy.ops.import_scene.gltf(filepath=str(root/'source'/'scene.gltf'))
meshes=[o for o in bpy.context.scene.objects if o.type=='MESH']
for o in list(meshes):
 if o.name!='Object_2':
  meshes.remove(o);bpy.data.objects.remove(o,do_unlink=True)
for o in meshes:
 world=o.matrix_world.copy();o.parent=None;o.matrix_world=world
 bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
 if o.data.has_custom_normals:bpy.ops.mesh.customdata_custom_splitnormals_clear()
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.001);bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 # Close the stock model's snarling jaw, keeping its original muzzle shape.
 for v in o.data.vertices:
  x,y,z=v.co
  if y<-3.30 and 3.80<z<4.12:
   weight=max(0,min(1,(-y-3.30)/.32));v.co.z+=.105*weight
 # Keep the original body while replacing its coarse stock tail in this derivative.
 if o.name in ['Object_2','Object_6','Object_10','Object_11']:
  bm=bmesh.new();bm.from_mesh(o.data);remove=[v for v in bm.verts if v.co.y>2.89 or (v.co.y>2.35 and abs(v.co.x)<.46 and 1.05<v.co.z<3.05)];bmesh.ops.delete(bm,geom=remove,context='VERTS');bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
 o.data.update()
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
# Swept layered mane is part of the model, rather than a trailing particle overlay.
flow_specs=[]
def plume(name,start,end,width,depth):
 start=Vector(start);end=Vector(end);direction=(end-start).normalized();across=direction.cross(Vector((1,0,0))).normalized()
 if across.length<.01:across=Vector((0,1,0))
 thick=direction.cross(across).normalized();verts=[];faces=[];count=12;ring=8
 for j in range(count):
  t=j/(count-1);center=start.lerp(end,t)+Vector((0,-.10*math.sin(math.pi*t),.09*math.sin(math.pi*t)))
  taper=max(.002,(math.sin(math.pi*(.16+.84*t))**.8)*(1-t)**.25)
  for k in range(ring):
   a=k/ring*math.tau;verts.append(center+across*math.cos(a)*width*taper+thick*math.sin(a)*depth*taper)
 for j in range(count-1):
  for k in range(ring):a=j*ring+k;b=j*ring+(k+1)%ring;faces.append((a,b,b+ring,a+ring))
 faces.append(tuple(range(ring-1,-1,-1)));faces.append(tuple((count-1)*ring+k for k in range(ring)))
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(fur)
 for face in mesh.polygons:face.use_smooth=True
 obj['flow_name']=name;flow_specs.append((name,tuple(start),tuple(end)));meshes.append(obj)
# A continuous ruff connects the layers so they read as fur, not pasted-on fins.
verts=[];faces=[];rings=[(-2.73,4.65,.56,.27),(-2.48,4.39,.69,.38),(-2.18,4.02,.83,.46),(-1.93,3.66,.92,.48),(-1.85,3.39,.78,.34)]
for j,(y,z,rx,ry) in enumerate(rings):
 for k in range(32):
  a=k/32*math.tau;verts.append((math.cos(a)*rx,y+math.sin(a)*ry,z+.065*math.cos(a*6+j*.6)))
for j in range(len(rings)-1):
 for k in range(32):a=j*32+k;b=j*32+(k+1)%32;faces.append((a,b,b+32,a+32))
faces.append(tuple(range(31,-1,-1)));faces.append(tuple((len(rings)-1)*32+k for k in range(32)))
mesh=bpy.data.meshes.new('Continuous layered ruff');mesh.from_pydata(verts,[],faces);mesh.update();obj=bpy.data.objects.new('Continuous layered ruff',mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(fur)
for f in mesh.polygons:f.use_smooth=True
meshes.append(obj)
for side in [-1,1]:
 for i in range(5):
  z=4.73-i*.25;y=-2.70+i*.18;x=side*(.52+.075*i)
  plume('Mane_%s_%s'%(side,i),(x,y,z),(x+side*.16,y+.70,z-.17),.23,.062)
 for i in range(2):
  plume('Cheek_%s_%s'%(side,i),(side*.45,-2.98+i*.17,4.26-i*.15),(side*(.65+i*.06),-2.44+i*.22,4.08-i*.19),.15,.045)
for i in range(2):plume('Dorsal_%s'%i,(0,-1.65+i*.27,4.55),(0,-.78+i*.35,4.58),.16,.065)
# A tapered curled tail, with a rounded fur volume rather than a flat paddle.
path=[(2.15,3.04,.28,.22),(2.70,3.09,.37,.32),(3.20,3.24,.44,.40),(3.65,3.53,.36,.34),(4.02,3.90,.23,.22),(4.22,4.14,.07,.075),(4.24,4.29,.003,.003)]
verts=[];faces=[]
for j,(y,z,rx,rz) in enumerate(path):
 for k in range(16):
  a=k/16*math.tau;verts.append((math.cos(a)*rx,y+math.sin(a)*rz*.50,z+math.sin(a)*rz))
for j in range(len(path)-1):
 for k in range(16):a=j*16+k;b=j*16+(k+1)%16;faces.append((a,b,b+16,a+16))
faces.append(tuple(range(15,-1,-1)));faces.append(tuple((len(path)-1)*16+k for k in range(16)))
mesh=bpy.data.meshes.new('Curled fur tail');mesh.from_pydata(verts,[],faces);mesh.update();obj=bpy.data.objects.new('Curled fur tail',mesh);bpy.context.collection.objects.link(obj);obj.data.materials.append(fur);meshes.append(obj)
# Exact union preserves the uploaded anatomy and joins the overlapping fur volumes.
base=next(o for o in meshes if o.name=='Object_2');addons=[o for o in meshes if o!=base]
for o in meshes:
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.001);bmesh.ops.holes_fill(bm,edges=[e for e in bm.edges if e.is_boundary],sides=0);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
 print('INPUT_VOLUME',o.name,bm.calc_volume(signed=True),flush=True);bm.to_mesh(o.data);bm.free()
bpy.ops.object.select_all(action='DESELECT')
for o in addons:o.select_set(True)
bpy.context.view_layer.objects.active=addons[0];bpy.ops.object.join();extra=bpy.context.object;extra.name='Sculpted fur volumes'
bpy.ops.object.select_all(action='DESELECT');base.select_set(True);bpy.context.view_layer.objects.active=base
union=base.modifiers.new('Coherent sculpted fur','BOOLEAN');union.operation='UNION';union.solver='EXACT';union.use_self=True;union.object=extra;bpy.ops.object.modifier_apply(modifier=union.name)
bpy.data.objects.remove(extra,do_unlink=True);body=base;body.name='Sculpted coherent coat';meshes=[body];flow_specs=[]
bm=bmesh.new();bm.from_mesh(body.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.001);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));volume=bm.calc_volume(signed=True);boundary=sum(e.is_boundary for e in bm.edges);print('FUSED_COAT_VOLUME',volume,'BOUNDARY_EDGES',boundary,flush=True);assert volume>9,'Fusion lost the body';bm.to_mesh(body.data);bm.free()
for face in body.data.polygons:face.use_smooth=True
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
 for i in range(420):
  a=.22+i/419*math.tau*1.22;r=.045+.48*i/419;points.append((-.50+r*math.cos(a),3.62+r*math.sin(a)))
 ribbon('Shoulder vermilion spiral',points,.13,side)
 for name,controls,width in [
 ('Neck flame',[(-2.12,3.10),(-2.08,3.48),(-1.87,3.91),(-1.53,4.29)],.18),
 ('Neck returning flame',[(-2.16,3.54),(-2.20,3.92),(-2.09,4.26)],.08),
 ('Flank pointed sweep',[(-.15,3.22),(.40,3.24),(.99,3.56),(1.21,3.86)],.17),
 ('Upper returning sweep',[(.16,3.48),(.72,3.71),(.94,4.03)],.065),
 ('Foreleg flame',[(-1.70,.40),(-1.44,.77),(-1.28,1.24),(-1.35,1.55)],.10),
 ('Hock flame',[(1.86,.30),(2.15,.65),(2.18,1.05),(2.08,1.23)],.095)]:ribbon(name,smoothpath(controls),width,side)
 for cy,cz,radius in [(3.35,3.25,.20),(3.93,3.55,.12)]:
  points=[]
  for i in range(200):
   a=i/199*math.tau*1.30;r=.025+radius*i/199;points.append((cy+r*math.cos(a),cz+r*math.sin(a)))
  # Reuse the tapered stroke, then replace its colour with soft charcoal.
  left=[];right=[]
  for i,(y,z) in enumerate(points):
   a=Vector(points[max(0,i-1)]);b=Vector(points[min(len(points)-1,i+1)]);d=(b-a).normalized();n=Vector((-d.y,d.x));width=.022*math.sin(math.pi*i/199)**.6
   left.append(tuple(Vector((y,z))-n*width));right.append(tuple(Vector((y,z))+n*width))
  polygon(left+right[::-1],(42,38,30,255))
 # Painted ornamental scrolls give the existing white fur folds a clear ink identity.
 for cy,cz,radius in [(-1.30,3.55,.22),(-1.08,.79,.115),(2.13,.82,.13)]:
  points=[]
  for i in range(240):
   a=i/239*math.tau*1.40;r=.014+radius*i/239;points.append((cy+r*math.cos(a),cz+r*math.sin(a)))
  left=[];right=[]
  for i,(y,z) in enumerate(points):
   a=Vector(points[max(0,i-1)]);b=Vector(points[min(len(points)-1,i+1)]);d=(b-a).normalized();n=Vector((-d.y,d.x));width=.013*math.sin(math.pi*i/239)**.7
   left.append(tuple(Vector((y,z))-n*width));right.append(tuple(Vector((y,z))+n*width))
  polygon(left+right[::-1],(33,29,23,255))
 # Calligraphic brow sweeps, placed around the unchanged slightly raised ink eye.
 polygon([(-3.66,4.48),(-3.48,4.65),(-3.27,4.86),(-3.00,5.02),(-3.10,4.83),(-3.37,4.63)],(185,22,10,255))
 polygon([(-3.48,4.51),(-3.26,4.56),(-3.00,4.77),(-3.14,4.49),(-3.34,4.44)],(185,22,10,255))
 polygon([(-3.38,4.85),(-3.21,5.03),(-2.96,5.18),(-3.10,4.96),(-3.29,4.82)],(185,22,10,255))
 polygon([(y-.04,z+.035) for y,z in [(-3.40,4.58),(-3.30,4.64),(-3.12,4.64),(-3.24,4.57),(-3.34,4.56)]],(15,13,10,255))
 # Delicate ink fur strokes; these are surface paint, not floating geometry.
 for i in range(7):
  y=-2.76+i*.09;z=4.66-i*.15
  points=smoothpath([(y,z),(y+.15,z-.05),(y+.28,z+.015)])
  left=[];right=[]
  for j,(a,b) in enumerate(points):
   width=.020*math.sin(math.pi*j/(len(points)-1))
   left.append((a,b-width));right.append((a,b+width))
  polygon(left+right[::-1],(35,31,25,220))
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
bone('hips',(0,2.30,3.15),(0,.82,3.35),'body')
bone('chest',(0,.82,3.35),(0,-1.55,3.58),'body')
bone('neck',(0,-1.55,3.58),(0,-2.60,4.35),'chest')
bone('head',(0,-2.60,4.35),(0,-3.70,4.35),'neck')
bone('tail',(0,2.55,3.15),(0,3.48,3.23),'hips');bone('tailTip',(0,3.48,3.23),(0,4.35,4.10),'tail')
for name,start,end in flow_specs:
 middle=Vector(start).lerp(Vector(end),.52);parent='tail' if name.startswith('Tail') else 'head' if name.startswith('Cheek') else 'neck' if name.startswith('Mane') else 'chest'
 bone(name, start, middle,parent);bone(name+'Tip',middle,end,name)
leg_specs={}
for side,x in [('L',.61),('R',-.61)]:
 for leg in ['fore','hind']:
  name=leg+side
  if leg=='fore':joints=[(x,-1.42,3.02),(x,-1.20,1.68),(x,-1.36,.46),(x,-1.76,.18)]
  else:joints=[(x,2.35,3.08),(x,1.80,1.94),(x,2.22,.68),(x,1.82,.18)]
  bone(name,joints[0],joints[1],'chest' if leg=='fore' else 'hips');bone(leg+'Shin'+side,joints[1],joints[2],name);bone(leg+'Paw'+side,joints[2],joints[3],leg+'Shin'+side)
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
  x,y,z=v.co;side='L' if x>=0 else 'R';chest=smoothstep((1.60-y)/2.70);weights={'chest':chest,'hips':1-chest}
  if o.get('flow_name'):
   name=o['flow_name'];info=next(info for info in flow_specs if info[0]==name);start=Vector(info[1]);end=Vector(info[2]);t=max(0,min(1,(v.co-start).dot(end-start)/(end-start).length_squared));tip=smoothstep((t-.25)/.60);weights={name:1-tip,name+'Tip':tip}
  elif y>2.60 and z>2.55:
   root_weight=smoothstep((y-2.60)/.50);tip=smoothstep((y-3.24)/.85);weights={'hips':1-root_weight,'tail':root_weight*(1-tip),'tailTip':root_weight*tip}
  elif z<2.95 and abs(x)>.26 and (y<-1.00 or y>1.30):
   leg='fore' if y<0 else 'hind';attach=smoothstep((2.95-z)/.60)
   knee=1.68 if leg=='fore' else 1.94;lower=smoothstep((knee+.22-z)/.48);paw=smoothstep((.66-z)/.35)
   weights={('chest' if leg=='fore' else 'hips'):1-attach,leg+side:attach*(1-lower),leg+'Shin'+side:attach*lower*(1-paw),leg+'Paw'+side:attach*lower*paw}
  elif y<-2.10 and z>2.8:
   t=smoothstep((-y-2.35)/.72);weights={'neck':1-t,'head':t}
  elif y>2.75 and z>1:
   t=smoothstep((y-2.75)/.55);weights={'hips':1-t,'tail':t}
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
  rig.pose.bones['body'].location.z=-.36+.045*math.sin(phase*2) if clip=='Walk' else .012*math.sin(phase)
  rig.pose.bones['body'].rotation_euler.x=.008*math.sin(phase*2)
  rig.pose.bones['head'].rotation_euler.x=.012*math.sin(phase*2+.6)
  rig.pose.bones['tail'].rotation_euler.z=.09*math.sin(phase-.7)
  rig.pose.bones['tailTip'].rotation_euler.z=.11*math.sin(phase-1.3)
  rig.pose.bones['chest'].rotation_euler.y=.045*math.sin(phase) if clip=='Walk' else .009*math.sin(phase)
  rig.pose.bones['hips'].rotation_euler.y=-.038*math.sin(phase) if clip=='Walk' else 0
  rig.pose.bones['chest'].rotation_euler.x=.024*math.sin(phase*2+.3) if clip=='Walk' else 0
  rig.pose.bones['neck'].rotation_euler.x=-.02*math.sin(phase*2+.3) if clip=='Walk' else .008*math.sin(phase)
  for i,(name,start,end) in enumerate(flow_specs):
   rig.pose.bones[name].rotation_euler.x=.045*math.sin(phase-.18*i)
   rig.pose.bones[name+'Tip'].rotation_euler.x=.07*math.sin(phase-.18*i-.5)
  for name,(joints,leg,side) in leg_specs.items():
   offset={('fore','L'):0,('hind','R'):.25,('fore','R'):.5,('hind','L'):.75}[(leg,side)]
   t=(cycle+offset)%1
   stride=2.05 if leg=='fore' else 1.78
   if clip=='Walk':
    if t<.62:
     u=t/.62;dy=-stride/2+stride*u;lift=0;curl=0
    else:
     u=(t-.62)/.38;v=.38/.62;dy=stride*(.5+v*u-(1+v)*(10*u**3-15*u**4+6*u**5));lift=(.44 if leg=='fore' else .34)*math.sin(math.pi*u)**3;curl=.39*math.sin(math.pi*u)**3
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
bpy.context.tool_settings.mesh_select_mode=(False,False,True)
for region in ['body','head']:
 bpy.ops.object.mode_set(mode='OBJECT')
 for v in combined.data.vertices:v.select=False
 for e in combined.data.edges:e.select=False
 for face in combined.data.polygons:
  head=face.center.y<-2.35 and face.center.z>3.30;face.select=(head if region=='head' else not head)
 bpy.ops.object.mode_set(mode='EDIT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
 uv=combined.data.uv_layers.active.data
 for face in combined.data.polygons:
  if face.select:
   for index in face.loop_indices:uv[index].uv.x=uv[index].uv.x*(.42 if region=='head' else .56)+(.58 if region=='head' else 0)
atlas=bpy.data.images.new('Painted ivory fur atlas',width=8192,height=8192);target=nodes.new('ShaderNodeTexImage');target.image=atlas;nodes.active=target
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=False;scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True;scene.render.bake.margin=4
active=rig.animation_data.action;rig.animation_data.action=None
for b in rig.pose.bones:b.rotation_euler=(0,0,0);b.location=(0,0,0)
bpy.context.view_layer.update();bpy.ops.object.bake(type='DIFFUSE')
atlas.filepath_raw=str(root/'fur-tones.png');atlas.file_format='PNG';atlas.save();atlas.pack();links.new(target.outputs['Color'],bs.inputs['Base Color'])
# A portable tangent normal map anchors the fur grain to the moving skin.
normal_atlas=bpy.data.images.new('Fur grain normals',width=2048,height=2048);normal_atlas.colorspace_settings.name='Non-Color';normal_atlas.generated_color=(.5,.5,1,1);normal_tex=nodes.new('ShaderNodeTexImage');normal_tex.image=normal_atlas;nodes.active=normal_tex;scene.render.bake.normal_space='TANGENT';scene.render.bake.use_clear=False;bpy.ops.object.bake(type='NORMAL')
normal_pixels=np.empty(len(normal_atlas.pixels),dtype=np.float32);normal_atlas.pixels.foreach_get(normal_pixels);normal_pixels=normal_pixels.reshape((-1,4));invalid=(normal_pixels[:,3]<.5)|(normal_pixels[:,2]<.85);normal_pixels[invalid]=(.5,.5,1,1);normal_atlas.pixels.foreach_set(normal_pixels.ravel());normal_atlas.update();print('NORMAL_BACKGROUND_REPAIRED',int(invalid.sum()))
normal_atlas.filepath_raw=str(root/'fur-normal.png');normal_atlas.file_format='PNG';normal_atlas.save();normal_atlas.pack();normal_node=nodes.new('ShaderNodeNormalMap');normal_node.uv_map=combined.data.uv_layers.active.name;links.new(normal_tex.outputs['Color'],normal_node.inputs['Color']);links.new(normal_node.outputs['Normal'],bs.inputs['Normal'])

rig.animation_data.action=active
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
for o in meshes:o.select_set(True)
bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(root/'wolf.glb'),use_selection=True,export_animations=True,export_nla_strips=True)
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=96;scene.cycles.use_denoising=False
scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.55,.55,.55,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.28
scene.view_settings.view_transform='AgX'
scene.view_settings.look='AgX - Medium High Contrast'
scene.render.use_freestyle=True;scene.render.line_thickness=1.3
line=scene.view_layers[0].freestyle_settings.linesets[0];line.select_crease=False;line.select_contour=False;line.select_external_contour=True;line.linestyle.color=(.04,.035,.03);line.linestyle.alpha=.90
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.05));floor=bpy.context.object;m=bpy.data.materials.new('Backdrop');m.diffuse_color=(.25,.28,.3,1);floor.data.materials.append(m)
for pos,power in [((5,-6,10),1700),((-5,1,8),650)]:
 bpy.ops.object.light_add(type='AREA',location=pos);l=bpy.context.object;l.data.energy=power;l.data.size=5;l.rotation_euler=(Vector((0,0,2.5))-l.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(13,-7,7));camera=bpy.context.object;camera.rotation_euler=(Vector((0,0,2.5))-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=11;scene.camera=camera
scene.render.resolution_x=1000;scene.render.resolution_y=800;scene.render.resolution_percentage=100
scene.frame_set(1);scene.cycles.samples=32 if draft else 128;scene.render.filepath=str(review/(revision+'-body.png'));bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'wolf.blend'))
rig.animation_data.action=bpy.data.actions['Walk']
scene.render.resolution_x=640;scene.render.resolution_y=512;scene.cycles.samples=12 if draft else 32
frames=[1,9,17,25,33,41] if draft else range(1,49)
for f in frames:
 scene.frame_set(f);scene.render.filepath=str(Path('/tmp')/f'{revision}-walk-{f:02}.png');bpy.ops.render.render(write_still=True)
print('ART_REBUILD_COMPLETE',revision)

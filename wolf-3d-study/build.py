import bpy, math, os
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=os.path.dirname(os.path.abspath(__file__))
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine='CYCLES';scene.cycles.samples=96;scene.cycles.use_denoising=False
scene.render.resolution_x=1280;scene.render.resolution_y=1000;scene.render.resolution_percentage=100
scene.world.use_nodes=True;scene.world.node_tree.nodes.get('Background').inputs['Color'].default_value=(.78,.82,.81,1);scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.28
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.render.image_settings.file_format='PNG'
scene.render.film_transparent=False

def mat(name,col,rough=1):
 m=bpy.data.materials.new(name);m.diffuse_color=(*col,1);m.use_nodes=True;n=m.node_tree.nodes;p=n.get('Principled BSDF');p.inputs['Base Color'].default_value=(*col,1);p.inputs['Roughness'].default_value=rough
 if name=='Ivory ink wash':
  noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=95;noise.inputs['Detail'].default_value=2
  ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(.88,.86,.78,1);ramp.color_ramp.elements[1].color=(*col,1);m.node_tree.links.new(noise.outputs['Fac'],ramp.inputs[0]);m.node_tree.links.new(ramp.outputs[0],p.inputs['Base Color'])
 if name.startswith('Flame'):
  p.inputs['Emission Color'].default_value=(*col,1);p.inputs['Emission Strength'].default_value=.35
 return m
ivory=mat('Ivory ink wash',(1,.98,.91));shadow=mat('Warm fur recess',(.7,.70,.62));ink=mat('Charcoal ink',(.025,.025,.023));red=mat('Vermilion paint',(.73,.032,.014));green=mat('Engraved turquoise',(.065,.48,.38));jade=mat('Dark jade engraving',(.025,.16,.115));gold=mat('Warm amber',(.9,.57,.095));orange=mat('Flame vermilion',(.96,.095,.005));yellow=mat('Flame golden core',(1,.49,.009));pink=mat('Inner ear wash',(.72,.65,.55))
parts=[]
def loft(name,points,radii,material=ivory,N=16,collect=False):
 verts=[];faces=[]
 for i,p in enumerate(points):
  p=Vector(p);tan=(Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])).normalized();a=Vector((0,1,0));a=(a-tan*a.dot(tan)).normalized();b=tan.cross(a)
  for j in range(N):
   t=j*math.tau/N;verts.append(p+a*(math.cos(t)*radii[i][0])+b*(math.sin(t)*radii[i][1]))
 for i in range(len(points)-1):
  for j in range(N):faces.append((i*N+j,i*N+(j+1)%N,(i+1)*N+(j+1)%N,(i+1)*N+j))
 faces.append(tuple(range(N-1,-1,-1)));faces.append(tuple((len(points)-1)*N+j for j in range(N)))
 me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.data.materials.append(material)
 for p in me.polygons:p.use_smooth=True
 if collect:parts.append(o)
 return o

def curve(name,points,material=ink,width=.007):
 if name in ['Head fur ink ridge','Tail plume ink ridge','Neck feather ridge']:return
 data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.resolution_u=16;data.bevel_depth=width;data.bevel_resolution=3;s=data.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
 for b,p in zip(s.bezier_points,points):b.co=p;b.handle_left_type='AUTO';b.handle_right_type='AUTO'
 ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob);ob.data.materials.append(material);return ob

# Continuous canine anatomy: thorax, tuck, pelvis, neck, skull and articulated legs.
loft('Anatomy torso',[(-.83,0,1.08),(-.66,0,1.16),(-.4,0,1.17),(-.12,0,1.19),(.2,0,1.25),(.48,0,1.29),(.66,0,1.30)],[(.12,.19),(.24,.30),(.21,.25),(.16,.20),(.23,.31),(.28,.39),(.20,.30)],collect=True)
loft('Upright neck',[(.4,0,1.32),(.59,0,1.49),(.74,0,1.71),(.91,0,1.89)],[(.24,.30),(.24,.29),(.20,.24),(.16,.20)],collect=True)
loft('Noble skull',[(.84,0,1.92),(1.00,0,1.98),(1.14,0,1.96),(1.26,0,1.91)],[(.13,.17),(.18,.22),(.17,.20),(.115,.125)],collect=True)
loft('Long wedge muzzle',[(1.17,0,1.86),(1.31,0,1.84),(1.45,0,1.82),(1.56,0,1.82)],[(.13,.115),(.11,.08),(.075,.055),(.053,.045)],collect=True)
for s in [-1,1]:
 y=s*.22
 loft('Front leg',[(.51,y,1.17),(.54,y,.99),(.48,y,.74),(.61,y,.48),(.66,y,.19),(.67,y,.09)],[(.115,.14),(.105,.13),(.065,.085),(.055,.065),(.043,.05),(.06,.055)],collect=True)
 loft('Front paw',[(.61,y,.065),(.7,y,.075),(.8,y,.062),(.86,y,.04)],[(.067,.06),(.095,.07),(.09,.045),(.07,.025)],collect=True)
 loft('Hind haunch', [(-.65,y,1.10),(-.60,y,.92),(-.42,y,.70),(-.69,y,.44),(-.78,y,.30),(-.72,y,.10)],[(.16,.18),(.15,.19),(.10,.12),(.06,.065),(.05,.055),(.045,.052)],collect=True)
 loft('Rear paw',[(-.76,y,.065),(-.68,y,.07),(-.56,y,.055),(-.50,y,.035)],[(.055,.05),(.085,.07),(.08,.045),(.06,.025)],collect=True)
 loft('Alert ear',[(.91,s*.13,2.09),(.90,s*.15,2.21),(.96,s*.155,2.38)],[(.085,.11),(.059,.07),(.005,.008)],collect=True)
 # Small connected tufts at limb roots, not giant detached spikes.
 for k in range(3):
  loft('Neck ruff root',[(.64,s*(.13+k*.04),1.68-k*.09),(.38-k*.06,s*(.23+k*.018),1.54-k*.09),(.17-k*.085,s*(.24+k*.02),1.48-k*.10)],[(.072,.10),(.06,.072),(.003,.005)],collect=True)
loft('Plume tail',[(-.77,0,1.16),(-1.01,0,1.17),(-1.18,0,1.27),(-1.30,0,1.44),(-1.27,0,1.59),(-1.16,0,1.68)],[(.08,.10),(.11,.16),(.12,.19),(.095,.15),(.05,.09),(.002,.003)],collect=True)
# Fuse only the anatomy, retaining a coherent sculpt rather than primitive seams.
bpy.ops.object.select_all(action='DESELECT')
for o in parts:o.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();body=bpy.context.object;body.name='Divine wolf continuous coat'
r=body.modifiers.new('Continuous anatomical skin','REMESH');r.mode='VOXEL';r.voxel_size=.023;bpy.ops.object.modifier_apply(modifier=r.name)
s=body.modifiers.new('Sculpt smoothing','SMOOTH');s.factor=.55;s.iterations=5;bpy.ops.object.modifier_apply(modifier=s.name)
sub=body.modifiers.new('Soft ink surface','SUBSURF');sub.levels=1;bpy.ops.object.modifier_apply(modifier=sub.name)
body.data.materials.clear();body.data.materials.append(ivory)
for p in body.data.polygons:p.use_smooth=True
bvh=BVHTree.FromObject(body,bpy.context.evaluated_depsgraph_get())

def paint(name,xz,side=-1,material=red,width=.015):
 dense=[]
 for a,b in zip(xz,xz[1:]):
  steps=max(2,int(math.hypot(b[0]-a[0],b[1]-a[1])/.008))
  dense.extend([(a[0]+(b[0]-a[0])*k/steps,a[1]+(b[1]-a[1])*k/steps) for k in range(steps)])
 dense.append(xz[-1]);xz=dense
 verts=[]
 for i,(x,z) in enumerate(xz):
  prev=Vector(xz[max(0,i-1)]);next=Vector(xz[min(len(xz)-1,i+1)]);t=(next-prev).normalized();n=Vector((-t.y,t.x));w=width*(.25+.75*min(1,i/3,(len(xz)-1-i)/3));edge=[]
  for sign in [-1,1]:
   xx=x+n.x*w*sign;zz=z+n.y*w*sign;hit,normal,_,_=bvh.ray_cast(Vector((xx,side*2.5,zz)),Vector((0,-side,0)),5)
   if hit:edge.append(hit+normal*.004)
  if len(edge)==2:verts.extend(edge)
 if len(verts)<4:return
 faces=[(i,i+1,i+3,i+2) for i in range(0,len(verts)-2,2)];me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.update();o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);me.materials.append(material);o['paint_surface']=True
 for p in me.polygons:p.use_smooth=True
 return o

for side in [-1,1]:
 # Chest spiral is painted along the actual 3D surface.
 spiral=[]
 for i in range(75):
  a=i/74*math.tau*1.65;r=.02+.16*i/74;spiral.append((.42+r*math.cos(a),1.29+r*math.sin(a)))
 paint('Curved vermilion shoulder spiral',spiral,side,width=.017)
 paint('Long flowing flank paint',[(-.70,1.20),(-.50,1.26),(-.32,1.31),(-.07,1.31),(.12,1.42),(.32,1.56)],side,width=.018)
 paint('Lower flank brush stroke',[(-.60,1.16),(-.43,1.19),(-.19,1.20),(.05,1.28),(.20,1.38)],side,width=.010)
 paint('Forehead markings',[(.91,2.10),(1.01,2.05),(1.10,2.00),(1.17,1.97)],side,width=.018)
 paint('Face flame marking',[(.99,2.10),(1.10,2.06),(1.19,2.00),(1.23,1.96)],side,width=.012)
 paint('Painted cheek curl',[(1.04,1.97),(1.06,1.91),(1.15,1.88),(1.20,1.92)],side,width=.010)
 for x,z in [(.61,.28),(-.72,.20)]:
  paint('Ankle vermilion flourish',[(x-.03,z+.11),(x+.025,z+.065),(x-.01,z+.02),(x+.045,z)],side,width=.012)
 # Dark elegant eye, amber iris and expressive brow are inset against the head.
 for name,loc,scale,material in [('Inked eye',(1.17,side*.142,1.968),(.061,.012,.023),ink),('Amber eye',(1.18,side*.153,1.969),(.022,.007,.015),gold),('Eye pupil',(1.183,side*.158,1.969),(.007,.005,.013),ink)]:
  bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=loc);o=bpy.context.object;o.name=name;o.scale=scale;o.data.materials.append(material)
 curve('Expressive ink brow',[(1.10,side*.155,2.004),(1.16,side*.16,2.017),(1.215,side*.132,2.00)],ink,.009)
 curve('Mouth line',[(1.20,side*.101,1.80),(1.38,side*.075,1.787),(1.51,side*.043,1.797)],ink,.007)
 loft('Inner ear',[(.912,side*.162,2.17),(.945,side*.17,2.31)],[(.038,.04),(.002,.004)],pink,10)
 for pawx in [.74,-.60]:
  for yy in [-.031,.028]:
   pts=[]
   for k in range(8):
    x=pawx+.068*k/7;y=side*.22+yy;hit,normal,_,_=bvh.ray_cast(Vector((x,y,.30)),Vector((0,0,-1)),.4)
    if hit:pts.append(hit+normal*.003)
   if len(pts)>1:curve('Paw toe ink',pts,ink,.004)
 paint('Inner ear pigment',[(.90,2.17),(.92,2.235),(.953,2.32)],side,material=pink,width=.022)
bpy.ops.mesh.primitive_uv_sphere_add(segments=24,ring_count=12,location=(1.56,0,1.829));nose=bpy.context.object;nose.name='Inked nose';nose.scale=(.047,.057,.042);nose.data.materials.append(ink)

# Sculpted curled fur ornaments: volumetric ivory ribbons with inked ridges.
def ribbon(name,pts,widths,material=ivory,depth=.028):
 pts=[Vector(p) for p in pts];verts=[];faces=[]
 for i,p in enumerate(pts):
  tan=(pts[min(i+1,len(pts)-1)]-pts[max(0,i-1)]).normalized();across=Vector((-tan.z,0,tan.x)).normalized()
  for j in range(8):
   a=j*math.tau/8;verts.append(p+across*(math.cos(a)*widths[i])+Vector((0,1,0))*(math.sin(a)*depth*min(1,widths[i]/.04)))
 for i in range(len(pts)-1):
  for j in range(8):faces.append((i*8+j,i*8+(j+1)%8,(i+1)*8+(j+1)%8,(i+1)*8+j))
 faces.extend([tuple(range(7,-1,-1)),tuple((len(pts)-1)*8+j for j in range(8))]);me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);o=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(o);o.data.materials.append(material)
 for p in me.polygons:p.use_smooth=True
 sub=o.modifiers.new('Silky sculpted tuft','SUBSURF');sub.levels=2
 return o
for side in [-1,1]:
 for i in range(7):
  y=side*.16;raw=[(.99-i*.035,y,2.10-i*.065),(.80-i*.033,y,2.06-i*.066),(.63-i*.045,y,2.01-i*.072)];pts=[]
  for x,yy,z in raw:
   hit,normal,_,_=bvh.ray_cast(Vector((x,side*2.5,z)),Vector((0,-side,0)),5)
   pts.append((x,hit.y+side*.013 if hit else yy,z))
  ribbon('Head flowing fur',pts,[.045,.032,.002],ivory,.014)
  curve('Head fur ink ridge',[(x,y+side*.016,z) for x,y,z in pts],ink,.004)
 # Curled shoulder feather grows outward/back from the actual ruff.
 for i in range(3):
  y=side*(.23+i*.025);pts=[(.54-i*.10,y,1.56-i*.12),(.34-i*.11,y*1.18,1.66-i*.08),(.14-i*.12,y*1.2,1.61-i*.065),(.14-i*.14,y*1.18,1.47-i*.07),(.27-i*.12,y*1.2,1.45-i*.07),(.31-i*.13,y*1.2,1.55-i*.06),(.22-i*.13,y*1.2,1.56-i*.06)]
  ribbon('Shoulder spiral feather',pts,[.09,.095,.08,.064,.052,.035,.003],ivory,.022)
  curve('Ink on curled shoulder fur',[(x,y+side*.026,z) for x,y,z in pts],ink,.005)
 for i in range(4):
  pts=[(.60-i*.08,side*.23,1.66-i*.10),(.29-i*.10,side*.28,1.66-i*.10),(.03-i*.12,side*.29,1.70-i*.10),(-.14-i*.10,side*.26,1.79-i*.12)]
  ribbon('Layered swept neck fur',pts,[.10,.095,.058,.002],ivory,.023)
  curve('Neck feather ridge',[(x,y+side*.025,z) for x,y,z in pts],ink,.004)
 # Hip and ankle curls carry the same engraved ornamental language.
 for cx,cz,cy,r in [(-.65,1.21,side*.24,.105),(.59,.20,side*.24,.050),(-.73,.24,side*.235,.055),(-1.10,1.39,side*.11,.075)]:
  pts=[];widths=[]
  for k in range(30):
   a=k/29*math.tau*1.3;rr=r*(1-k/34);pts.append((cx+rr*math.cos(a),cy,cz+rr*math.sin(a)));widths.append(.035*(1-k/31))
  ribbon('Ivory ornamental curl',pts,widths,ivory,.016);curve('Fine curl ink',[(x,y+side*.019,z) for x,y,z in pts],ink,.004)
# Tail plume feather leaves follow the main tail, fully dimensional.
for i in range(4):
 pts=[(-.92-i*.06,0,1.19+i*.045),(-1.15-i*.025,-.018,1.24+i*.075),(-1.37-i*.016,0,1.47+i*.055),(-1.19+i*.035,0,1.70-i*.015)]
 pts=[(x,-.095+i*.063,z) for x,y,z in pts]
 ribbon('Tail flowing feather',pts,[.08,.075,.06,.002],ivory,.04);curve('Tail plume ink ridge',[(x,y-.045,z) for x,y,z in pts],ink,.004)

# A real tilted jade disc, etched spirals and sculpted flame ribbons.
disc_center=Vector((.02,0,1.66));tilt=-.16
bpy.ops.mesh.primitive_cylinder_add(vertices=80,radius=.43,depth=.075,location=disc_center);disc=bpy.context.object;disc.name='Turquoise divine mirror';disc.rotation_euler.y=tilt;disc.data.materials.append(green);bev=disc.modifiers.new('Carved mirror bevel','BEVEL');bev.width=.022;bev.segments=3
bpy.ops.mesh.primitive_torus_add(major_radius=.41,minor_radius=.023,major_segments=80,minor_segments=12,location=disc_center+Vector((0,0,.045)));rim=bpy.context.object;rim.name='Raised jade mirror rim';rim.rotation_euler.y=tilt;rim.data.materials.append(jade)
for radius in [.28,.35]:
 curve('Circular mirror engraving',[(disc_center.x+radius*math.cos(k*math.tau/90),radius*math.sin(k*math.tau/90),1.71-radius*math.cos(k*math.tau/90)*math.sin(tilt)) for k in range(91)],jade,.005)
curve('Mirror central spiral',[(.02+.15*(k/79)*math.cos(k/79*math.tau*1.8),.15*(k/79)*math.sin(k/79*math.tau*1.8),1.713) for k in range(80)],jade,.008)
for i in range(5):
 y=(i-2)*.15;z=1.73+abs(i-2)*.035;length=[.88,1.17,1.40,1.14,.97][i];rise=[.44,.65,.88,.70,.49][i];pts=[(-.25,y,z),(-.51,y,z+.05),(-.72,y+.05,z+.17),(-length,y-.03,z+rise*.48),(-length-.12,y+.02,z+rise*.72),(-length+.10,y+.02,z+rise*.88),(-length+.025,y-.02,z+rise)]
 ribbon('Sculpted flame tongue',pts,[.105,.12,.10,.10,.07,.045,.002],orange,.035)
 ribbon('Flame golden heart',[(x,y-.038,z+.015) for x,y,z in pts],[.04,.05,.045,.033,.024,.01,.002],yellow,.009)
# Model-only export, prior to adding the presentation environment.
model_objects=list(bpy.context.scene.objects)
bpy.ops.object.select_all(action='DESELECT')
for o in model_objects:o.select_set(True)
bpy.context.view_layer.objects.active=body
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'wolf-static.blend'))
# glTF exporter exports evaluated meshes; curves are explicitly converted in a copy scene.
for o in model_objects:
 if o.type=='CURVE':
  bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=os.path.join(ROOT,'wolf-static.glb'),use_selection=True,export_apply=True)

floor=mat('Washi stage',(.88,.84,.73));bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.012));bpy.context.object.data.materials.append(floor)
def area(name,loc,power,size):
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
area('Broad soft key',(3,-4,6),350,5);area('Warm fill',(-3,1,4),100,4);area('Ink rim light',(1,4,5),220,3)
bpy.ops.object.camera_add(location=(4.7,-7.5,3.3));cam=bpy.context.object;cam.rotation_euler=(Vector((-.05,0,1.14))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4.2;scene.camera=cam
scene.render.use_freestyle=True
lines=scene.view_layers[0].freestyle_settings.linesets[0].linestyle;lines.color=(.045,.035,.025);lines.thickness=1.7
contours=bpy.data.collections.new('Ink contour geometry');scene.collection.children.link(contours)
for o in model_objects:
 if not o.get('paint_surface'):contours.objects.link(o)
lineset=scene.view_layers[0].freestyle_settings.linesets[0];lineset.select_by_collection=True;lineset.collection=contours;lineset.collection_negation='INCLUSIVE'
scene.render.filepath=os.path.join(ROOT,'wolf-three-quarter.png');bpy.ops.render.render(write_still=True)
cam.location=(2.2,-8,2.9);cam.rotation_euler=(Vector((-.05,0,1.14))-cam.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=os.path.join(ROOT,'wolf-profile.png');bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(ROOT,'wolf-preview-scene.blend'))
print('STATIC_3D_STUDY_COMPLETE')

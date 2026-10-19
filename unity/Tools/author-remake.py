"""Author static world/NPC meshes. Then run check-remake-fbx.py -- --write-bindings
to record the actual exported material-section order before Unity packaging.
Never touches Amaterasu.
"""
import bpy,math,random,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.noise import noise_vector
R=Path(__file__).resolve().parents[1];OUT=R/'Assets/Sunward/Models/Remake';OUT.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True);random.seed(6821);s=bpy.context.scene
mats={}
for name in ['Oak','Bark','Plaster','Roof','Stone','Earth','Meadow','Indigo','Vermilion','Jade','Paper','Skin']:
 m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Roughness'].default_value=.83
 tex=m.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(R/'Assets/Sunward/Textures/Remake'/f'{name}.png'));m.node_tree.links.new(tex.outputs['Color'],p.inputs['Base Color']);mats[name]=m
for name,color in {'Ink':(.06,.065,.06,1),'Bronze':(.33,.28,.13,1),'Cream':(.90,.85,.69,1),'Hair':(.095,.085,.07,1),'White':(.9,.89,.81,1),'Iris':(.19,.16,.10,1),'Glow':(1,.69,.24,1),'Pink':(.95,.60,.63,1),'Leaf':(.25,.44,.23,1)}.items():
 m=bpy.data.materials.new(name);m.diffuse_color=color;m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=color;p.inputs['Roughness'].default_value=.75
 if name=='Bronze':p.inputs['Metallic'].default_value=.45
 mats[name]=m
assets=[];parts=[];asset_name='';manifest=[]
def use(obj,mat):
 obj.data.materials.append(mats[mat]);parts.append(obj);return obj
def cube(p,scale,mat='Oak',bevel=.025):
 bpy.ops.mesh.primitive_cube_add(size=1,location=p);o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  m=o.modifiers.new('Hand eased edges','BEVEL');m.width=bevel;m.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name)
 return use(o,mat)
def sphere(p,scale,mat='Stone',segments=16):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=max(8,segments//2),radius=1,location=p);o=bpy.context.object;o.scale=scale;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 for f in o.data.polygons:f.use_smooth=True
 return use(o,mat)
def cylinder(a,b,r,mat='Oak',vertices=12,r2=None):
 a,b=Vector(a),Vector(b);d=b-a;bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=r,radius2=r if r2 is None else r2,depth=d.length,location=(a+b)*.5);o=bpy.context.object;o.rotation_euler=d.to_track_quat('Z','Y').to_euler();return use(o,mat)
def curve(points,r=.02,mat='Ink',resolution=2):
 c=bpy.data.curves.new('Carved flowing line','CURVE');c.dimensions='3D';c.bevel_depth=r;c.bevel_resolution=resolution;sp=c.splines.new('BEZIER');sp.bezier_points.add(len(points)-1)
 for p,co in zip(sp.bezier_points,points):p.co=co;p.handle_left_type=p.handle_right_type='AUTO'
 o=bpy.data.objects.new('Sweep',c);s.collection.objects.link(o);bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');return use(bpy.context.object,mat)
def lathe(profile,p=(0,0,0),mat='Stone',n=24):
 v=[];f=[]
 for r,z in profile:
  for i in range(n):a=i/n*math.tau;v.append((p[0]+r*math.cos(a),p[1]+r*math.sin(a),p[2]+z))
 for j in range(len(profile)-1):
  for i in range(n):a=j*n+i;b=j*n+(i+1)%n;c=a+n;d=b+n;f.append((a,b,d,c))
 f+=[tuple(reversed(range(n))),tuple((len(profile)-1)*n+i for i in range(n))]
 mesh=bpy.data.meshes.new('Turned vessel');mesh.from_pydata(v,[],f);mesh.update();o=bpy.data.objects.new('Turned vessel',mesh);s.collection.objects.link(o)
 for face in mesh.polygons:face.use_smooth=True
 return use(o,mat)
def begin(name):
 global parts,asset_name;parts=[];asset_name=name;bpy.ops.object.select_all(action='DESELECT')
def finish():
 global parts
 bpy.ops.object.select_all(action='DESELECT')
 for o in parts:o.select_set(True)
 bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object;o.name=asset_name+'_Mesh';bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
 # Put origin at the asset's ground datum, not the last selected part.
 s.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
 if not o.data.uv_layers:
  bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
 parent=bpy.data.objects.new(asset_name,None);s.collection.objects.link(parent);o.parent=parent
 front=bpy.data.objects.new(asset_name+'_Facing',None);s.collection.objects.link(front);front.parent=parent;front.location=(0,-1,0)
 assets.append(parent);manifest.append({'name':asset_name,'mesh':o.name,'materials':[m.name for m in o.data.materials],'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'front':front.name});return parent

def roof(width,depth,height,mat='Roof'):
 # Continuous curved roof backing under individual kawara tiles.
 verts=[];faces=[]
 for side in [-1,1]:
  start=len(verts)
  for row in range(9):
   t=row/8;y=side*(t*(depth/2+.55));z=height+.85*(1-t)**1.2+.16*t*t
   for x in [-width/2-.55,width/2+.55]:verts.append((x,y,z-.025))
  for row in range(8):
   a=start+row*2;face=(a,a+1,a+3,a+2);faces.append(face if side<0 else tuple(reversed(face)))
 me=bpy.data.meshes.new('Curved roof continuous underlay');me.from_pydata(verts,[],faces);o=bpy.data.objects.new('Closed roof sheathing',me);s.collection.objects.link(o);use(o,mat)
 sol=o.modifiers.new('Eave thickness','SOLIDIFY');sol.thickness=.09;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=sol.name)
 # Individual half-round kawara tiles on the continuous curved roof.
 for side in [-1,1]:
  for row in range(7):
   t=row/6;y=side*(.15+t*(depth/2+.42));z=height+.85*(1-t)**1.2+.16*t*t
   for col in range(16):
    x=-width/2-.35+col*(width+.7)/15
    slope=side*(-1.02*max(.001,1-t)**.2+.32*t)/(depth/2+.42)
    o=cylinder((x,y-.29,z-.29*slope),(x,y+.29,z+.29*slope),.07,mat,8)
  for k in range(3):
   y=side*(depth/2+.38);curve([(-width/2-.48,y,height+.15+k*.06),(0,y,height-.02+k*.06),(width/2+.48,y,height+.15+k*.06)],.055,mat)
 cylinder((-width/2-.45,0,height+.92),(width/2+.45,0,height+.92),.13,mat,12)
 for side in [-1,1]:curve([(side*width/2,0,height+.91),(side*(width/2+.4),0,height+1.03),(side*(width/2+.48),0,height+1.22)],.065,mat)
def house(name,variant):
 begin(name);w,d=6,5
 cube((0,0,.18),(6.2,5.2,.36),'Stone',.09);cube((0,0,1.72),(5.7,4.7,2.8),'Plaster',.04)
 for x in [-2.85,-1.45,0,1.45,2.85]:
  for y in [-2.4,2.4]:cube((x,y,1.76),(.15,.17,3.1),'Oak',.02)
 for y in [-2.45,2.45]:
  for z in [.42,1.4,2.95]:cube((0,y,z),(5.9,.17,.13),'Oak',.025)
 for sign in [-1,1]:
  # Recessed shoji windows with real lattice depth.
  x=sign*1.9;cube((x,-2.43,1.8),(1.15,.06,1.25),'Paper',.015)
  for i in range(5):cube((x-.55+i*.275,-2.49,1.8),(.025,.04,1.28),'Oak',.005)
  for z in [1.2,1.6,2,2.4]:cube((x,-2.50,z),(1.16,.04,.025),'Oak',.004)
 cube((0,-2.46,1.48),(1.15,.09,2.12),'Indigo'if variant else'Vermilion',.02)
 for sign in [-1,1]:cube((sign*.6,-2.54,1.5),(.11,.13,2.25),'Oak',.018)
 cube((0,-2.82,.25),(1.65,.72,.22),'Stone',.05);cube((0,-3.02,.12),(2.1,.42,.18),'Stone',.04)
 for side in [-1,1]:
  curve([(side*2.8,-2.4,2.35),(side*2.5,-2.4,2.85),(side*2.05,-2.4,3.0)],.065,'Oak')
 roof(6,5,3.2)
 # Ridge vents and end-cap finials distinguish the two silhouettes.
 if variant:
  cube((0,0,4.15),(1.8,1.1,.45),'Plaster',.04);roof(1.7,1.1,4.35,'Roof')
 for side in [-1,1]:
  for x in [side*2.5]:cylinder((x,-2.62,2.7),(x,-2.62,2.95),.018,'Bronze');lathe([(.07,-.2),(.16,-.12),(.18,.02),(.13,.17),(.07,.2)],(x,-2.62,2.5),'Paper',16)
 finish()
house('House_A',False);house('House_B',True)

def leaf(center,direction,size,mat):
 c=Vector(center);axis=Vector(direction).normalized();side=axis.cross(Vector((0,0,1)))
 if side.length<.01:side=Vector((1,0,0))
 side.normalize();p=[c,c+axis*size*.5+side*size*.23+Vector((0,0,size*.08)),c+axis*size,c+axis*size*.5-side*size*.23+Vector((0,0,size*.08))]
 mesh=bpy.data.meshes.new('Curved leaf');mesh.from_pydata(p,[],[(0,1,2),(0,2,3),(2,1,0),(3,2,0)]);mesh.uv_layers.new();o=bpy.data.objects.new('Botanical leaf',mesh);s.collection.objects.link(o);use(o,mat)
def tree(name,kind,seed):
 random.seed(seed);begin(name)
 curve([(0,0,0),(.12,-.02,1.4),(-.07,.08,2.7),(.18,0,4.4)],.17,'Bark',2)
 for r in range(5):
  a=r*2.4;cylinder((0,0,.14),(math.sin(a)*.60,math.cos(a)*.60,.01),.10,'Bark',10,r2=.025)
 count=8 if kind!='pine'else 12
 for branch in range(count):
  a=branch*2.4;z=2+branch*.24;reach=1.6 if kind!='pine'else max(.45,2.1-branch*.12)
  tip=Vector((math.sin(a)*reach,math.cos(a)*reach,z+.55));curve([(0,0,z-.5),(tip.x*.55,tip.y*.55,z+.1),tip],.055,'Bark',2)
  for twig in range(6):
   u=twig/5;point=tip+Vector((math.sin(a+u*2)*.55,math.cos(a+u*2)*.55,u*.35));cylinder(tip,point,.018,'Bark',8,r2=.006)
   for k in range(24 if kind=='cherry'else 36):
    r=random.random()**.5*.58;b=random.random()*math.tau;c=point+Vector((math.cos(b)*r,math.sin(b)*r,random.uniform(-.14,.26)))
    if kind=='cherry':
     for petal in range(5):
      angle=petal*math.tau/5;leaf(c,(math.cos(angle),math.sin(angle),.2),.17,'Pink'if (branch+k)%3 else'Cream')
    else:leaf(c,(math.cos(b),math.sin(b),random.uniform(.1,.7)),.40 if kind=='maple'else .34,'Leaf'if k%3 else'Meadow')
 finish()
for name,kind,seed in [('Cherry_A','cherry',11),('Cherry_B','cherry',71),('Maple_A','maple',31),('Pine_A','pine',51)]:tree(name,kind,seed)
# Shared bent-blade and wildflower patches, not grass-shaped boxes.
for flowers in [False,True]:
 begin('Flower_Patch' if flowers else 'Grass_Patch')
 random.seed(412 if flowers else 812)
 for k in range(24 if flowers else 130):
  x=random.uniform(-.6,.6);y=random.uniform(-.6,.6);h=random.uniform(.14,.46);a=random.uniform(0,math.tau)
  if flowers:
   top=(x+.035,y,h);cylinder((x,y,0),top,.008,'Leaf',6)
   for petal in range(5):
    angle=petal*math.tau/5;leaf(top,(math.cos(angle),math.sin(angle),.4),.08,'Pink'if k%3 else'Cream')
  else:
   dx,dy=math.cos(a),math.sin(a);side=Vector((-dy,dx,0))*.022
   v=[]
   for row in range(4):
    u=row/3;c=Vector((x+dx*.17*u*u,y+dy*.17*u*u,h*u));width=side*(1-u*.96)
    v.extend([c-width,c+width])
   me=bpy.data.meshes.new('Swept grass blade');me.from_pydata(v,[],[(q,q+1,q+3,q+2)for q in range(0,6,2)]);o=bpy.data.objects.new('Bent blade',me);s.collection.objects.link(o);use(o,'Meadow'if k%3 else'Leaf')
 finish()
for i in range(4):
 begin('Rock_'+str(i));bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=3,radius=1);o=bpy.context.object
 for v in o.data.vertices:
  n=noise_vector(v.co*2.3+Vector((i*3,.4,1)));v.co+=n*.19;v.co.z=max(-.62,v.co.z);v.co.x*=1.05+i*.08;v.co.y*=.78+(i%2)*.14;v.co.z*=.77
 # Keep real facets, with small rounded edges for convincing grazing highlights.
 use(o,'Stone');bevel=o.modifiers.new('Eroded edges','BEVEL');bevel.width=.035;bevel.segments=2;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=bevel.name)
 finish()

def pot(p,scale,mat='Jade'):
 return lathe([(0,0),(.16*scale,0),(.22*scale,.18*scale),(.20*scale,.34*scale),(.11*scale,.42*scale),(.13*scale,.45*scale),(.10*scale,.45*scale),(.08*scale,.40*scale),(.14*scale,.20*scale),(0,.08*scale)],p,mat)
def market(name,kind):
 begin(name);fabric=['Vermilion','Jade','Indigo','Paper'][kind]
 for x in [-1.5,1.5]:
  for y in [-.75,.75]:cube((x,y,1.42),(.13,.13,2.84),'Oak',.024)
 for y in [-.75,.75]:cube((0,y,2.7),(3.2,.15,.18),'Oak',.025)
 for x in [-1.5,1.5]:
  for y in [-.75,.75]:cylinder((x,y,2.1),(x*.65,y,2.7),.042,'Oak',8)
 cube((0,0,.48),(2.95,1.40,.85),'Oak',.055)
 for i in range(9):cube((-1.31+i*.328,0,.94),(.31,1.56,.08),'Oak',.018)
 # Real folded, thick fabric roof with scalloped valance.
 verts=[];faces=[];nx,ny=30,14
 for j in range(ny+1):
  for i in range(nx+1):
   u=i/nx;t=j/ny;verts.append(((u-.5)*3.6,(t-.5)*2.3,2.78+.28*math.sin(t*math.pi)-.08*math.sin(u*math.pi)+.02*math.sin(u*40)))
   if i<nx and j<ny:k=j*(nx+1)+i;faces.append((k,k+1,k+nx+2,k+nx+1))
 me=bpy.data.meshes.new('Tensioned fabric');me.from_pydata(verts,[],faces);o=bpy.data.objects.new('Woven awning',me);s.collection.objects.link(o);use(o,fabric);m=o.modifiers.new('Cloth thickness','SOLIDIFY');m.thickness=.025;bpy.context.view_layer.objects.active=o;bpy.ops.object.modifier_apply(modifier=m.name)
 for i in range(7):cube((-1.5+i*.5,-1.15,2.63),(.47,.025,.3),fabric,.035)
 for x in [-1.2,1.2]:
  cylinder((x,-.8,2.7),(x,-.8,2.36),.015,'Bronze');lathe([(.08,-.22),(.18,-.14),(.20,.03),(.14,.22),(.07,.24)],(x,-.8,2.12),'Paper',16)
 cube((0,.55,1.43),(2.6,.38,.09),'Oak',.018)
 for row in range(2):
  for k in range(5):
   x=-1.13+k*.55;y=-.30+row*.50
   if kind==0:
    cube((x,y,1.02),(.49,.43,.08),'Oak',.016)
    for a in range(3):sphere((x-.13+a*.13,y,1.15),(.10,.09,.10),'Vermilion'if k%2 else'Cream',12)
   elif kind==1:pot((x,y,.98),.9,'Jade'if k%2 else'Plaster')
   elif kind==2:
    pot((x,y,.98),.75,'Plaster')
    for f in range(3):
     a=f*2.4;top=(x+math.sin(a)*.10,y+math.cos(a)*.10,1.65+f*.045);cylinder((x,y,1.2),top,.008,'Leaf',6)
     for p in range(5):aa=p*math.tau/5;leaf(top,(math.cos(aa),math.sin(aa),.1),.095,'Pink'if k%2 else'Cream')
   else:
    roll=cylinder((x-.19,y,1.13),(x+.19,y,1.13),.11,['Indigo','Vermilion','Jade'][k%3],16)
    for end in [-1,1]:sphere((x+end*.195,y,1.13),(.012,.095,.095),'Paper',12)
 # Rear stock shelf and attached patterned sign.
 for k in range(4):pot((-1+k*.65,.56,1.49),.75,'Jade'if kind%2 else'Paper')
 cube((0,-1.18,2.20),(1.0,.07,.38),'Oak',.025);cube((0,-1.225,2.2),(.83,.012,.26),fabric,.008)
 finish()
for i,n in enumerate(['Market_Produce','Market_Ceramics','Market_Flowers','Market_Textiles']):market(n,i)

def resident(name,garment,role):
 begin(name)
 # Layered kimono with actual folds, split lower panels and obi depth.
 sphere((0,0,1.15),(.27,.16,.42),garment,24)
 for side in [-1,1]:
  sphere((side*.145,0,.48),(.17,.15,.40),garment,20)
  sphere((side*.145,-.07,.065),(.11,.21,.065),'Ink',16)
  arm=cylinder((side*.24,0,1.45),(side*.47,-.025,1.10),.115,garment,16,r2=.15)
  sphere((side*.45,-.04,.97),(.065,.07,.12),'Skin',16)
  for finger in range(4):cylinder((side*(.42+finger*.018),-.065,.98),(side*(.42+finger*.018),-.082,.88),.012,'Skin',8,r2=.010)
 for z in [1.03,1.12]:lathe([(.275,z),(.28,z+.065)],(0,0,0),'Indigo'if garment!='Indigo'else'Vermilion',24)
 # Fold ribbons break up the generic cylinder silhouette.
 for side in [-1,1]:
  curve([(side*.20,-.14,1.48),(side*.05,-.18,1.17),(side*.08,-.16,.91)],.012,'Cream')
  for k in range(3):curve([(side*(.06+k*.05),-.13,.9),(side*(.09+k*.05),-.155,.60),(side*(.10+k*.05),-.14,.20)],.009,'Oak')
 cylinder((0,0,1.48),(0,0,1.70),.072,'Skin',16)
 sphere((0,0,1.87),(.16,.14,.215),'Skin',32)
 for side in [-1,1]:
  sphere((side*.16,.005,1.87),(.035,.03,.06),'Skin',16)
  sphere((side*.065,-.137,1.91),(.042,.014,.018),'White',20)
  sphere((side*.065,-.150,1.909),(.013,.008,.014),'Iris',16)
  sphere((side*.061,-.158,1.914),(.004,.003,.004),'White',12)
  curve([(side*.105,-.134,1.94),(side*.064,-.148,1.948),(side*.027,-.136,1.94)],.006,'Hair')
 sphere((0,-.157,1.86),(.024,.038,.045),'Skin',16)
 curve([(-.043,-.137,1.80),(0,-.146,1.794),(.043,-.137,1.80)],.004,'Oak')
 sphere((0,.018,2.01),(.165,.145,.115),'Hair',24)
 if role==2:
  sphere((0,.13,1.99),(.105,.11,.10),'Hair',20)
 else:
  for side in [-1,1]:sphere((side*.142,.02,1.91),(.025,.11,.10),'Hair',16)
 if role==1:
  # Soft tied headcloth and knot.
  lathe([(.16,2.00),(.17,2.07),(.12,2.10)],(0,0,0),'Paper',24);sphere((.15,.05,2.04),(.055,.04,.05),'Paper',16)
 finish()
resident('Resident_Artisan','Vermilion',0);resident('Resident_Merchant','Jade',1);resident('Resident_Pilgrim','Indigo',2)
# Export all assets at their origin, independent of diagnostic stage positions.
bpy.ops.object.select_all(action='DESELECT')
for root in assets:
 root.select_set(True)
 for o in root.children:o.select_set(True)
path=OUT/'WindflowerRemake.fbx';bpy.ops.export_scene.fbx(filepath=str(path),use_selection=True,object_types={'EMPTY','MESH'},add_leaf_bones=False,bake_anim=False,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',path_mode='STRIP')
report={'origin':'Original Blender-authored static assets for Windflower, no outside meshes','fbx_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'assets':manifest,'materials':[{ 'name':n,'texture':n+'.png'if n in ['Oak','Bark','Plaster','Roof','Stone','Earth','Meadow','Indigo','Vermilion','Jade','Paper','Skin']else None,'color':list(m.diffuse_color)}for n,m in mats.items()]}
(R/'Review/remake-library.json').write_text(json.dumps(report,indent=2))
# Diagnostic render uses the actual exported mesh sources; not a Unity render.
for i,root in enumerate(assets):root.location=((i%5)*9,(i//5)*10,0)
s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=False;s.render.resolution_x=1600;s.render.resolution_y=1100;s.render.resolution_percentage=100
s.world=bpy.data.worlds.new('Paper studio');s.world.color=(.55,.56,.50)
bpy.ops.object.light_add(type='AREA',location=(0,-10,30));bpy.context.object.data.energy=14000;bpy.context.object.data.size=25
bpy.ops.object.camera_add(location=(47,-36,36));cam=bpy.context.object;cam.rotation_euler=(Vector((16,12,1.5))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=58;s.camera=cam
s.render.filepath=str(R/'Review/remake-library-diagnostic.png');bpy.ops.render.render(write_still=True)
print('Exported static library:',len(assets),'assets',sum(a['polygons']for a in manifest),'polygons',flush=True)

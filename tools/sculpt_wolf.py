"""Build a new connected anatomical coat, rebind to the attributed canine rig.
Runs inside adapt_wolf.py after the source import; source geometry is only a weight reference.
"""
from mathutils.kdtree import KDTree
reference=fox
kd=KDTree(len(reference.data.vertices))
for i,v in enumerate(reference.data.vertices):kd.insert(v.co,i)
kd.balance()
source_weights=[]
for v in reference.data.vertices:
 source_weights.append({reference.vertex_groups[g.group].name:g.weight for g in v.groups})
parts=[]
def loft(name,points,radii,steps=12):
 verts=[];faces=[]
 for i,p in enumerate(points):
  p=Vector(p);tangent=(Vector(points[min(i+1,len(points)-1)])-Vector(points[max(0,i-1)])).normalized()
  across=Vector((1,0,0))
  if abs(tangent.dot(across))>.85:across=Vector((0,1,0))
  across=(across-tangent*across.dot(tangent)).normalized();up=tangent.cross(across).normalized()
  for j in range(steps):
   a=j*math.tau/steps;verts.append(p+across*(math.cos(a)*radii[i][0])+up*(math.sin(a)*radii[i][1]))
 for i in range(len(points)-1):
  for j in range(steps):faces.append((i*steps+j,i*steps+(j+1)%steps,(i+1)*steps+(j+1)%steps,(i+1)*steps+j))
 faces.append(tuple(range(steps-1,-1,-1)));faces.append(tuple((len(points)-1)*steps+j for j in range(steps)))
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update()
 ob=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(ob);parts.append(ob);return ob
# Thorax, tucked abdomen and pelvis form one continuous shaped surface.
loft('Thorax',[(0,-30,54),(0,-22,52),(0,-10,50),(0,4,52),(0,18,51),(0,29,49),(0,35,50)],[(8,12),(13,19),(12,17),(8.5,9),(9.5,11),(12,15),(7,10)],16)
loft('Neck',[(0,-24,53),(0,-31,59),(0,-38,64),(0,-45,65)],[(11,15),(11,15),(9,12),(7.5,10)],14)
loft('Skull',[(0,-40,65),(0,-47,66),(0,-54,63),(0,-59,59)],[(7,9),(8.3,10),(6.5,7),(4.8,5)],14)
loft('Muzzle',[(0,-52,59),(0,-59,57),(0,-65,55.5),(0,-68,55.5)],[(5.2,5),(4.6,4),(3.5,2.7),(2.6,2.3)],12)
for s in [-1,1]:
 for dx in [-1.6,0,1.6]:
  loft('Fore toes',[(s*7+dx,-26,3),(s*7+dx,-30,2.5),(s*7+dx,-32,2.4)],[(1.5,1.8),(1.4,1.7),(.4,.8)],8)
  loft('Hind toes',[(s*7+dx,29,3),(s*7+dx,25,2.5),(s*7+dx,23,2.4)],[(1.5,1.8),(1.4,1.7),(.4,.8)],8)
 loft('Foreleg',[(s*8,-21,46),(s*8,-18,36),(s*7,-16,25),(s*7,-20,13),(s*7,-23,5),(s*7,-27,2.5)],[(4.5,5.5),(3.7,4),(2.7,2.8),(1.8,2),(2,2),(3.2,2.1)],10)
 loft('Hindleg',[(s*8,27,46),(s*9,24,38),(s*8,22,29),(s*7,34,17),(s*7,33,9),(s*7,29,3),(s*7,26,2)],[(5.5,7),(5,6),(3.2,3.6),(2,2.4),(1.7,1.8),(2.6,2),(3.2,1.8)],10)
 # Small canine ears are continuous with the skull, not giant fox triangles.
 loft('Ear',[(s*5.5,-44,72),(s*6,-43,76),(s*6.8,-43,81)],[(4,3),(2.7,1.8),(1.0,.8)],8)
 # A volumetric ruff emerges from the neck; feather tips are layered and tapered.
 for i in range(4):
  loft('Ruff',[(s*(6+i*.9),-34+i*3,61-i*2),(s*(12+i*.6),-27+i*4,58-i*2),(s*(14+i),-17+i*5,54-i*2)],[(3.7,4.2),(3,3),(.18,.2)],8)
loft('Tail',[(0,35,51),(0,44,45),(0,57,38),(1,72,33),(2,86,35),(2,96,39)],[(5,6),(5.8,6.5),(5.5,6),(4.5,5),(2.8,3),(.2,.2)],12)
# Fuse intersecting forms into a single continuous skin, then retain an intentional low-poly silhouette.
bpy.ops.object.select_all(action='DESELECT')
for ob in parts:ob.select_set(True)
bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();new=bpy.context.object
new.name='PaintedWolf'
remesh=new.modifiers.new('Connected anatomy','REMESH');remesh.mode='VOXEL';remesh.voxel_size=1.45;remesh.use_smooth_shade=True
bpy.ops.object.modifier_apply(modifier=remesh.name)
smooth=new.modifiers.new('Sculpt transitions','SMOOTH');smooth.factor=.6;smooth.iterations=3;bpy.ops.object.modifier_apply(modifier=smooth.name)
dec=new.modifiers.new('Painted planes','DECIMATE');dec.ratio=min(1,2200/len(new.data.polygons));bpy.ops.object.modifier_apply(modifier=dec.name)
for poly in new.data.polygons:poly.use_smooth=True
# Preserve UV topology for paint projection, using a fresh ivory image instead of the fox atlas.
bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=1.15,island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
image=bpy.data.images.new('IvoryCoat',width=64,height=64);image.generated_color=(1,.98,.93,1);image.pack()
mat=bpy.data.materials.new('Ivory skin');mat.use_nodes=True
tex=mat.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image
mat.node_tree.links.new(tex.outputs['Color'],mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color']);new.data.materials.clear();new.data.materials.append(mat)
for vg in reference.vertex_groups:new.vertex_groups.new(name=vg.name)
for v in new.data.vertices:
 weights={}
 for co,index,d in kd.find_n(v.co,4):
  w=1/(.5+d*d)
  for name,value in source_weights[index].items():weights[name]=weights.get(name,0)+value*w
 if v.co.y < -48: weights={'b_Head_05':1}
 elif v.co.y < -38:
  a=(-38-v.co.y)/10;a=a*a*(3-2*a)
  weights={name:value*(1-a) for name,value in weights.items()};weights['b_Head_05']=weights.get('b_Head_05',0)+sum(weights.values())*a/max(1e-6,1-a)
 total=sum(weights.values())
 for name,value in weights.items():
  if value/total>.01:new.vertex_groups[name].add([v.index],value/total,'REPLACE')
new.parent=rig;mod=new.modifiers.new('Canine deformation','ARMATURE');mod.object=rig
# Nose is a small bound surface with its own dark material, leaving approved eye geometry intact.
bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=6,location=(0,-68,55.5));nose=bpy.context.object;nose.name='WolfNose';nose.scale=(2.8,1.8,2.2)
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
vg=nose.vertex_groups.new(name='b_Head_05');vg.add(list(range(len(nose.data.vertices))),1,'REPLACE');nose.parent=rig
mod=nose.modifiers.new('Head deformation','ARMATURE');mod.object=rig
black=bpy.data.materials.new('Charcoal nose');black.diffuse_color=(.035,.028,.023,1);nose.data.materials.append(black)
bpy.data.objects.remove(reference,do_unlink=True);fox=new
print('NEW_ANATOMICAL_MESH',len(new.data.vertices),'vertices',len(new.data.polygons),'faces')

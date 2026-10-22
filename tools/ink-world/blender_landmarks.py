"""Blender-authored moving waterwheel and arched vermilion bridge ornaments.

Run from repository root:
  blender -b -t 4 -P tools/ink-world/blender_landmarks.py
Creates bevelled/merged native Unity meshes and a local authoring .blend.
No scene, material, collision, gameplay or animation files are modified.
"""
from pathlib import Path
import sys,math,json
import bpy,bmesh
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/village'))
import native
OUT=ROOT/'Sunward-Unity/Assets/Sunward/Generated/InkWorld'
LOCAL=Path('/workspace/work/ink-world');LOCAL.mkdir(parents=True,exist_ok=True)
WOOD=(.53,.33,.15);LIGHT=(.64,.43,.22);IRON=(.12,.13,.12)
RED=(.77,.16,.075);INK=(.10,.10,.075);GOLD=(.91,.64,.20);STONE=(.48,.47,.34)
parts={};rows=[]

def cv(p):return Vector((p[0],-p[2],p[1]))
def uc(p):return (p.x,p.z,-p.y)

def own(o,part,color):
 o.name=part+'-'+str(len(parts.setdefault(part,[])))
 o.color=(*color,1);parts[part].append(o)
 mat=bpy.data.materials.get(str(color))
 if mat is None:
  mat=bpy.data.materials.new(str(color));mat.diffuse_color=(*color,1);mat.use_nodes=True
  bs=mat.node_tree.nodes.get('Principled BSDF');bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Roughness'].default_value=.75
 o.data.materials.append(mat)
 return o

def bevel(o,width=.018,segments=1):
 if width<=0:return o
 mod=o.modifiers.new('Authored softened ink catching edges','BEVEL');mod.width=width;mod.segments=segments;mod.limit_method='ANGLE'
 return o

def box(part,center,size,col=WOOD,width=.015):
 bpy.ops.mesh.primitive_cube_add(size=1,location=cv(center));o=bpy.context.object
 o.scale=(size[0],size[2],size[1]);bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 own(o,part,col);bevel(o,width);return o

def beam(part,a,b,width,depth,col=WOOD):
 a,b=cv(a),cv(b);d=b-a
 bpy.ops.mesh.primitive_cube_add(size=1,location=(a+b)*.5);o=bpy.context.object
 o.scale=(width,depth,d.length);o.rotation_euler=d.to_track_quat('Z','Y').to_euler()
 bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 own(o,part,col);bevel(o,min(width,depth)*.08);return o

def solid(part,verts,faces,col=WOOD,edge=.01):
 me=bpy.data.meshes.new(part);me.from_pydata([cv(p) for p in verts],[],faces);me.update()
 o=bpy.data.objects.new(part,me);bpy.context.collection.objects.link(o);own(o,part,col)
 if edge:bevel(o,edge)
 return o

def cylinder(part,center,radius,depth,col=IRON,vertices=12,axis=(0,0,1)):
 bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=cv(center));o=bpy.context.object
 o.rotation_euler=cv(axis).to_track_quat('Z','Y').to_euler();own(o,part,col)
 if radius>.12:bevel(o,.008,1)
 return o

def sector(part,r0,r1,a0,a1,z,depth,col):
 vv=[];samples=4
 for zz in (z-depth/2,z+depth/2):
  for r in (r0,r1):
   for a in np.linspace(a0,a1,samples):vv.append((r*math.cos(a),r*math.sin(a),zz))
 n=samples;ff=[]
 # two annular faces, inside/outside walls, two endcaps.
 for j in range(n-1):
  ff.extend([(j,j+1,n+j+1,n+j),(2*n+j,3*n+j,3*n+j+1,2*n+j+1),
             (j,2*n+j,2*n+j+1,j+1),(n+j,n+j+1,3*n+j+1,3*n+j)])
 ff.extend([(0,n,3*n,2*n),(n-1,3*n-1,4*n-1,2*n-1)])
 return solid(part,vv,ff,col,.012)

def torus(part,center,major,minor,col=IRON):
 bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=5,location=cv(center),major_radius=major,minor_radius=minor)
 o=bpy.context.object;o.rotation_euler=cv((0,0,1)).to_track_quat('Z','Y').to_euler();own(o,part,col);return o

def curved_spoke(angle):
 vv=[];samples=7
 for t in np.linspace(0,1,samples):
  r=.28+1.61*t;a=angle+.14*math.sin(t*math.pi)+.12*t
  centre=np.array([math.cos(a)*r,math.sin(a)*r,0]);side=np.array([-math.sin(a),math.cos(a),0])
  w=.15*(1-t)+.075*t
  vv.extend([centre+side*w+(0,0,-.08),centre-side*w+(0,0,-.08),centre-side*w+(0,0,.08),centre+side*w+(0,0,.08)])
 ff=[(0,3,2,1)]
 for j in range(samples-1):
  for k in range(4):ff.append((j*4+k,j*4+(k+1)%4,(j+1)*4+(k+1)%4,(j+1)*4+k))
 ff.append(tuple((samples-1)*4+k for k in range(4)))
 solid('Mill-wheel-wood',vv,ff,LIGHT,.012)

def waterwheel():
 # All moving geometry shares one origin. The caller rotates BOTH parts together.
 for j in range(16):
  a=j*math.tau/16
  for z in (-.245,.245):
   sector('Mill-wheel-wood',1.82,2.02,a+.004,a+math.tau/16-.004,z,.12,WOOD if j%3 else LIGHT)
  # Radial paddle boards, cut from timber, with iron bolts on their two cheeks.
  o=box('Mill-wheel-wood',(math.cos(a)*2.02,math.sin(a)*2.02,0),(.15,.38,.64),LIGHT,.014)
  # Cube localX is radial and localY tangent in Unity XY plane.
  o.rotation_euler[1]=-a
  for z in (-.315,.315):
   cylinder('Mill-wheel-iron',(math.cos(a)*1.935,math.sin(a)*1.935,z),.025,.02,vertices=6)
 for j in range(10):curved_spoke(j*math.tau/10)
 cylinder('Mill-wheel-wood',(0,0,0),.36,.49,LIGHT,vertices=16)
 cylinder('Mill-wheel-iron',(0,0,0),.15,1.10,vertices=12)
 for z in (-.285,.285):
  torus('Mill-wheel-iron',(0,0,z),1.87,.021)
  torus('Mill-wheel-iron',(0,0,z),.34,.033)
  for j in range(10):
   a=j*math.tau/10
   cylinder('Mill-wheel-iron',(math.cos(a)*.26,math.sin(a)*.26,z),.024,.025,vertices=6)
 # Stationary frame: wheel axis at +2.0, supports either side of the wheel plane.
 for z in (-.61,.61):
  for x in (-.66,.66):
   beam('Mill-support-wood',(x,.13,z),(0,2.0,z),.18,.19,WOOD)
   box('Mill-support-stone',(x,.06,z),(.53,.16,.48),STONE,.05)
  beam('Mill-support-wood',(-.85,.33,z),(.85,.33,z),.15,.16,WOOD)
  box('Mill-support-wood',(0,1.93,z),(.58,.34,.30),LIGHT,.025)
  box('Mill-support-iron',(0,2.10,z),(.62,.055,.33),IRON,.009)
  cylinder('Mill-support-iron',(0,2.0,z),.19,.34,vertices=12)
 for x in (-.66,.66):beam('Mill-support-wood',(x,.30,-.77),(x,.30,.77),.16,.15,WOOD)


def arch(x):
 u=(x+4.85)/9.7
 return .10+.42*max(0,math.sin(math.pi*u))**1.5

def bridge():
 for z in (-1.18,1.18):
  # Continuous shaped rails with open space under each arm; no replacement deck.
  for height in (.55,1.0):
   for j in range(12):
    x0=-4.85+j*9.7/12;x1=-4.85+(j+1)*9.7/12
    beam('Bridge-vermilion',(x0,arch(x0)+height,z),(x1,arch(x1)+height,z),.12,.13,RED)
  for j in range(9):
   x=-4.72+j*9.44/8;y=arch(x)
   # Raised narrow posts and layered dark caps, broader at the two bridge ends.
   w=.18 if j in (0,8) else .15
   box('Bridge-vermilion',(x,y+.61,z),(w,1.22,w),RED,.018)
   box('Bridge-ink',(x,y+1.24,z),(w+.10,.10,w+.10),INK,.016)
   box('Bridge-gold',(x,y+1.30,z),(w+.025,.025,w+.025),GOLD,0)
   cylinder('Bridge-gold',(x,y+.80,z+(.094 if z>0 else -.094)),.061,.018,vertices=10)
   box('Bridge-ink',(x,y+.10,z),(w+.06,.16,w+.06),INK,.012)
  # Decorative Japanese curved end finials, stepped red rails curling upward.
  for sign in (-1,1):
   xx=sign*4.85;yy=arch(xx)+1.0
   pts=[(xx-sign*.22,yy,z),(xx,yy+.02,z),(xx+sign*.20,yy+.10,z),(xx+sign*.28,yy+.22,z)]
   for a,b in zip(pts,pts[1:]):beam('Bridge-vermilion',a,b,.11,.12,RED)
   cylinder('Bridge-gold',(xx+sign*.28,yy+.23,z),.055,.14,vertices=10)


def export(part,objects):
 result=native.Mesh();deps=bpy.context.evaluated_depsgraph_get()
 for obj in objects:
  # Applying bevel and merge in Blender gives authored edge loops, not raw cubes.
  evaluated=obj.evaluated_get(deps);me=bpy.data.meshes.new_from_object(evaluated,depsgraph=deps)
  me.transform(obj.matrix_world)
  bm=bmesh.new();bm.from_mesh(me)
  bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
  bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
  bm.to_mesh(me);bm.free();me.calc_loop_triangles()
  base=len(result.v);col=obj.color[:3]
  for v in me.vertices:
   p=uc(v.co);result.vertex(p,col,(p[0]*.35,p[1]*.35))
  for tri in me.loop_triangles:result.tri.append(tuple(base+i for i in tri.vertices))
  bpy.data.meshes.remove(me)
 # Native uses Unity Y-up coordinates, with positive determinant conversion.
 target=OUT/(part+'.asset');result.write(target);g=native.guid(target)
 v=np.array(result.v);rows.append({'name':part,'guid':g,'vertices':len(v),'triangles':len(result.tri),'min':v.min(0).tolist(),'max':v.max(0).tolist()})
 return target


def preview():
 # Camera displays Blender source assembled into two separate asset examples.
 for part,objects in parts.items():
  for obj in objects:
   if part.startswith('Mill-support'):obj.location+=cv((-5,0,0))
   elif part.startswith('Mill-wheel'):obj.location+=cv((-5,2.0,0))
   elif part.startswith('Bridge'):obj.location+=cv((4,0,0))
 bpy.ops.mesh.primitive_plane_add(size=100,location=(0,0,-.15));floor=bpy.context.object
 mat=bpy.data.materials.new('Neutral preview ground');mat.diffuse_color=(.16,.19,.14,1);floor.data.materials.append(mat)
 bpy.ops.object.camera_add(location=(15,-20,12));cam=bpy.context.object
 cam.rotation_euler=(Vector((.5,0,1.7))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=18
 scene=bpy.context.scene;scene.camera=cam;scene.world.color=(.3,.3,.3)
 for pos,power,size in [((-4,-7,12),1900,8),((7,5,8),1100,6)]:
  bpy.ops.object.light_add(type='AREA',location=pos);bpy.context.object.data.energy=power;bpy.context.object.data.size=size
 scene.render.engine='CYCLES';scene.cycles.samples=24;scene.cycles.use_denoising=False
 scene.render.resolution_x=1500;scene.render.resolution_y=850;scene.render.resolution_percentage=100
 scene.render.use_stamp=True;scene.render.use_stamp_note=True;scene.render.stamp_note_text='BLENDER ASSET PREVIEW - NOT UNITY GAMEPLAY';scene.render.use_stamp_date=False;scene.render.use_stamp_time=False;scene.render.use_stamp_frame=False;scene.render.use_stamp_filename=False;scene.render.stamp_font_size=16
 scene.render.image_settings.file_format='JPEG';scene.render.image_settings.quality=90;scene.render.filepath=str(LOCAL/'blender-landmarks.jpg')
 bpy.ops.wm.save_as_mainfile(filepath=str(LOCAL/'sunward-landmarks.blend'))
 bpy.ops.render.render(write_still=True)


def main():
 bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
 OUT.mkdir(parents=True,exist_ok=True);waterwheel();bridge()
 for part,objects in parts.items():export(part,objects)
 assert sum(row['triangles'] for row in rows)<=15000,'Landmark geometry exceeded budget'
 manifest={'authoring':'Blender4.3 bevel evaluation,bmesh vertex weld and face-normal recalculation; no external assets','coordinates':'Unity metres, Y up','wheel':'Axis local +Z; wood/iron same centre; radius2.10,bodydepth.64,axlelength1.10','support':'Ground origin, wheel bearing localY2.0; no collision included','bridge':'9.7mX rail span,Z+/-1.18; existing arch .10+.42*sin(pi*u)^1.5; no deck/collision','parts':rows}
 (ROOT/'tools/ink-world/blender-landmarks-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print('SUNWARD_BLENDER_MESHES '+json.dumps(rows))
 preview()

if __name__=='__main__':main()

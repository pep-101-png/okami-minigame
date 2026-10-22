"""Inspect saved resident geometry and weighted walk poses using Blender.
This is an offline model preview, never a claimed Unity render.
"""
import bpy,math,re,struct
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'Sunward-Unity/Assets/Sunward/Generated/LivingVillagers';DEST=ROOT/'tools/living-world/previews';DEST.mkdir(exist_ok=True)

def rot_x(a):
 a=math.radians(a);return np.array([[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]])
def rotation(a,b):
 a=a/np.linalg.norm(a);b=b/np.linalg.norm(b);v=np.cross(a,b);c=np.dot(a,b);k=np.array([[0,-v[2],v[1]],[v[2],0,-v[0]],[-v[1],v[0],0]])
 return np.eye(3)+k+k@k/(1+c) if c>-.99999 else rot_x(180)
def mat(p,r=None):
 m=np.eye(4);m[:3,3]=p
 if r is not None:m[:3,:3]=r
 return m

def pose(phase):
 bob=-.018+math.cos(phase*math.tau*2)*.006
 poses=[mat((0,.74+bob,0)),mat((0,1.20+bob,0)),mat((0,1.68+bob,0))]
 for side in (-1,1):
  p=(phase+(0 if side<0 else .5))%1
  z=.16*(1-p/.6*2) if p<.6 else -.16+.32*((p-.6)/.4)
  y=.065+(math.sin((p-.6)/.4*math.pi)*.055 if p>=.6 else 0)
  a=np.array([side*.14,.74+bob,0]);goal=np.array([side*.14,y,z]);axis=goal-a;d=min(np.linalg.norm(axis),.6749);axis/=np.linalg.norm(axis);l1=.34;l2=.335
  x=(l1*l1-l2*l2+d*d)/(2*d);h=math.sqrt(max(0,l1*l1-x*x));bend=np.array([0,0,1])-axis*axis[2];bend/=np.linalg.norm(bend);knee=a+axis*x+bend*h
  poses.extend([mat(a,rotation(np.array([0,-1,0]),knee-a)),mat(knee,rotation(np.array([0,-1,0]),goal-knee)),mat(goal)])
 for side in (-1,1):
  p=(phase+(0 if side<0 else .5))%1;r=rot_x(-math.sin(p*math.tau)*12);a=np.array([side*.27,1.42+bob,0]);b=a+r@np.array([side*.16,-.24,0]);poses.extend([mat(a,r),mat(b,r@rot_x(-5))])
 return poses

def read(role,phase=None):
 s=(OUT/('Living-'+role+'.asset')).read_text();n=int(re.search(r'm_VertexCount: (\d+)',s)[1]);raw=bytes.fromhex(re.search(r'_typelessdata: ([a-f0-9]+)',s)[1]);v=np.array([struct.unpack_from('<3f',raw,i*80) for i in range(n)]);colors=np.array([struct.unpack_from('<3f',raw,i*80+24) for i in range(n)])
 ix=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([a-f0-9]+)',s)[1]),dtype='<u4').reshape(-1,3)
 if phase is not None:
  block=re.search(r'  m_BindPose:\n(.*?)(?=  m_BoneNameHashes:)',s,re.S)[1]
  binds=[np.array(list(map(float,re.findall(r'e\d\d: ([^\n]+)',b)))).reshape(4,4) for b in re.split(r'(?=  - e00:)',block) if 'e00:' in b]
  matrices=np.array([a@b for a,b in zip(pose(phase),binds)]);vv=np.column_stack([v,np.ones(len(v))]);result=np.zeros((n,3))
  for k in range(4):
   weights=np.array([struct.unpack_from('<f',raw,i*80+48+k*4)[0] for i in range(n)]);bones=np.array([struct.unpack_from('<I',raw,i*80+64+k*4)[0] for i in range(n)])
   result+=np.einsum('nij,nj->ni',matrices[bones],vv)[:,:3]*weights[:,None]
  v=result
 return v,ix,colors

def reset():bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
def add(role,position,phase=None):
 v,ix,colors=read(role,phase);v=np.column_stack([v[:,0],-v[:,2],v[:,1]])
 mesh=bpy.data.meshes.new(role);mesh.from_pydata(v,[],ix);mesh.update();o=bpy.data.objects.new(role,mesh);bpy.context.collection.objects.link(o);o.location=position
 attr=mesh.color_attributes.new(name='Pigment',type='FLOAT_COLOR',domain='POINT')
 for d,c in zip(attr.data,colors):d.color=(*c,1)
 m=bpy.data.materials.new(role);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Roughness'].default_value=.85;vc=m.node_tree.nodes.new('ShaderNodeVertexColor');vc.layer_name='Pigment';m.node_tree.links.new(vc.outputs['Color'],bs.inputs['Base Color']);mesh.materials.append(m)
 for f in mesh.polygons:f.use_smooth=True

def render(name,look,camera,scale,res):
 bpy.ops.mesh.primitive_plane_add(size=100);m=bpy.data.materials.new('parchment');m.diffuse_color=(.31,.28,.21,1);bpy.context.object.data.materials.append(m)
 bpy.ops.object.camera_add(location=camera);cam=bpy.context.object;cam.rotation_euler=(Vector(look)-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=scale;bpy.context.scene.camera=cam
 for pos,power in [((-4,-5,7),900),((5,2,4),700)]:
  bpy.ops.object.light_add(type='AREA',location=pos);bpy.context.object.data.energy=power;bpy.context.object.data.size=5
 s=bpy.context.scene;s.world.color=(.35,.35,.35);s.render.engine='CYCLES';s.cycles.samples=16;s.cycles.use_denoising=False;s.render.resolution_x=res[0];s.render.resolution_y=res[1];s.render.resolution_percentage=100;s.render.image_settings.file_format='JPEG';s.render.filepath=str(DEST/(name+'.jpg'));bpy.ops.render.render(write_still=True)
reset()
for i,r in enumerate(['Gardener','Merchant','Elder','Samurai','ShrineMaiden','Geisha','Chef']):add(r,((i-3)*1.2,0,0))
render('resident-costumes-blender',(0,0,1),(2,-14,5),9.4,(1800,850))
reset()
for k,r in enumerate(['Samurai','Chef','Geisha']):
 for i,p in enumerate([.05,.33,.72]):add(r,((i-1)*1.3,(k-1)*1.3,0),p)
render('resident-weighted-walk-blender',(0,0,1),(6,-12,6),6.4,(1400,1000))

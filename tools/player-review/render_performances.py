"""Inspect saved skin weights with held-prop IK. Blender asset poses, not Unity."""
from pathlib import Path
import sys,re,math,struct
import numpy as np
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
source=(ROOT/'tools/living-world/render_residents.py').read_text().split('reset()\nfor i,r')[0]
exec(compile(source,str(ROOT/'tools/living-world/render_residents.py'),'exec'),globals())
DEST=ROOT/'tools/player-review/previews';DEST.mkdir(exist_ok=True)
parents=[-1,0,1,0,3,4,0,6,7,1,9,1,11]
base=[]
s=(OUT/'Living-Samurai.asset').read_text();block=re.search(r'  m_BindPose:\n(.*?)(?=  m_BoneNameHashes:)',s,re.S)[1]
for b in re.split(r'(?=  - e00:)',block):
 if 'e00:' in b:base.append(np.linalg.inv(np.array(list(map(float,re.findall(r'e\d\d: ([^\n]+)',b)))).reshape(4,4)))
locals_=[base[i] if p<0 else np.linalg.inv(base[p])@base[i] for i,p in enumerate(parents)]

def fk(seated=False):
 poses=[]
 for i,p in enumerate(parents):
  local=locals_[i].copy()
  if i==0 and seated:local[1,3]-=.5
  if seated and i in [3,6]:local[:3,:3]=rot_x(-80)
  if seated and i in [4,7]:local[:3,:3]=rot_x(138)
  poses.append(local if p<0 else poses[p]@local)
 for i in [5,8]:poses[i][:3,:3]=np.eye(3)
 return poses

def reach(poses,side,target):
 aidx=9 if side==0 else 11;bidx=aidx+1;hand=np.array([-.10 if side==0 else .10,-.24,.052,1]);a=poses[aidx][:3,3].copy();b=poses[bidx][:3,3].copy();c=(poses[bidx]@hand)[:3]
 l1=np.linalg.norm(b-a);l2=np.linalg.norm(c-b);axis=target-a;d=np.clip(np.linalg.norm(axis),abs(l1-l2)+.0001,l1+l2-.0001);axis/=np.linalg.norm(axis);x=(l1*l1-l2*l2+d*d)/(2*d);h=math.sqrt(max(0,l1*l1-x*x));pole=np.array([-1 if side==0 else 1,-.2,0]);pole-=axis*pole.dot(axis);pole/=np.linalg.norm(pole);knee=a+axis*x+pole*h
 poses[aidx][:3,:3]=rotation(b-a,knee-a)@poses[aidx][:3,:3];poses[bidx]=poses[aidx]@locals_[bidx];b=poses[bidx][:3,3];c=(poses[bidx]@hand)[:3];poses[bidx][:3,:3]=rotation(c-b,a+axis*d-b)@poses[bidx][:3,:3]

poses=fk()
def pose(_):return poses

def prop(name,matrix,offset):
 p=OUT/(name+'.asset');s=p.read_text();n=int(re.search(r'm_VertexCount: (\d+)',s)[1]);raw=bytes.fromhex(re.search(r'_typelessdata: ([0-9a-f]+)',s)[1]);stride=len(raw)//n;v=np.array([struct.unpack_from('<3f',raw,k*stride) for k in range(n)]);v=(np.column_stack([v,np.ones(n)])@matrix.T)[:,:3];v=np.column_stack([v[:,0],-v[:,2],v[:,1]]);ix=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-f]+)',s)[1]),dtype='<u4').reshape(-1,3)
 me=bpy.data.meshes.new(name);me.from_pydata(v,[],ix);me.update();ob=bpy.data.objects.new(name,me);bpy.context.collection.objects.link(ob);ob.location=offset;m=bpy.data.materials.new(name);m.diffuse_color=(.37,.18,.06,1);me.materials.append(m)

reset()
for i,p in enumerate([0,1,.45]):
 poses=fk();weapon=mat((0,1.53+(1.16-1.53)*p,.13+(.33-.13)*p),rot_x(-18+81*p));reach(poses,1,weapon[:3,3]);reach(poses,0,(weapon@np.array([0,-.075,0,1]))[:3]);offset=((i-2)*1.55,0,0);add('Samurai',offset,0);prop('Practice-bokken',weapon,offset)
poses=fk(True);reach(poses,0,np.array([-.16,.73,.28]));reach(poses,1,np.array([.16,1.03,.26]));offset=(1.55,0,0);add('Chef',offset,0);prop('Rice-bowl',mat((-.16,.73,.28)),offset);prop('Tea-cup',mat((.16,1.03,.26)),offset)
a=math.radians(62);rz=np.array([[math.cos(a),-math.sin(a),0],[math.sin(a),math.cos(a),0],[0,0,1]])
poses=fk();violin=mat((-.06,1.27,.23),rz);bowmat=mat((.06,1.27,.30));reach(poses,0,(violin@np.array([0,.17,.035,1]))[:3]);reach(poses,1,(bowmat@np.array([.17,0,0,1]))[:3]);offset=(3.1,0,0);add('Geisha',offset,0);prop('Violin-carved-body',violin,offset);prop('Violin-horsehair-bow',bowmat,offset)
render('held-props-and-seated-poses',(0,0,1),(5,-14,5),9.3,(1800,820))

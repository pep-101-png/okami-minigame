"""Small native Unity asset authoring helpers. No Unity, Blender or external assets required."""
from pathlib import Path
import re,json,hashlib,struct,math
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
ASSETS=ROOT/'Sunward-Unity/Assets/Sunward'
OUT=ASSETS/'Generated/VillageFinish'

def guid(path):
 p=Path(str(path)+'.meta')
 if p.exists():return re.search(r'guid: (\w+)',p.read_text())[1]
 g=hashlib.md5(str(Path(path).relative_to(ROOT)).encode()).hexdigest()
 file_id=2100000 if Path(path).suffix=='.mat' else 4300000
 p.write_text(f'fileFormatVersion: 2\nguid: {g}\nNativeFormatImporter:\n  externalObjects: {{}}\n  mainObjectFileID: {file_id}\n  userData:\n  assetBundleName:\n  assetBundleVariant:\n')
 return g

def vec(s,key):return np.array([float(v) for v in re.search(r'\b'+key+r': \{x: ([^,]+), y: ([^,]+), z: ([^}]+)',s).groups()])
def fmt(p):return '{x: %.7g, y: %.7g, z: %.7g}'%tuple(p)
class Mesh:
 def __init__(self):self.v=[];self.c=[];self.uv=[];self.bones=[];self.tri=[]
 def vertex(self,p,color=(1,1,1),uv=(0,0),bone=0):
  self.v.append(tuple(p));self.c.append(tuple(color));self.uv.append(uv);self.bones.append(bone);return len(self.v)-1
 def face(self,pts,color, bone=0):
  ids=[self.vertex(p,color,(i%2,i//2),bone) for i,p in enumerate(pts)]
  for i in range(1,len(ids)-1):self.tri.append((ids[0],ids[i],ids[i+1]))
 def box(self,center,size,color,bone=0,bevel=.04):
  # Clipped corners and softly tapered bevels, not six primitive cube faces.
  x,y,z=center;w,h,d=np.array(size)*.5;b=min(bevel,w*.3,d*.3,h*.3)
  rings=[]
  for yy,rr in [(y-h,1-b/max(w,d)),(y-h+b,1),(y+h-b,1),(y+h,1-b/max(w,d))]:
   ring=[]
   for px,pz in [(-w+b,-d),(w-b,-d),(w,-d+b),(w,d-b),(w-b,d),(-w+b,d),(-w,d-b),(-w,-d+b)]:ring.append((x+px*rr,yy,z+pz*rr))
   rings.append(ring)
  self.face(rings[0],color,bone);self.face(list(reversed(rings[-1])),color,bone)
  for a,bb in zip(rings,rings[1:]):
   for k in range(8):self.face([a[k],bb[k],bb[(k+1)%8],a[(k+1)%8]],color,bone)
 def loft(self,rings,color,bone=0,n=16,flute=0):
  base=[]
  for j,(x,y,z,rx,rz) in enumerate(rings):
   ids=[]
   for k in range(n):
    a=k*math.tau/n;r=1+flute*math.cos(a*8)
    ids.append(self.vertex((x+math.cos(a)*rx*r,y,z+math.sin(a)*rz*r),np.array(color)*(1+.04*math.sin(a*3+j)),(k/n,j/max(1,len(rings)-1)),bone))
   base.append(ids)
  for a,b in zip(base,base[1:]):
   for k in range(n):kk=(k+1)%n;self.tri.extend([(a[k],b[k],a[kk]),(a[kk],b[k],b[kk])])
  for ids,reverse in [(base[0],False),(base[-1],True)]:
   center=np.mean(np.array(self.v)[ids],axis=0);m=self.vertex(center,color,(.5,.5),bone)
   for k in range(n):a,b=ids[k],ids[(k+1)%n];self.tri.append((m,b,a) if reverse else (m,a,b))
 def ellipsoid(self,p,size,color,bone=0,n=16,rows=10):
  rings=[]
  for j in range(rows+1):
   a=-math.pi/2+j*math.pi/rows;r=max(.005,math.cos(a));rings.append((p[0],p[1]+math.sin(a)*size[1],p[2],r*size[0],r*size[2]))
  self.loft(rings,color,bone,n)
 def tube(self,points,radii,color,bone=0,n=10,groove=0):
  rings=[]
  for j,p in enumerate(points):
   p=np.array(p);t=np.array(points[min(j+1,len(points)-1)],dtype=float)-np.array(points[max(0,j-1)],dtype=float);t/=max(np.linalg.norm(t),1e-8)
   ax=np.cross(t,(0,0,1) if abs(t[2])<.8 else (0,1,0));ax/=max(np.linalg.norm(ax),1e-8);az=np.cross(ax,t)
   ids=[]
   for k in range(n):
    a=k*math.tau/n;rr=radii[j]*(1+groove*math.sin(a*5+j*.7));ids.append(self.vertex(p+(ax*math.cos(a)+az*math.sin(a))*rr,np.array(color)*(1+.1*math.sin(a*5+j*.4)),(k/n,j*.35),bone))
   rings.append(ids)
  for a,b in zip(rings,rings[1:]):
   for k in range(n):kk=(k+1)%n;self.tri.extend([(a[k],b[k],a[kk]),(a[kk],b[k],b[kk])])
  for ids,rev in [(rings[0],False),(rings[-1],True)]:
   mid=self.vertex(np.mean(np.array(self.v)[ids],axis=0),color,(.5,.5),bone)
   for k in range(n):self.tri.append((mid,ids[(k+1)%n],ids[k]) if rev else (mid,ids[k],ids[(k+1)%n]))
 def leaf(self,p,length,width,angle,color,tip=.12,bone=0):
  p=np.array(p);right=np.array([math.cos(angle),0,math.sin(angle)]);forward=np.array([-math.sin(angle),0,math.cos(angle)])
  rows=[]
  for j in range(5):
   t=j/4;w=math.sin(t*math.pi)*width*.5;center=p+forward*length*t+np.array([0,math.sin(t*math.pi)*length*.2+t*tip,0]);rows.append([center-right*w,center+np.array([0,width*.12*math.sin(t*math.pi),0]),center+right*w])
  for row,(a,b) in enumerate(zip(rows,rows[1:])):
   for k in range(2):
    ids=[self.vertex(p,np.array(color)*(1+k*.12),uv,bone) for p,uv in [(a[k],(k/2,row/4)),(b[k],(k/2,(row+1)/4)),(b[k+1],((k+1)/2,(row+1)/4)),(a[k+1],((k+1)/2,row/4))]]
    self.tri.extend([(ids[0],ids[1],ids[2]),(ids[0],ids[2],ids[3])])
 def merge(self,other,offset=(0,0,0),scale=(1,1,1)):
  n=len(self.v);self.v.extend((np.array(other.v)*scale+offset).tolist());self.c.extend(other.c);self.uv.extend(other.uv);self.bones.extend(other.bones);self.tri.extend(tuple(i+n for i in t) for t in other.tri)
 def save(self,name,skin=False,template=None):
  OUT.mkdir(parents=True,exist_ok=True);p=OUT/(name+'.asset');self.write(p,skin,template);return guid(p)
 def write(self,p,skin=False,template=None):
  assert self.v and self.tri
  v=np.array(self.v,dtype=float);ix=np.array(self.tri,dtype=int);norm=np.zeros_like(v)
  for a,b,c in ix:
   nn=np.cross(v[b]-v[a],v[c]-v[a])
   for k in (a,b,c):norm[k]+=nn
  lengths=np.linalg.norm(norm,axis=1);norm[lengths<1e-10]=(0,1,0);norm/=np.maximum(np.linalg.norm(norm,axis=1,keepdims=True),1e-10)
  buf=bytearray()
  for i,(pos,nn,c,uv) in enumerate(zip(v,norm,self.c,self.uv)):
   buf.extend(struct.pack('<12f',*pos,*nn,*np.clip(c,0,1),1,*uv))
   if skin:buf.extend(struct.pack('<4f4I',1,0,0,0,self.bones[i],0,0,0))
  sample=template or (ASSETS/'Generated/Renovation/Detail-18.asset').read_text()
  sample=re.sub(r'm_Name: .*',f'm_Name: {p.stem}',sample,count=1)
  sample=re.sub(r'indexCount: \d+',f'indexCount: {len(ix)*3}',sample,count=1)
  sample=re.sub(r'(?m)^(    vertexCount:|    m_VertexCount:) \d+',lambda m:f'{m[1]} {len(v)}',sample)
  sample=re.sub(r'(?m)^  m_IndexFormat: .*','  m_IndexFormat: 1',sample)
  sample=re.sub(r'(?m)^  m_IndexBuffer: .*','  m_IndexBuffer: '+ix.astype('<u4').tobytes().hex(),sample)
  channels=[]
  for i in range(14):
   offset,dimension,format_={0:(0,3,0),1:(12,3,0),3:(24,4,0),4:(40,2,0),12:(48,4,0),13:(64,4,10)}.get(i,(0,0,0))
   if i>=12 and not skin:dimension=0;offset=0;format_=0
   channels.append(f'    - stream: 0\n      offset: {offset}\n      format: {format_}\n      dimension: {dimension}\n')
  sample=re.sub(r'    m_Channels:\n.*?(?=    m_DataSize:)', '    m_Channels:\n'+''.join(channels),sample,flags=re.S)
  sample=re.sub(r'(?m)^    m_DataSize: .*',f'    m_DataSize: {len(buf)}',sample)
  sample=re.sub(r'(?m)^    _typelessdata: .*','    _typelessdata: '+buf.hex(),sample)
  center=(v.min(0)+v.max(0))/2;ext=(v.max(0)-v.min(0))/2
  if skin:
   poseblock=re.search(r'  m_BindPose:\n(.*?)(?=  m_BoneNameHashes:)',sample,re.S)[1]
   matrices=[np.array([float(x) for x in re.findall(r'e\d\d: ([^\n]+)',block)]).reshape(4,4) for block in re.split(r'(?=  - e00:)',poseblock) if 'e00:' in block]
   boxes=[]
   for bone,bind in enumerate(matrices):
    points=v[np.array(self.bones)==bone]
    local=(np.column_stack([points,np.ones(len(points))])@bind.T)[:,:3] if len(points) else np.zeros((1,3))
    boxes.append('  - m_Min: '+fmt(local.min(0))+'\n    m_Max: '+fmt(local.max(0))+'\n')
   sample=re.sub(r'  m_BonesAABB:.*?(?=  m_VariableBoneCountWeights:)', '  m_BonesAABB:\n'+''.join(boxes),sample,flags=re.S)
  sample=re.sub(r'm_Center: \{[^}]+\}', 'm_Center: '+fmt(center),sample)
  sample=re.sub(r'm_Extent: \{[^}]+\}', 'm_Extent: '+fmt(ext),sample)
  p.write_text('\n'.join(line.rstrip() for line in sample.splitlines())+'\n')
  np.savez_compressed('/tmp/sunward-'+p.stem+'.npz',vertices=v,triangles=ix,colors=np.array(self.c))

def material(name,color=(1,1,1),family=None,wind=0):
 template=(ASSETS/'Generated/Remake/Stone.mat').read_text();template=re.sub(r'm_Name: .*',f'm_Name: {name}',template,count=1)
 template=re.sub(r'- _VertexTint: .*','- _VertexTint: 1',template)
 template=re.sub(r'- _BaseColor: .*','- _BaseColor: {r: %g, g: %g, b: %g, a: 1}'%color,template)
 template=re.sub(r'- _ArtStrength: .*',f'- _ArtStrength: {0.6 if family else 0}',template)
 template=re.sub(r'- _SurfaceKind: .*',f'- _SurfaceKind: {1 if family=="wood" else 5 if wind else 2}',template)
 template=re.sub(r'- _Wind: .*',f'- _Wind: {wind}\n    - _WindObjectSpace: 1',template);template=re.sub(r'- _Cull: .*',f'- _Cull: {0 if wind else 2}',template)
 if family:
  for slot,suffix in [('_DetailMap',''),('_DetailNormal','-normal')]:
   g=guid(ASSETS/f'Textures/Art/Paint-{family}{suffix}.png')
   template=re.sub(r'(- '+slot+r':\n        m_Texture: )[^\n]+',r'\g<1>{fileID: 2800000, guid: '+g+', type: 3}',template)
 p=OUT/(name+'.mat');p.write_text('\n'.join(line.rstrip() for line in template.splitlines())+'\n');return guid(p)

class Scene:
 def __init__(self,path,text=None):
  self.path=path;s=path.read_text() if text is None else text;self.header=s.split('--- !u!')[0];self.blocks={}
  for b in re.split(r'(?=--- !u!)',s):
   if b.startswith('--- !u!'):self.blocks[int(re.search(r'&(-?\d+)',b)[1])]=b
  self.next=8000000000000000000
 def alloc(self):
  self.next+=1
  while self.next in self.blocks:self.next+=1
  return self.next
 def kind(self,id):return int(re.match(r'--- !u!(\d+)',self.blocks[id])[1])
 def name(self,id):
  m=re.search(r'^  m_Name: (.*)',self.blocks.get(id,''),re.M)
  if not m:return ''
  value=m[1]
  if value.startswith('"'):return bytes(value[1:-1],'utf8').decode('unicode_escape')
  return value
 def refs(self,id):return [int(x) for x in re.findall(r'component: \{fileID: (-?\d+)\}',self.blocks[id])]
 def owner(self,id):
  match=re.search(r'm_GameObject: \{fileID: (-?\d+)\}',self.blocks[id])
  return int(match[1]) if match else 0
 def component(self,id,kind):return next((r for r in self.refs(id) if self.kind(r)==kind),None)
 def transform(self,id):return self.component(id,4)
 def set(self,id,key,value):
  s,count=re.subn(r'(?m)^  '+key+r': .*',lambda _:'  '+key+': '+str(value),self.blocks[id]);assert count==1,(id,key);self.blocks[id]=s
 def disabled(self,id):self.set(id,'m_Enabled',0)
 def add(self,name,mesh,mat,parent=0,p=(0,0,0),scale=(1,1,1)):
  go,t,mf,mr=[self.alloc() for _ in range(4)]
  source_go=next(i for i in self.blocks if self.kind(i)==1 and self.component(i,33) and self.component(i,23) and self.component(i,4))
  templates=[self.blocks[source_go],self.blocks[self.transform(source_go)],self.blocks[self.component(source_go,33)],self.blocks[self.component(source_go,23)]]
  oldids=[source_go,self.transform(source_go),self.component(source_go,33),self.component(source_go,23)]
  for typ,id,raw in zip([1,4,33,23],[go,t,mf,mr],templates):
   raw=re.sub(r'^--- !u!\d+ &-?\d+.*',f'--- !u!{typ} &{id}',raw)
   for old,new in zip(oldids,[go,t,mf,mr]):raw=re.sub(r'fileID: '+str(old)+r'\b','fileID: '+str(new),raw)
   self.blocks[id]=raw
  self.blocks[go]=re.sub(r'  m_Component:\n.*?(?=  m_Layer:)',f'  m_Component:\n  - component: {{fileID: {t}}}\n  - component: {{fileID: {mf}}}\n  - component: {{fileID: {mr}}}\n',self.blocks[go],flags=re.S)
  self.set(go,'m_Name',json.dumps(name));self.set(go,'m_IsActive',1)
  self.set(t,'m_LocalPosition',fmt(p));self.set(t,'m_LocalScale',fmt(scale));self.set(t,'m_LocalRotation','{x: 0, y: 0, z: 0, w: 1}');self.set(t,'m_Father',f'{{fileID: {parent}}}')
  self.blocks[t]=re.sub(r'  m_Children:.*?(?=  m_Father:)', '  m_Children: []\n',self.blocks[t],flags=re.S)
  self.set(mf,'m_Mesh',f'{{fileID: 4300000, guid: {mesh}, type: 2}}')
  self.set(mr,'m_Enabled',1);self.blocks[mr]=re.sub(r'  m_Materials:\n.*?(?=  m_StaticBatchInfo:)',f'  m_Materials:\n  - {{fileID: 2100000, guid: {mat}, type: 2}}\n',self.blocks[mr],flags=re.S)
  if parent:
   raw=self.blocks[parent]
   if '  m_Children: []' in raw:raw=raw.replace('  m_Children: []',f'  m_Children:\n  - {{fileID: {t}}}')
   else:raw=raw.replace('  m_Children:\n',f'  m_Children:\n  - {{fileID: {t}}}\n')
   self.blocks[parent]=raw
  else:
   root=next(i for i in self.blocks if self.kind(i)==1660057539);self.blocks[root]+=f'  - {{fileID: {t}}}\n'
  return go
 def save(self):
  # SceneRoots stays last. Unity accepts object blocks in arbitrary order.
  root=next(i for i in self.blocks if self.kind(i)==1660057539)
  self.path.write_text('\n'.join(line.rstrip() for line in (self.header+''.join(v for i,v in self.blocks.items() if i!=root)+self.blocks[root]).splitlines())+'\n')

def repaired_normals(raw):
 """Filtered legacy mesh copies need finite normals even on unused/degenerate source vertices."""
 n=int(re.search(r'm_VertexCount: (\d+)',raw)[1]);data=bytearray.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)',raw)[1]);stride=len(data)//n
 v=np.array([struct.unpack_from('<3f',data,i*stride) for i in range(n)])
 dtype='<u4' if 'm_IndexFormat: 1' in raw else '<u2';ix=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-fA-F]+)',raw)[1]),dtype=dtype).reshape(-1,3)
 normal=np.zeros_like(v)
 for a,b,c in ix:
  nn=np.cross(v[b]-v[a],v[c]-v[a])
  for i in (a,b,c):normal[i]+=nn
 lengths=np.linalg.norm(normal,axis=1);normal[lengths<1e-10]=(0,1,0);normal/=np.maximum(np.linalg.norm(normal,axis=1,keepdims=True),1e-10)
 for i,nn in enumerate(normal):struct.pack_into('<3f',data,i*stride+12,*nn)
 return re.sub(r'(?m)^    _typelessdata: .*','    _typelessdata: '+data.hex(),raw)

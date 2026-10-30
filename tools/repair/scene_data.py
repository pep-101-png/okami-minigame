"""Read resolved saved-scene render geometry and prefab overrides without Unity."""
from pathlib import Path
import re,sys,json
import math
import numpy as np
ROOT=Path(__file__).resolve().parents[2];A=ROOT/'Sunward-Unity/Assets'
sys.path.insert(0,str(ROOT/'tools/village'))
from native import Scene,vec

def ref(raw,key):
    m=re.search(re.escape(key)+r': \{fileID: (-?\d+)(?:, guid: (\w+))?',raw)
    return (int(m[1]),m[2]) if m else (0,None)
def rotation(q):
    x,y,z,w=q
    return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def transform(raw):
    m=np.eye(4);q=list(map(float,re.search(r'm_LocalRotation: \{x: ([^,]+), y: ([^,]+), z: ([^,]+), w: ([^}]+)',raw).groups()));m[:3,:3]=rotation(q)@np.diag(vec(raw,'m_LocalScale'));m[:3,3]=vec(raw,'m_LocalPosition');return m
class World:
    def __init__(self):
        self.scene=Scene(A/'Sunward/Scenes/Windflower.unity');self.assets={};self.prefabs={};self.meshes={};self.transforms={};self.overrides={};self.meshfiles={}
        for p in A.rglob('*.meta'):
            m=re.search(r'^guid: (\w+)',p.read_text(),re.M)
            if m:self.assets[m[1]]=p.with_suffix('')
        for i,b in self.scene.blocks.items():
            if self.scene.kind(i)!=1001:continue
            source=self.assets.get(ref(b,'m_SourcePrefab')[1])
            if source is None or source.suffix!='.prefab':continue
            self.prefabs[i]=Scene(source);o={}
            for m in re.finditer(r'    - target: \{fileID: (-?\d+),[^\n]+\}\n      propertyPath: ([^\n]+)\n      value:[ \t]*([^\n]*)\n      objectReference: ([^\n]+)',b):o[int(m[1]),m[2].strip("'\"")]=(m[3],m[4])
            self.overrides[i]=o
    def raw(self,instance,id):
        src=self.scene if instance==0 else self.prefabs[instance];raw=src.blocks[id]
        if not instance:return raw
        for (target,key),(value,reference) in self.overrides[instance].items():
            if target!=id:continue
            if key.startswith(('m_LocalPosition.','m_LocalScale.','m_LocalRotation.')):
                field,axis=key.split('.');raw=re.sub(r'('+field+r': \{[^\n]*?\b'+axis+r': )[^,}]+',lambda m:m[1]+value,raw)
            elif key=='m_Mesh':raw=re.sub(r'm_Mesh: [^\n]+','m_Mesh: '+reference,raw)
            elif key=='m_Materials.Array.data[0]':raw=re.sub(r'(  m_Materials:\n  - )[^\n]+',lambda m:m[1]+reference,raw)
            elif key in ['m_Enabled','m_IsActive']:raw=re.sub(r'(?m)^  '+key+r': [^\n]+','  '+key+': '+value,raw)
        return raw
    def matrix(self,instance,id):
        if not id:return np.eye(4)
        key=(instance,id)
        if key in self.transforms:return self.transforms[key]
        raw=self.raw(instance,id)
        if 'm_LocalPosition:' not in raw:
            prefab=ref(raw,'m_PrefabInstance')[0];source=ref(raw,'m_CorrespondingSourceObject')[0]
            out=self.matrix(prefab,source) if prefab in self.prefabs else np.eye(4)
        else:
            parent=ref(raw,'m_Father')[0];base=self.matrix(instance,parent)
            if instance and not parent:
                pt=ref(self.scene.blocks[instance],'m_TransformParent')[0];base=self.matrix(0,pt)
            out=base@transform(raw)
        self.transforms[key]=out;return out
    def active(self,instance,go):
        src=self.scene if not instance else self.prefabs[instance];raw=self.raw(instance,go)
        if '  m_IsActive: 0\n' in raw:return False
        t=src.transform(go)
        if not t:return False
        parent=ref(self.raw(instance,t),'m_Father')[0]
        return self.active(instance,src.owner(parent)) if parent and parent in src.blocks and src.owner(parent) else True
    def mesh(self,guid,fileid):
        key=(guid,fileid)
        if key in self.meshes:return self.meshes[key]
        path=self.assets.get(guid)
        if not path or path.suffix!='.asset':return None
        if guid not in self.meshfiles:
            self.meshfiles[guid]={int(m[1]):m[0] for m in re.finditer(r'--- !u!43 &(-?\d+)\n(.*?)(?=--- !u!|\Z)',path.read_text(),re.S)}
        raw=self.meshfiles[guid].get(fileid)
        if raw is None:return None
        count=int(re.search(r'm_VertexCount: (\d+)',raw)[1])
        if not count:return None
        buf=bytes.fromhex(re.search('_typelessdata: ([a-f0-9]+)',raw)[1]);stride=len(buf)//count
        v=np.ndarray((count,3),'<f4',buffer=buf,strides=(stride,4)).copy();ix=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([a-f0-9]*)',raw)[1]),'<u4' if 'm_IndexFormat: 1' in raw else '<u2').reshape(-1,3)
        out=dict(path=path,raw=raw,vertices=v,triangles=ix,stride=stride);self.meshes[key]=out;return out
    def renderers(self):
        for instance,source in [(0,self.scene),*self.prefabs.items()]:
            for i in source.blocks:
                if source.kind(i) not in [23,137]:continue
                raw=self.raw(instance,i);go=source.owner(i)
                if not go or 'm_Name:' not in source.blocks[go] or '  m_Enabled: 0\n' in raw or not self.active(instance,go):continue
                if source.kind(i)==137:mesh=ref(raw,'m_Mesh')
                else:
                    mf=source.component(go,33)
                    if not mf:continue
                    mesh=ref(self.raw(instance,mf),'m_Mesh')
                matrix=self.matrix(instance,source.transform(go));data=self.mesh(mesh[1],mesh[0]);lo=hi=None
                if data is not None:
                    p=data['vertices']@matrix[:3,:3].T+matrix[:3,3];lo=p.min(0);hi=p.max(0)
                materials=re.findall(r'guid: (\w+)',re.search(r'  m_Materials:\n(.*?)(?=  m_StaticBatchInfo:|  m_StaticBatchRoot:)',raw,re.S)[1])
                yield dict(instance=instance,renderer=i,go=go,name=source.name(go),meshID=mesh[0],meshGUID=mesh[1],mesh=self.assets.get(mesh[1]),materials=materials,kind=source.kind(i),matrix=matrix,lo=lo,hi=hi)

class Terrain:
    def __init__(self,world,rows=None):
        rows=list(world.renderers()) if rows is None else rows
        r=next(r for r in rows if r['lo'] is not None and r['hi'][0]-r['lo'][0]>120 and r['hi'][1]<2)
        v=world.mesh(r['meshGUID'],r['meshID'])['vertices'];self.heights={(round(float(x),2),round(float(z),2)):float(y) for x,y,z in v}
    def height(self,x,z):
        x=float(np.clip(x,-60,69.999));z=float(np.clip(z,-47.999,48));ix=math.floor((x+60)*2);iz=math.floor((48-z)*2);u=(x+60)*2-ix;v=(48-z)*2-iz;x0=-60+ix*.5;z0=48-iz*.5
        h00=self.heights[round(x0,2),round(z0,2)];h10=self.heights[round(x0+.5,2),round(z0,2)];h01=self.heights[round(x0,2),round(z0-.5,2)];h11=self.heights[round(x0+.5,2),round(z0-.5,2)]
        return h00+(h10-h00)*u+(h01-h00)*v if u+v<=1 else h11+(h01-h11)*(1-u)+(h10-h11)*(1-v)

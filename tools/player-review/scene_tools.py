from pathlib import Path
import re,sys,numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/village'))
from native import *

def parent(s,t):
 m=re.search(r'm_Father: \{fileID: (-?\d+)\}',s.blocks.get(t,''));return int(m[1]) if m else 0

def active(s,go):
 while go and go in s.blocks:
  if '  m_IsActive: 0\n' in s.blocks[go]:return False
  t=s.transform(go)
  if not t:return True
  t=parent(s,t);go=s.owner(t) if t else 0
 return True

def world(s,t,cache=None):
 cache={} if cache is None else cache
 if not t or t not in s.blocks:return np.eye(4)
 if t in cache:return cache[t]
 b=s.blocks[t]
 if 'm_LocalPosition:' not in b:return np.eye(4)
 p=vec(b,'m_LocalPosition');scale=vec(b,'m_LocalScale');q=re.search(r'm_LocalRotation: \{x: ([^,]+), y: ([^,]+), z: ([^,]+), w: ([^}]+)',b)
 x,y,z,w=map(float,q.groups());rot=np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
 m=np.eye(4);m[:3,:3]=rot@np.diag(scale);m[:3,3]=p
 cache[t]=world(s,parent(s,t),cache)@m;return cache[t]

def asset_index():
 return {re.search(r'guid: (\w+)',p.read_text())[1]:p.with_suffix('') for p in ASSETS.rglob('*.meta') if re.search(r'guid: (\w+)',p.read_text())}

def bounds(s,go,src,index,cache=None):
 mf=s.component(go,33)
 if not mf:return None
 b=s.blocks[mf];g=re.search(r'm_Mesh: \{fileID: (-?\d+), guid: (\w+)',b)
 if not g:return None
 if g[2]=='1aa5e7ba7e3b6c64889eadc3b9e05f0b':
  n=src.fileids.get(int(g[1]));v=src.positions(n) if n is not None else None
  if v is None:return None
  lo,hi=v.min(0),v.max(0)
 elif g[2] in index:
  p=index[g[2]]
  if p.suffix!='.asset':return None
  raw=p.read_text()
  if 'm_VertexCount:' not in raw:return None
  c,e=vec(raw,'m_Center'),vec(raw,'m_Extent');lo,hi=c-e,c+e
 else:return None
 corners=np.array([[x,y,z,1] for x in [lo[0],hi[0]] for y in [lo[1],hi[1]] for z in [lo[2],hi[2]]]);w=(corners@world(s,s.transform(go),cache).T)[:,:3];return w.min(0),w.max(0)

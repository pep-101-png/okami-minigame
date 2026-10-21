"""Sculpt closed, upturned Kasuga stone caps into the two existing native meshes.
Retains GUIDs, local mounting height and outer bounds; no scene/collider changes.
"""
from pathlib import Path
import re,math,struct
import numpy as np
ROOT=Path(__file__).resolve().parents[2]/'Sunward-Unity/Assets/Sunward/Generated'

def build():
 # Radial profile: closed underside, carved cornice, shallow concave hip, lotus finial.
 profile=[(0,1.50),(.45,1.50),(.48,1.525),(.51,1.56),(.50,1.59),(.43,1.61),(.36,1.65),(.27,1.74),(.17,1.82),(.09,1.86),(.07,1.90),(.085,1.94),(.055,2.00),(0,2.03)]
 sides=48;verts=[];uv=[];rings=[]
 for j,(radius,height) in enumerate(profile):
  ring=[]
  for k in range(1 if radius==0 else sides):
   a=k*math.tau/sides
   # Four hip corners, softened rather than a generic circular cone.
   squareness=(1/max(abs(math.cos(a)),abs(math.sin(a))))**.60
   rr=radius*squareness/(2**.30) if radius>.10 else radius
   corner=abs(math.sin(a*2))**5
   lift=.035*corner*max(0,1-abs(height-1.58)/.12)
   ring.append(len(verts));verts.append((math.cos(a)*rr,height+lift,math.sin(a)*rr));uv.append((k/sides,j/(len(profile)-1)))
  rings.append(ring)
 tri=[]
 for j in range(len(rings)-1):
  a,b=rings[j],rings[j+1]
  for k in range(sides):
   n=(k+1)%sides
   if len(a)==1:tri.append((a[0],b[k],b[n]))
   elif len(b)==1:tri.append((a[k],b[0],a[n]))
   else:tri.extend([(a[k],b[k],a[n]),(a[n],b[k],b[n])])
 v=np.array(verts)
 v[:,0]*=.51/np.max(abs(v[:,0]));v[:,2]*=.51/np.max(abs(v[:,2]))
 norm=np.zeros_like(v)
 for t in tri:
  a,b,c=v[list(t)];n=np.cross(b-a,c-a)
  for k in t:norm[k]+=n
 norm/=np.maximum(np.linalg.norm(norm,axis=1,keepdims=True),1e-9)
 # Preserve the original exact bounding volume and mounting elevations.
 buf=b''.join(struct.pack('<12f',*p,*n,1,1,1,1,*u) for p,n,u in zip(v,norm,uv))
 indices=struct.pack('<'+'H'*(len(tri)*3),*(i for t in tri for i in t))
 return v,tri,buf,indices

def main():
 v,tri,buf,indices=build()
 for relative in ['EnvironmentReview/Mesh-1.asset','Renovation/Detail-73.asset']:
  p=ROOT/relative;s=p.read_text()
  s=re.sub(r'indexCount: \d+',f'indexCount: {len(tri)*3}',s,count=1)
  s=re.sub(r'(?m)^(    vertexCount:|    m_VertexCount:) \d+',lambda m:f'{m[1]} {len(v)}',s)
  s=re.sub(r'(?m)^  m_IndexBuffer: .*',f'  m_IndexBuffer: {indices.hex()}',s)
  s=re.sub(r'(?m)^    m_DataSize: \d+',f'    m_DataSize: {len(buf)}',s)
  s=re.sub(r'(?m)^    _typelessdata: .*',f'    _typelessdata: {buf.hex()}',s)
  p.write_text(s)
 # Geometry-only preview input, kept outside Assets/repository.
 with open('/tmp/sunward-lantern.obj','w') as f:
  for p in v:f.write('v %f %f %f\n'%tuple(p))
  for t in tri:f.write('f %d %d %d\n'%tuple(i+1 for i in t))
 print(f'{len(v)} vertices / {len(tri)} triangles per cap; original mounting bounds retained')
if __name__=='__main__':main()

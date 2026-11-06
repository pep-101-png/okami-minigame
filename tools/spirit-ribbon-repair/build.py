"""Smooth a derived copy of the original ES mesh; preserve originals and paint."""
from pathlib import Path
import json,math,hashlib,shutil,sys,re
import numpy as np
R=Path(__file__).resolve().parents[2];A=R/'Sunward-Unity/Assets';D=A/'OkamiRemaster/Original/Resources/Okami'
sys.path.insert(0,'/workspace/work/reference-repairs');from meta import meta

def smooth(a,b,x):
 u=np.clip((x-a)/(b-a),0,1);return u*u*(3-2*u)

def weights(z):
 t=max(0,min(4,z/.975));i=int(math.floor(t+.5));x=t-i
 ids=[max(0,min(4,i-1)),max(0,min(4,i)),max(0,min(4,i+1))]
 return ids,[.5*(.5-x)**2,.75-x*x,.5*(.5+x)**2]

rows=[]
for name in ['es4a','es4b']:
 folder=D/(name+'-flow');folder.mkdir(exist_ok=True);meta(folder);j=json.loads((D/name/'Model.json').read_text());counts=[]
 for p in j['parts']:
  v=np.array(p['positions']).reshape(-1,3);uv=np.array(p['uv']).reshape(-1,2);c=np.array(p['colors']).reshape(-1,4);verts=[np.r_[a,b,d].tolist() for a,b,d in zip(v,uv,c)];tris=np.array(p['indices']).reshape(-1,3).tolist();mid={}
  def midpoint(a,b):
   key=tuple(sorted((a,b)))
   if key not in mid:mid[key]=len(verts);verts.append(((np.array(verts[a])+verts[b])*.5).tolist())
   return mid[key]
  # Split long native edges, retaining original winding, cross sections and UVs.
  finished=[];pending=tris[:]
  while pending:
   tri=pending.pop();edges=[(tri[0],tri[1],tri[2]),(tri[1],tri[2],tri[0]),(tri[2],tri[0],tri[1])];a,b,c0=max(edges,key=lambda e:np.linalg.norm(np.array(verts[e[0]][:3])-verts[e[1]][:3]));length=np.linalg.norm(np.array(verts[a][:3])-verts[b][:3])
   if length<=.085:finished.append(tri);continue
   m=midpoint(a,b);pending.extend([[a,m,c0],[m,b,c0]])
  values=np.array(verts);values[:,:2]*=.65;values[:,8]*=smooth(.035,.22,values[:,2])*(1-smooth(3.35,3.83,values[:,2]));ids=[];w=[]
  for z in values[:,2]:ii,ww=weights(z);ids.extend(ii);w.extend(ww)
  p.update(positions=values[:,:3].ravel().tolist(),uv=values[:,3:5].ravel().tolist(),colors=values[:,5:9].ravel().tolist(),indices=np.array(finished).ravel().tolist(),boneIndices=ids,weights=w);counts.append(dict(vertices=len(values),triangles=len(finished)))
 j['derivation']='Original ES mesh subdivided without changing its topology or UV painting; transverse width 65%, native bind-chain quadratic weights and faded blunt roots/tips. Original assets unchanged.';j['name']=name+'-flow';dest=folder/'Model.json';dest.write_text(json.dumps(j,separators=(',',':'))+'\n');meta(dest)
 for tx in j['textures']:
  if not tx.get('vertexOnly'):
   dest=folder/tx['path'];shutil.copyfile(D/name/tx['path'],dest);meta(dest)
 rows.append(dict(original=name,derived=name+'-flow',sourceSHA256=j['sourceSHA256'],mesh=counts))
(R/'tools/spirit-ribbon-repair/provenance.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))

from pathlib import Path
import sys,json,numpy as np
sys.path[:0]=['/workspace/sunward-remaster/tools/playtest-followup','/workspace/sunward-tundra-desktop/tools/spirit-charge-home/trailer'];from pose_audit import bank;from asset_geometry import rotation,skin
D=Path(__file__).resolve().parents[2]/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami';P=Path(__file__).resolve().parents[2]/'Sunward-Unity/Assets/OkamiRemaster/Player/Resources/NativePlayer/pl00';m=json.loads((P/'Model.json').read_text());wm=json.loads((D/'wp29/Model.json').read_text());b=bank(P/'Poses.bytes');wb=bank(D/'wp29/Poses.bytes');bind=[np.zeros(3)]
for bone in m['bones']:bind.append(np.array(bone['position'])+bind[bone['parent']+1])
offset=bind[31]-bind[1]
def matrices(model,p):
 out=[]
 for i,r in enumerate(p):
  M=np.eye(4);M[:3,:3]=rotation(r[3:7])@np.diag(r[7:]);M[:3,3]=r[:3];parent=model['bones'][i-1]['parent']+1 if i else -1;out.append(M if parent<0 else out[parent]@M)
 return out
results=[]
for phase in np.linspace(.05,.26,12):
 p=b['pl00_523'][0][round(phase*(len(b['pl00_523'][0])-1))];ms=matrices(m,p);head=ms[8][:3,3];socket=(ms[1]@np.r_[offset,1])[:3]
 for wi in [0,len(wb['wp29_001'][0])//2]:
  parts=skin(wm,wb['wp29_001'][0][wi]);verts=[];samples=[]
  for part,v in zip(wm['parts'],parts):
   if int(part['name'].split('-')[1]) not in [1,3]:continue
   v=v@ms[1][:3,:3].T+socket+np.array([0,.22,-.5]);verts.append(v)
   tri=v[np.array(part['indices']).reshape(-1,3)];q=[]
   for a in np.linspace(0,1,8):
    for c in np.linspace(0,1,8):
     if a+c<=1:q.append(tri[:,0]*(1-a-c)+tri[:,1]*a+tri[:,2]*c)
   samples.append(np.concatenate(q))
  v=np.concatenate(verts);q=np.concatenate(samples);dist=((v-head)[:,[0,2]]**2).sum(1);hit=dist<.2025;lift=max(0,float(np.max(head[1]+np.sqrt(.2025-dist[hit])-v[hit,1])) if hit.any() else 0);lift+=.025 if lift else 0;q[:,1]+=lift;gap=float(np.linalg.norm(q-head,axis=1).min());results.append((float(phase),wi,lift,gap))
assert min(x[3] for x in results)>=.44,'Native held blade intersects the sampled skull volume'
print('lowest sampled skull clearance',min(x[3] for x in results),'lift range',min(x[2] for x in results),max(x[2] for x in results));print('failures',[r for r in results if r[3]<.44])
Path('/workspace/work/village-complete/blade-geometry.json').write_text(json.dumps(results,indent=2))

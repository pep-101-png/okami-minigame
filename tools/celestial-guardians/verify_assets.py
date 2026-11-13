"""Validate recovered guardian model/paint/bank bindings and Unity metadata."""
from pathlib import Path
import json,struct,numpy as np,re,hashlib
R=Path(__file__).resolve().parents[2];A=R/'Sunward-Unity/Assets';D=A/'OkamiRemaster/Original/Resources/Okami';checks=0
for name in ['guardian-sentinel','guardian-fox','guardian-eclipse']:
 p=D/name;j=json.loads((p/'Model.json').read_text());b=(p/'Poses.bytes').read_bytes();magic,version,nb,n=struct.unpack_from('<4sIII',b);assert magic==b'OPB1' and nb==len(j['bones'])+1
 for part in j['parts']:
  nv=len(part['positions'])//3;assert len(part['colors'])==nv*4 and len(part['uv'])==nv*2 and len(part['weights'])==nv*3
  assert all(0<=x<nv for x in part['indices']);assert np.allclose(np.array(part['weights']).reshape(-1,3).sum(1),1,atol=.005)
  tex=next(t for t in j['textures'] if t['index']==part['texture']);assert tex.get('vertexOnly') or (p/tex['path']).exists();checks+=1
 off=16
 for i in range(n):
  ln=struct.unpack_from('<I',b,off)[0];off+=4;clip=b[off:off+ln].decode();off+=ln;nf,duration,loop=struct.unpack_from('<IfI',b,off);off+=12;pose=np.frombuffer(b,'<f4',nf*nb*10,off).reshape(nf,nb,10);off+=pose.nbytes;assert np.isfinite(pose).all() and duration>0 and nf>=2;assert np.allclose(np.linalg.norm(pose[:,:,3:7],axis=2),1,atol=1e-5);checks+=1
 assert off==len(b)
 for file in [p,*p.iterdir()]:
  if file.suffix!='.meta':assert Path(str(file)+'.meta').exists(),file
assert json.loads((D/'guardian-sentinel/Model.json').read_text())['visibleGroups']==[0,1,4]
assert json.loads((D/'guardian-fox/Model.json').read_text())['visibleGroups']==[0,1]
for p in [*A.glob('OkamiRemaster/Original/Scripts/Celestial*.cs'),A/'Sunward/Scripts/GameFlow.Celestial.cs',A/'OkamiRemaster/Original/Shaders/OriginalCelestialCourt.shader',D/'Effects/CelestialCourt.mat']:assert Path(str(p)+'.meta').exists(),p
print('PASS',checks,'original model/texture/motion checks; metadata present')

"""Check recovered fish geometry, pose curves, textures and Unity metadata."""
from pathlib import Path
import json,struct,numpy as np,re
R=Path(__file__).resolve().parents[2];A=R/'Sunward-Unity/Assets';D=A/'OkamiRemaster/Original/Resources/Okami';checks=0
for name in ['ana1','ana5','ana6','ana8','anac','anad']:
 p=D/('pond-'+name);j=json.loads((p/'Model.json').read_text());b=(p/'Poses.bytes').read_bytes();magic,version,nb,n=struct.unpack_from('<4sIII',b);assert magic==b'OPB1' and nb==len(j['bones'])+1
 for part in j['parts']:
  nv=len(part['positions'])//3;assert len(part['colors'])==nv*4 and len(part['uv'])==nv*2 and len(part['weights'])==nv*3
  assert all(0<=x<nv for x in part['indices']);assert np.allclose(np.array(part['weights']).reshape(-1,3).sum(1),1,atol=.005)
  tx=next(t for t in j['textures'] if t['index']==part['texture']);assert tx.get('vertexOnly') or (p/tx['path']).exists();checks+=1
 off=16;clips={}
 for i in range(n):
  ln=struct.unpack_from('<I',b,off)[0];off+=4;clip=b[off:off+ln].decode();off+=ln;nf,duration,loop=struct.unpack_from('<IfI',b,off);off+=12;pose=np.frombuffer(b,'<f4',nf*nb*10,off).reshape(nf,nb,10);off+=pose.nbytes;assert np.isfinite(pose).all() and duration>0 and nf>=2;assert np.allclose(np.linalg.norm(pose[:,:,3:7],axis=2),1,atol=1e-5);checks+=1;clips[clip]=(duration,loop)
 assert off==len(b) and clips[name+'_003'][1]==1 and clips[name+'_003'][0]>.25
 for f in [p,*p.iterdir()]:
  if f.suffix!='.meta':assert Path(str(f)+'.meta').exists(),f
for p in [*A.glob('OkamiRemaster/Original/Scripts/Village*.cs'),*A.glob('OkamiRemaster/Original/Scripts/*Mastery*.cs'),A/'OkamiRemaster/Original/Scripts/MoonlitTrail.cs',A/'OkamiRemaster/Original/Scripts/SevenCutSequence.cs',A/'Sunward/Scripts/GameFlow.Adventures.cs',A/'Sunward/Scripts/ScrollUI.Adventures.cs']:assert Path(str(p)+'.meta').exists(),p
print('PASS',checks,'fish geometry, paint and source motion checks; .meta files present')

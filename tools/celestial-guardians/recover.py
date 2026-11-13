"""Recover guardian MD/DDP/MOT payloads from the user's inspected originals."""
from pathlib import Path
import sys,importlib.util,json,hashlib,struct,numpy as np,copy,re
R=Path(__file__).resolve().parents[2];S=Path('/workspace/work/full-asset-inspection');A=R/'Sunward-Unity/Assets';W=Path('/workspace/work/celestial-guardians');W.mkdir(exist_ok=True)
sys.path.insert(0,'/workspace/sunward-remaster/tools/remaster/live');import export_player as mot
spec=importlib.util.spec_from_file_location('converter','/workspace/sunward-remaster/tools/remaster/export_native_review.py');conv=importlib.util.module_from_spec(spec);spec.loader.exec_module(conv)
rows=[json.loads(s) for s in (S/'inventory.jsonl').read_text().splitlines()];ledger=[]
selected={'em61':['em61_000','em61_010','em61_011','em61_020','em61_030','em61_031','em61_032','em61_033','em61_040','em61_050'],'em16':['em60_001','em60_010','em60_011','em60_020','em60_030','em60_031','em60_035','em60_043'],'em62':['em62_000','em62_010','em62_011','em62_020','em62_030','em62_031','em62_032','em62_033','em62_040','em62_050']}
for pkg,names in selected.items():
 target=A/'OkamiRemaster/Original/Resources/Okami'/('guardian-sentinel' if pkg=='em16' else 'guardian-fox' if pkg=='em61' else 'guardian-eclipse');target.mkdir(exist_ok=True)
 es=[e for e in rows if e['group']=='EM' and e['package']==pkg];md=next(e for e in es if e['type']=='MD');raw=(S/md['cache']).read_bytes();assert hashlib.sha256(raw).hexdigest()==md['sha256']
 native=conv.read_model(raw,[dict(e,path=e.get('cache','')) for e in es],pkg,S,target,True);model=copy.deepcopy(native)
 for b in model['bones']:b['position']=(np.array(b['position'])*[-.075,.075,.075]).tolist()
 for p in model['parts']:
  p['positions']=(np.array(p['positions']).reshape(-1,3)*[-.075,.075,.075]).ravel().tolist();p['indices']=np.array(p['indices']).reshape(-1,3)[:,[0,2,1]].ravel().tolist()
 if pkg=='em61':model['visibleGroups']=[0,1]
 if pkg=='em16':model['visibleGroups']=[0,1,4]
 model['sourceUnits']='Metres; native X reflected; original geometry, paint and weights';(target/'Model.json').write_text(json.dumps(model,separators=(',',':')))
 records=[];motions=[]
 for name in names:
  row=next(e for e in es if e['type']=='MOT' and e['name']==name);raw=(S/row['cache']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];frames,loop,ch=mot.parse(raw,len(native['bones']),allow_duplicate_channels=True);n=max(2,(frames-1)*2+1);bank=np.array([mot.sample(native,ch,t) for t in np.linspace(0,frames-1,n)])
  for i in range(1,n):bank[i,np.sum(bank[i-1,:,3:7]*bank[i,:,3:7],axis=1)<0,3:7]*=-1
  assert np.isfinite(bank).all();b=name.encode();records.append(struct.pack('<I',len(b))+b+struct.pack('<IfI',n,max(1,frames-1)/30,int(loop))+bank.astype('<f4').tobytes());motions.append(dict(name=name,sha256=row['sha256'],frames=frames))
 (target/'Poses.bytes').write_bytes(struct.pack('<4sIII',b'OPB1',1,len(native['bones'])+1,len(records))+b''.join(records));ledger.append(dict(package=pkg,modelSHA256=md['sha256'],resource=target.name,motions=motions,textures=model['textures'],parts=len(model['parts'])))
 print(pkg,len(model['bones']),len(model['parts']),flush=True)
for target in [A/'OkamiRemaster/Original/Resources/Okami'/n for n in ['guardian-sentinel','guardian-eclipse','guardian-fox']]:
 for p in [target,*target.iterdir()]:
  if p.suffix=='.meta':continue
  g=hashlib.sha256(('CelestialGuardians/'+str(p.relative_to(A))).encode()).hexdigest()[:32];meta=Path(str(p)+'.meta')
  if meta.exists():continue
  if p.suffix=='.png':
   template=(A/'OkamiRemaster/Original/Resources/Okami/em11/Texture-0.png.meta').read_text();meta.write_text(re.sub(r'^guid: \w+','guid: '+g,template,flags=re.M))
  else:meta.write_text('fileFormatVersion: 2\nguid: '+g+'\n'+('folderAsset: yes\nDefaultImporter:' if p.is_dir() else 'TextScriptImporter:')+'\n  externalObjects: {}\n  userData:\n  assetBundleName:\n  assetBundleVariant:\n')
# The palace originally held only its sleeping pose. Add the recovered native
# standing idle, byte-for-byte from the already imported compatible player bank.
palace=A/'OkamiRemaster/Original/Resources/Okami/palace-shiranui/Poses.bytes';source=A/'OkamiRemaster/Player/Resources/NativePlayer/pl00/Poses.bytes'
b=palace.read_bytes();raw=source.read_bytes();_,_,nb,count=struct.unpack_from('<4sIII',b);_,_,sourceBones,n=struct.unpack_from('<4sIII',raw);assert nb==sourceBones
def records(data):
 _,_,bones,n=struct.unpack_from('<4sIII',data);off=16;out={}
 for _ in range(n):
  start=off;ln=struct.unpack_from('<I',data,off)[0];off+=4;name=data[off:off+ln].decode();off+=ln;frames,_,_=struct.unpack_from('<IfI',data,off);off+=12+frames*bones*40;out[name]=data[start:off]
 return out
record=records(raw)['pl00_000']
if 'pl00_000' not in records(b):palace.write_bytes(struct.pack('<4sIII',b'OPB1',1,nb,count+1)+b[16:]+record)
ledger.append(dict(resource='palace-shiranui',motion='pl00_000',sourceBank=str(source.relative_to(R)),sourceRecordSHA256=hashlib.sha256(record).hexdigest(),conversion='Exact compatible original idle record; existing sleeping clip preserved'))
(R/'tools/celestial-guardians/asset-provenance.json').write_text(json.dumps(ledger,indent=2))

"""Recover fish MD/DDP/MOT payloads from the user's inspected originals."""
from pathlib import Path
import sys,importlib.util,json,hashlib,struct,numpy as np,copy,re
R=Path(__file__).resolve().parents[2];S=Path('/workspace/work/full-asset-inspection');A=R/'Sunward-Unity/Assets';W=Path('/workspace/work/village-adventures');W.mkdir(exist_ok=True)
sys.path.insert(0,'/workspace/sunward-remaster/tools/remaster/live');import export_player as mot
spec=importlib.util.spec_from_file_location('converter','/workspace/sunward-remaster/tools/remaster/export_native_review.py');conv=importlib.util.module_from_spec(spec);spec.loader.exec_module(conv)
rows=[json.loads(s) for s in (S/'inventory.jsonl').read_text().splitlines()];ledger=[]

for pkg in ['ana1','ana5','ana6','ana8','anac','anad']:
 target=A/'OkamiRemaster/Original/Resources/Okami'/('pond-'+pkg);target.mkdir(exist_ok=True)
 es=[e for e in rows if e['group']=='AN' and e['package']==pkg];md=next(e for e in es if e['type']=='MD');raw=(S/md['cache']).read_bytes();assert hashlib.sha256(raw).hexdigest()==md['sha256']
 native=conv.read_model(raw,[dict(e,path=e.get('cache','')) for e in es],pkg,S,target,True);model=copy.deepcopy(native)
 for b in model['bones']:b['position']=(np.array(b['position'])*[-.075,.075,.075]).tolist()
 for p in model['parts']:
  p['positions']=(np.array(p['positions']).reshape(-1,3)*[-.075,.075,.075]).ravel().tolist();p['indices']=np.array(p['indices']).reshape(-1,3)[:,[0,2,1]].ravel().tolist()
 model['sourceUnits']='Metres; original fish geometry, weights, UV and paint';(target/'Model.json').write_text(json.dumps(model,separators=(',',':')))
 records=[];motions=[]
 for row in [e for e in es if e['type']=='MOT' and e.get('frames') and e['name'].endswith(('_002','_003','_004'))]:
  raw=(S/row['cache']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];frames,loop,ch=mot.parse(raw,len(native['bones']),allow_duplicate_channels=True);n=max(2,(frames-1)*2+1);bank=np.array([mot.sample(native,ch,t) for t in np.linspace(0,frames-1,n)])
  for i in range(1,n):bank[i,np.sum(bank[i-1,:,3:7]*bank[i,:,3:7],axis=1)<0,3:7]*=-1
  name=row['name'].encode();records.append(struct.pack('<I',len(name))+name+struct.pack('<IfI',n,max(1,frames-1)/30,int(loop))+bank.astype('<f4').tobytes());motions.append(dict(name=row['name'],sha256=row['sha256']))
 (target/'Poses.bytes').write_bytes(struct.pack('<4sIII',b'OPB1',1,len(native['bones'])+1,len(records))+b''.join(records));ledger.append(dict(package=pkg,sourceSHA256=md['sha256'],motions=motions,textures=model['textures']))
 for p in [target,*target.iterdir()]:
  if p.suffix=='.meta':continue
  g=hashlib.sha256(('VillageAdventures/'+str(p.relative_to(A))).encode()).hexdigest()[:32];m=Path(str(p)+'.meta')
  if m.exists():continue
  if p.suffix=='.png':m.write_text(re.sub(r'^guid: \w+','guid: '+g,(A/'OkamiRemaster/Original/Resources/Okami/em11/Texture-0.png.meta').read_text(),flags=re.M))
  else:m.write_text('fileFormatVersion: 2\nguid: '+g+'\n'+('folderAsset: yes\nDefaultImporter:' if p.is_dir() else 'TextScriptImporter:')+'\n  externalObjects: {}\n  userData:\n  assetBundleName:\n  assetBundleVariant:\n')
 print(pkg,flush=True)
(R/'tools/village-adventures/asset-provenance.json').write_text(json.dumps(ledger,indent=2))

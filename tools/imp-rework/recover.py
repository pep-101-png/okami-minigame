from pathlib import Path
import sys,json,struct,hashlib,numpy as np
R=Path(__file__).resolve().parents[2];S=Path('/workspace/work/full-asset-inspection');W=Path('/workspace/work/imp-rework');A=R/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami'
sys.path.insert(0,'/workspace/sunward-remaster/tools/remaster/live');import export_player as mot
rows=[json.loads(s) for s in (S/'inventory.jsonl').read_text().splitlines()]
ledger=[]
for idx in range(5):
 pkg=f'em0{idx}';model=json.loads((A/pkg/'Model.json').read_text())
 for b in model['bones']:b['position']=(np.array(b['position'])/[-.075,.075,.075]).tolist()
 records=[];roots=[]
 for row in rows:
  if row['package']!=pkg or row['type']!='MOT' or not row.get('frames') or row.get('maxBone',999)>=len(model['bones']):continue
  raw=(S/row['cache']).read_bytes();assert hashlib.sha256(raw).hexdigest()==row['sha256'];frames,loop,ch=mot.parse(raw,len(model['bones']),allow_duplicate_channels=True);n=max(2,(frames-1)*2+1);b=np.array([mot.sample(model,ch,t) for t in np.linspace(0,frames-1,n)])
  for i in range(1,n):b[i,np.sum(b[i-1,:,3:7]*b[i,:,3:7],1)<0,3:7]*=-1
  times=np.linspace(0,frames-1,n)
  if (0,1) in ch:b[:,0,1]=[mot.evaluate(ch[0,1],t)*.075 for t in times]
  xz=np.array([[-mot.evaluate(ch[0,0],t)*.075 if (0,0) in ch else 0,mot.evaluate(ch[0,2],t)*.075 if (0,2) in ch else 0] for t in times])
  roots.append(dict(name=row['name'],duration=(frames-1)/30,rootXZ=xz.round(6).ravel().tolist()))
  name=row['name'].encode();records.append(struct.pack('<I',len(name))+name+struct.pack('<IfI',n,(frames-1)/30,int(loop))+b.astype('<f4').tobytes());ledger.append(dict(package=pkg,name=row['name'],sourceSHA256=row['sha256']))
 (W/f'{pkg}-all.bytes').write_bytes(struct.pack('<4sIII',b'OPB1',1,len(model['bones'])+1,len(records))+b''.join(records));(W/f'{pkg}-roots.json').write_text(json.dumps(roots,separators=(',',':')));print(pkg,len(records),flush=True)
(W/'motion-provenance.json').write_text(json.dumps(ledger,indent=2))

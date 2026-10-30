"""Append only selected original human MOT curves, retaining existing bank bytes."""
from pathlib import Path
import sys,json,struct,hashlib
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/original-remake'));from export_assets import RES,motion,UNIT
SOURCE=Path('/workspace/work/full-asset-inspection');ROWS=[json.loads(l) for l in (SOURCE/'inventory.jsonl').read_text().splitlines()]
sys.path.insert(0,str(Path(__file__).parent));from pose_audit import bank

def append(package,names):
 p=RES/package;path=p/'Poses.bytes';raw=path.read_bytes();magic,version,bones,count=struct.unpack_from('<4sIII',raw);known=bank(path);model=json.loads((p/'Model.json').read_text())
 for b in model['bones']:b['position']=(np.array(b['position'])/[-UNIT,UNIT,UNIT]).tolist()
 extra=[];ledger=[]
 for name in names:
  if name in known:continue
  row=next(r for r in ROWS if r['group']=='HM' and r['package']==package and r['name']==name and r['type']=='MOT');source=(SOURCE/row['cache']).read_bytes();assert hashlib.sha256(source).hexdigest()==row['sha256']
  frames,loop,ch=motion.parse(source,bones-1,allow_duplicate_channels=True);n=max(2,(frames-1)*2+1);data=np.array([motion.sample(model,ch,t) for t in np.linspace(0,frames-1,n)])
  for i in range(1,n):
   flip=(data[i-1,:,3:7]*data[i,:,3:7]).sum(1)<0;data[i,flip,3:7]*=-1
  label=name.encode();extra.append(struct.pack('<I',len(label))+label+struct.pack('<IfI',n,max(1,frames-1)/30,int(loop))+data.astype('<f4').tobytes());ledger.append(dict(package=package,name=name,sourceSHA256=row['sha256'],frames=frames,sourceLoop=bool(loop)))
 path.write_bytes(struct.pack('<4sIII',magic,version,bones,count+len(extra))+raw[16:]+b''.join(extra));return ledger
if __name__=='__main__':
 records=[]
 for p,names in {'hm09':['hm05_039','hm05_03b','hm05_03c','hm05_03d'],'hm00':['hm00_039','hm00_03b','hm00_03c','hm00_03d'],'hm01':['hme5_039','hm94_03b','hm94_03c','hm94_03d'],'hm05':['hm05_039','hm05_03b','hm05_03c','hm05_03d'],'hm44':['hm44_080']}.items():records+=append(p,names)
 Path(__file__).with_name('motion-provenance.json').write_text(json.dumps(records,indent=2)+'\n');print('Selected original clips appended',len(records))

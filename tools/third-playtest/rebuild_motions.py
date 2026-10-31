"""Preserve original MOT bytes; rebuild selected poses with the native 0x30 channel mapping."""
from pathlib import Path
import sys,json,hashlib,struct,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/original-remake'));from export_assets import RES,motion,UNIT
sys.path.insert(0,str(ROOT/'tools/playtest-followup'));from pose_audit import bank
SOURCE=Path('/workspace/work/full-asset-inspection');ROWS=[json.loads(l) for l in (SOURCE/'inventory.jsonl').read_text().splitlines()]
BASE='045e48e7f07054b81876c58fe5975cb4616c3139'
def append(group,package,names):
 p=RES/package;path=p/'Poses.bytes';raw=path.read_bytes();magic,version,bones,count=struct.unpack_from('<4sIII',raw);known=bank(path);model=json.loads((p/'Model.json').read_text())
 for b in model['bones']:b['position']=(np.asarray(b['position'])/[-UNIT,UNIT,UNIT]).tolist()
 extra=[];report=[]
 for name in names:
  r=next(r for r in ROWS if r['group']==group and r['package']==package and r['name']==name and r['type']=='MOT');d=(SOURCE/r['cache']).read_bytes();assert hashlib.sha256(d).hexdigest()==r['sha256'];frames,loop,ch=motion.parse(d,bones-1,allow_duplicate_channels=True);report.append(dict(package=package,motion=name,sourceSHA256=r['sha256'],frames=frames,loop=bool(loop)))
  if name in known:continue
  n=max(2,(frames-1)*2+1);data=np.asarray([motion.sample(model,ch,t) for t in np.linspace(0,frames-1,n)])
  for i in range(1,n):
   flip=np.sum(data[i-1,:,3:7]*data[i,:,3:7],axis=1)<0;data[i,flip,3:7]*=-1
  label=name.encode();extra.append(struct.pack('<I',len(label))+label+struct.pack('<IfI',n,max(1,frames-1)/30,int(loop))+data.astype('<f4').tobytes())
 path.write_bytes(struct.pack('<4sIII',magic,version,bones,count+len(extra))+raw[16:]+b''.join(extra));return report

def run():
 report=[]
 # Keep earlier source clips but remove the previous cross-rig pose adapters
 # from use. New seated actors use their own native 003 + own arm channels.
 for p,names in {'hm00':['hm00_003','hm00_020'],'hm01':['hm01_003','hm01_020'],'hm05':['hm05_003','hm05_028'],'hm09':['hm05_003','hm05_028'],'hm29':['hm92_003','hm29_020']}.items():report+=append('HM',p,names)
 # Rebuild this bank from original source, including the complete-wheel loop.
 p=RES/'vt6a/Poses.bytes';old=p.read_bytes();_,_,bones,count=struct.unpack_from('<4sIII',old);p.write_bytes(struct.pack('<4sIII',b'OPB1',1,bones,0));report+=append('VT','vt6a',['vt6a_000','vt6a_001','vt6a_010','vt6a_020'])
 m=RES/'vt6a/Model.json';d=json.loads(m.read_text());d['visibleGroups']=[1];m.write_text(json.dumps(d,separators=(',',':')))
 # Distinct original attack actions, not six copies of one provisional clip.
 for p,name in [('em00','em00_131'),('em01','em00_132'),('em11','em65_021')]:report+=append('EM',p,[name])
 Path(__file__).with_name('motion-provenance.json').write_text(json.dumps(report,indent=2)+'\n');print('Native clips prepared',len(report))
if __name__=='__main__':run()

"""Retarget original seated human curves onto verified shared human joints.

Only native joints 0..19 (identical parent hierarchy) are mapped. Target-only
hair/clothing/prop joints retain their native bind transforms. No poses are
hand-authored. This is a Sunward adaptation, not a native koto-playing action.
"""
from pathlib import Path
import sys,json,struct,hashlib,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/original-remake'));from export_assets import RES,motion,UNIT
sys.path.insert(0,str(Path(__file__).parent));from append_motions import append
BASE='262519a7ac762e4e1f5af7f472139cedf87f8bd9';SOURCE=Path('/workspace/work/full-asset-inspection');ROWS=[json.loads(l) for l in (SOURCE/'inventory.jsonl').read_text().splitlines()]

def run():
    provenance=[]
    # Inspection banks never become accidental runtime dependencies.
    for package in ['hm00','hm01','hm05','hm09','hm44']:
        path=RES/package/'Poses.bytes';path.write_bytes(subprocess.check_output(['git','show',BASE+':'+str(path.relative_to(ROOT))],cwd=ROOT))
    source_model=json.loads((RES/'hm09/Model.json').read_text())
    for package in ['hm00','hm01','hm05','hm09']:
        model=json.loads((RES/package/'Model.json').read_text());assert [b['parent'] for b in model['bones'][:20]]==[b['parent'] for b in source_model['bones'][:20]]
        for b in model['bones']:b['position']=(np.array(b['position'])/[-UNIT,UNIT,UNIT]).tolist()
        path=RES/package/'Poses.bytes';raw=path.read_bytes();magic,version,bones,count=struct.unpack_from('<4sIII',raw);extra=[]
        for source_name,target_name in [('hm09_081','venue_seated'),('hm09_0a8','venue_hands')]:
            r=next(r for r in ROWS if r['group']=='HM' and r['package']=='hm09' and r['type']=='MOT' and r['name']==source_name);d=(SOURCE/r['cache']).read_bytes();assert hashlib.sha256(d).hexdigest()==r['sha256'];frames,loop,ch=motion.parse(d,len(source_model['bones']),allow_duplicate_channels=True);ch={k:v for k,v in ch.items() if k[0]<=20}
            n=max(2,(frames-1)*2+1);data=np.array([motion.sample(model,ch,t) for t in np.linspace(0,frames-1,n)])
            for i in range(1,n):
                flip=(data[i-1,:,3:7]*data[i,:,3:7]).sum(1)<0;data[i,flip,3:7]*=-1
            name=target_name.encode();extra.append(struct.pack('<I',len(name))+name+struct.pack('<IfI',n,(frames-1)/30,1)+data.astype('<f4').tobytes());provenance.append(dict(target=package,motion=target_name,source=source_name,sourceSHA256=r['sha256'],sharedNativeJoints=20,adaptation='Original seated/hand curves retargeted; dedicated instrument-playing action not identified'))
        path.write_bytes(struct.pack('<4sIII',magic,version,bones,count+len(extra))+raw[16:]+b''.join(extra))
    provenance+=append('hm44',['hm44_080'])
    # Keep only the native sword demo actually used plus the master's base motions.
    path=RES/'hm08/Poses.bytes';raw=path.read_bytes();magic,version,bones,count=struct.unpack_from('<4sIII',raw);off=16;retained=[];names=[]
    for _ in range(count):
        start=off;n=struct.unpack_from('<I',raw,off)[0];off+=4;name=raw[off:off+n].decode();off+=n;frames=struct.unpack_from('<I',raw,off)[0];off+=12+frames*bones*40
        if name in ['hm08_000','hm08_010','hm08_020','hm08_088','hm08_0a6','hm08_0a8']:retained.append(raw[start:off]);names.append(name)
    path.write_bytes(struct.pack('<4sIII',magic,version,bones,len(retained))+raw[16:16]+b''.join(retained));m=RES/'hm08/Model.json';d=json.loads(m.read_text());d['visibleGroups']=[0,2];m.write_text(json.dumps(d,separators=(',',':')))
    extra=Path(__file__).with_name('extra-assets.json');data=json.loads(extra.read_text());data[0]['visibleGroups']=[0,2];data[0]['motions']=[r for r in data[0]['motions'] if r['name'] in names];extra.write_text(json.dumps(data,indent=2)+'\n')
    Path(__file__).with_name('motion-provenance.json').write_text(json.dumps(provenance,indent=2)+'\n');print('Venue native curve mappings',len(provenance))
if __name__=='__main__':run()

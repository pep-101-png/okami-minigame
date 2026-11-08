from pathlib import Path
import sys,struct,json
R=Path(__file__).resolve().parents[2];D=R/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami';W=Path('/workspace/work/village-complete/sleep')
sys.path[:0]=['/workspace/work/reference-repairs','/workspace/sunward-remaster/tools/playtest-followup'];import assets;from pose_audit import bank;from meta import meta
rows=[]
for name,motion in [('hm00','hm00_039'),('hm05','hm05_039'),('hm68','hm00_039'),('hm0f','hm05_039')]:
 folder=W/name
 if not (folder/'Poses.bytes').exists():assets.export(name,folder,names=[motion])
 a,d,l=bank(folder/'Poses.bytes')[motion];target=D/name/'Poses.bytes';clips=bank(target);clips['village_sleep']=(a,d,l)
 with target.open('wb') as f:
  f.write(struct.pack('<4sIII',b'OPB1',1,a.shape[1],len(clips)))
  for n,(p,duration,loop) in clips.items():
   n=n.encode();f.write(struct.pack('<I',len(n))+n+struct.pack('<IfI',len(p),duration,loop)+p.astype('<f4').tobytes())
 meta(target);rows.append(dict(package=name,sourceMotion=motion,runtimeAlias='village_sleep',samePackage=True))
(R/'tools/village-complete/sleep-provenance.json').write_text(json.dumps(rows,indent=2)+'\n');print('Added four own-package recovered lying/sleep loops')

from pathlib import Path
import sys,json,shutil,subprocess,struct
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools/original-remake'),str(ROOT/'tools/playtest-followup')]
from export_assets import RES,guid,skin
from pose_audit import bank
records=[]
for package,mask,body,idle,motion in [('hm08',[0,2],2,'hm08_000','hm08_088'),('hm2d',[0,2,3],0,'hm00_000','hm2d_080'),('hm2e',[0,2,3,4],0,'hm00_000','hm2e_080')]:
 src=RES/package;dst=RES/('dojo-'+package);dst.mkdir(exist_ok=True)
 model=json.loads((src/'Model.json').read_text());groups=sorted(set(int(p['name'].split('-')[1]) for p in model['parts']));mask=[v for v in mask if v in groups];model['visibleGroups']=mask
 for f in src.iterdir():
  if f.suffix=='.png':shutil.copyfile(f,dst/f.name);guid(dst/f.name)
 (dst/'Model.json').write_text(json.dumps(model,separators=(',',':')));shutil.copyfile(src/'Poses.bytes',dst/'Poses.bytes')
 clips=bank(dst/'Poses.bytes');idle=idle if idle in clips else next(n for n in clips if n.endswith('_000'))
 # Isolate only the two used native clips; no inspection-only actions ship.
 header=(dst/'Poses.bytes').read_bytes()[:12];payload=bytearray(header+struct.pack('<I',2))
 for name in [idle,motion]:
  a,duration,loop=clips[name];n=name.encode();payload.extend(struct.pack('<I',len(n))+n+struct.pack('<IfI',len(a),duration,loop)+a.astype('<f4').tobytes())
 (dst/'Poses.bytes').write_bytes(payload)
 bodyparts=[(i,p) for i,p in enumerate(model['parts']) if int(p['name'].split('-')[1])==body]
 feet=[]
 for i,p in bodyparts:
  bi=np.array(p['boneIndices']).reshape(-1,3);weights=np.array(p['weights']).reshape(-1,3);ix=np.flatnonzero(np.any(np.isin(bi,[14,17])&(weights>.15),axis=1));
  if len(ix):feet.append(dict(part=p['name'],indices=ix.tolist()))
 assert feet,package
 pose=skin(model,clips[idle][0][0]);foot=np.concatenate([pose[next(i for i,p in enumerate(model['parts']) if p['name']==f['part'])][f['indices']] for f in feet]);top=max(pose[i][:,1].max() for i,p in bodyparts);scale=(2.05 if package=='hm08' else 1.85)/(top-foot[:,1].min())
 records.append(dict(package=package,resource='Okami/dojo-'+package,idle=idle,motion=motion,mask=mask,scale=scale,feet=feet))
 for f in [dst,*dst.iterdir()]:
  if not f.name.endswith('.meta'):guid(f)
# The inspection-only extra clips must not change the village Susano bank.
p=RES/'hm08/Poses.bytes';p.write_bytes(subprocess.check_output(['git','show','9646fda:'+str(p.relative_to(ROOT))],cwd=ROOT))
Path(__file__).with_name('training-sources.json').write_text(json.dumps(records,indent=2)+'\n')
print([(r['package'],r['mask'],r['scale'],len(r['feet'])) for r in records])

"""Selected authentic boss-stage layers and one native soldier, from decoded cache."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools/original-remake'),str(ROOT/'tools/playtest-repair'),str(ROOT/'tools/third-playtest')]
from export_assets import A,OUT,RES,guid,UNIT
from native import Mesh
import prepare_assets as prep
from rebuild_motions import append
sys.path.insert(0,'/workspace/work/full-asset-inspection');import visual_catalog as c
sources=[]
for key,source_name,keep in [('dungeon-floor','RM__LY80__Boss_Room',[1,2,3,4,5,6]),('dungeon-altar','__LY82__Boss_Saidan',None),('dungeon-west','M__LY83__Boss_kabeA',None),('dungeon-north','M__LY84__Boss_kabeB',None),('dungeon-east','M__LY85__Boss_kabeC',None),('dungeon-south','M__LY86__Boss_kabeD',None),('dungeon-seal','SO__LY8f__Sort_Boss',None)]:
 r=next(r for r in c.ROWS if r['group']=='ST1' and r['package']=='r10d' and r['type']=='SCR' and r['name']==source_name);assert hashlib.sha256((c.R/r['cache']).read_bytes()).hexdigest()==r['sha256'];parts,_=c.model(r);folder=RES/key;folder.mkdir(exist_ok=True);meshes=[];points=[]
 for i,p in enumerate(parts):
  if keep is not None and i not in keep:continue
  v=p['points']*[-UNIT,UNIT,UNIT];v-=np.array([337.5,15,-97.5]);points.append(v);m=Mesh();m.v=v.tolist();m.c=(p['colors'][:,:3]/128).tolist();uv=p['uv'].copy();uv[:,1]=1-uv[:,1];m.uv=uv.tolist();m.bones=[0]*len(v);m.tri=p['faces'][:,[0,2,1]].tolist();mesh=OUT/'Meshes'/(key+'-'+str(i)+'.asset');m.write(mesh)
  tex=p['texture'];assert tex is not None,(key,i);raw=(c.R/tex['cache']).read_bytes();assert hashlib.sha256(raw).hexdigest()==tex['sha256'];png=folder/(tex['sha256']+'.png');Image.open(c.R/tex['cache']).save(png);mat=OUT/'Materials'/(key+'-'+str(i)+'.mat');text=(OUT/'Materials/vta0-0.mat').read_text().replace(guid(RES/'vta0/Texture-0.png'),guid(png));text=text.replace('Original vta0 paint','Original r10d '+key);text=text.replace(guid(OUT/'Shaders/OriginalPaint.shader'),guid(OUT/'Shaders/OriginalDepthsPaint.shader'));mat.write_text(text);meshes.append(dict(mesh=guid(mesh),material=guid(mat),part=i,textureSHA256=tex['sha256']))
 q=np.concatenate(points);sources.append(dict(package=key,sourcePackage='r10d',sourceName=source_name,sourceSHA256=r['sha256'],sourceCentre=[337.5,15,-97.5],boundsMin=q.min(0).tolist(),boundsMax=q.max(0).tolist(),meshes=meshes))
 for f in [folder,*folder.rglob('*')]:
  if not f.name.endswith('.meta'):guid(f)
# Keep original village NPC resources unchanged; this new soldier is venue-only.
prep.ROWS=[r for r in prep.ROWS if r['package']!='hm2e' or r['type']!='MOT' or r['name'] in ['hm00_000','hm2e_080']]
prep.native('HM','hm2e',all_motions=True)
for f in [RES/'hm2e',*(RES/'hm2e').rglob('*')]:
 if not f.name.endswith('.meta'):guid(f)
for e in prep.LEDGER:
 for f in [*(OUT/'Meshes').glob('hm2e*'),*(OUT/'Materials').glob('hm2e*')]:
  if not f.name.endswith('.meta'):guid(f)
sources+=prep.LEDGER
motions=append('HM','hm08',['hm08_081','hm08_082','hm08_086','hm08_089','hm08_09a','hm08_09b','hm08_09c','hm08_09d','hm08_09f','hm08_0a1','hm08_0a2','hm08_0a5','hm08_0a7'])
Path(__file__).with_name('source-conversions.json').write_text(json.dumps(sources,indent=2)+'\n');Path(__file__).with_name('source-motions.json').write_text(json.dumps(motions,indent=2)+'\n')
print('Converted authentic r10d boss layers and native soldier')

"""Convert the inspected original dojo room and fence geometry, with provenance."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/original-remake'))
from export_assets import A,OUT,RES,guid,UNIT
from native import Mesh
sys.path.insert(0,'/workspace/work/full-asset-inspection');import visual_catalog as catalog

def run():
    result=[]
    for key,name in [('dojo-floor','__LY08__jimen'),('dojo-wall','__LY07__wall'),('dojo-water','__LY01__water'),('dojo-ceiling','__LY06__tenjou'),('dojo-sign','__LY05__kanban'),('dojo-entry-roof','__LY02__kawara'),('farm-fence','__LY04__saku')]:
        row=next(r for r in catalog.ROWS if r['package']=='r10c' and r['type']=='SCR' and r['name']==name)
        parts,_=catalog.model(row);target=RES/key;target.mkdir(exist_ok=True);meshes=[];points=[]
        for i,p in enumerate(parts):
            v=p['points']*[-UNIT,UNIT,UNIT];points.append(v);m=Mesh();m.v=v.tolist();m.c=(p['colors'][:,:3]/128).tolist();uv=p['uv'].copy();uv[:,1]=1-uv[:,1];m.uv=uv.tolist();m.bones=[0]*len(v);m.tri=p['faces'][:,[0,2,1]].tolist();path=OUT/'Meshes'/(key+'-'+str(i)+'.asset');m.write(path)
            texture=p['texture'];assert texture is not None,(key,i)
            raw=(catalog.R/texture['cache']).read_bytes();assert hashlib.sha256(raw).hexdigest()==texture['sha256'];png=target/(texture['sha256']+'.png');Image.open(catalog.R/texture['cache']).save(png)
            material=OUT/'Materials'/(key+'-'+str(i)+'.mat');material.write_text((OUT/'Materials/vta0-0.mat').read_text().replace(guid(RES/'vta0/Texture-0.png'),guid(png)).replace('Original vta0 paint','Original '+key+' paint'))
            meshes.append(dict(mesh=guid(path),material=guid(material),sourceTextureSHA256=texture['sha256']))
        v=np.concatenate(points);result.append(dict(package=key,sourcePackage='r10c',sourceName=name,sourceSHA256=row['sha256'],boundsMin=v.min(0).tolist(),boundsMax=v.max(0).tolist(),meshes=meshes))
    for p in [OUT,*OUT.rglob('*')]:
        if not p.name.endswith('.meta'):guid(p)
    Path(__file__).with_name('stage-conversions.json').write_text(json.dumps(result,indent=2));print('Converted original stage layers',len(result))

if __name__=='__main__':run()

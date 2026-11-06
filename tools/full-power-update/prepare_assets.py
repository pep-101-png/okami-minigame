"""Import verified original ES assets; no replacement models or paintings."""
from pathlib import Path
import sys,shutil,json,numpy as np
R=Path(__file__).resolve().parents[2];A=R/'Sunward-Unity/Assets';D=A/'OkamiRemaster/Original/Resources/Okami';W=Path('/workspace/work/native-power-update');sys.path.insert(0,'/workspace/work/reference-repairs');from meta import meta
rows=[]
for name in ['es3a','es4a','es4b']:
 folder=D/name;folder.mkdir(exist_ok=True);meta(folder)
 for p in (W/name).iterdir():
  if p.suffix not in ['.json','.png','.bytes']:continue
  if name=='es3a' and p.suffix=='.bytes':continue
  dst=folder/p.name;shutil.copyfile(p,dst);meta(dst)
 rows.append(dict(resource='Okami/'+name,source='data_pc/es/'+name+'.dat'))
a=json.loads((D/'es4a/Model.json').read_text());b=json.loads((D/'es4b/Model.json').read_text());assert a['bones']==b['bones'];assert a['parts']==b['parts'];shutil.copyfile(D/'es4a/Poses.bytes',D/'es4b/Poses.bytes');meta(D/'es4b/Poses.bytes')
p=json.loads((D/'pl0d/Model.json').read_text());q=json.loads((D/'es3a/Model.json').read_text());assert p['bones']==q['bones']
# These pieces complement the main model. The long vertical WP20 effect stays hidden.
for name,groups in [('wp20',[0,3]),('wp25',[0,1,2,3,4]),('wp29',[0,1,2,3,4]),('thunder-awakened',[0,1,2,3,4])]:
 p=D/name/'Model.json';j=json.loads(p.read_text());j['visibleGroups']=groups;p.write_text(json.dumps(j,separators=(',',':'))+'\n')
(R/'tools/full-power-update/native-provenance.json').write_text(json.dumps(dict(models=rows,fullPowerRig='ES3A and PL0D have identical original 38-bone parent/bind data',tendrils='ES4A and ES4B have identical original model/skeleton data; both use recovered ES4A et03 motion curves'),indent=2)+'\n')
print('Prepared original full-power body, matching tendril pair and missing weapon components')

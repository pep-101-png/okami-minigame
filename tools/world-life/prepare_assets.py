"""Convert only reviewed original crop/furniture/vegetation media."""
from pathlib import Path
import sys,json,re
ROOT=Path(__file__).resolve().parents[2];sys.path[:0]=[str(ROOT/'tools/playtest-repair'),str(ROOT/'tools/original-remake'),str(ROOT/'tools/third-playtest')]
import importlib.util
spec=importlib.util.spec_from_file_location('existing_preparer',ROOT/'tools/playtest-repair/prepare_assets.py');p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
from rebuild_motions import append
for group,names in [('IT',['it24','it25','it26','it27']),('VT',['vt59','vt64','vt0b','vt13'])]:
 for name in names:
  p.native(group,name)
  folder=p.RES/name;model=json.loads((folder/'Model.json').read_text())
  for t in model['textures']:
   if t.get('vertexOnly'):
    mat=p.OUT/'Materials'/(name+'-'+str(t['index'])+'.mat');mat.write_text(re.sub(r'(m_Texture:) \{fileID: 2800000, guid: [^}]+\}',r'\1 {fileID: 0}',mat.read_text()))
  for f in [folder,*folder.rglob('*'),*(p.OUT/'Meshes').glob(name+'-*'),*(p.OUT/'Materials').glob(name+'-*')]:
   if not f.name.endswith('.meta'):p.guid(f)
# Own original village seated and work gesture, no rig adaptation.
motions=append('HM','hm00',['hm00_003'])
Path(__file__).with_name('asset-sources.json').write_text(json.dumps(p.LEDGER,indent=2)+'\n');Path(__file__).with_name('motion-sources.json').write_text(json.dumps(motions,indent=2)+'\n')

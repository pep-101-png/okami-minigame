"""Convert only already-decoded, visually identified original furniture/decor."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/playtest-repair'));import prepare_assets as p
for package in ['vt90','vt9a','vt70']:p.native('VT',package)
# Native untextured vertex pigment must not create a nonexistent Texture-255.
import re
for package in ['vt90','vt9a','vt70']:
 model=json.loads((p.RES/package/'Model.json').read_text())
 for tex in model['textures']:
  if tex.get('vertexOnly'):
   mat=p.OUT/'Materials'/(package+'-'+str(tex['index'])+'.mat');raw=mat.read_text();mat.write_text(re.sub(r'(m_Texture:) \{fileID: 2800000, guid: [^}]+\}',r'\1 {fileID: 0}',raw))
 for meta in (p.RES/package).glob('*.png.meta'):
  if not meta.with_suffix('').exists():meta.unlink()
for package in ['vt90','vt9a','vt70']:
 folder=p.RES/package
 for f in [folder,*folder.rglob('*')]:
  if not f.name.endswith('.meta'):p.guid(f)
for e in p.LEDGER:
 for part in e['meshes']:
  for path in [p.OUT/'Meshes',p.OUT/'Materials']:
   for f in path.iterdir():
    if not f.name.endswith('.meta') and (e['package'] in f.name):p.guid(f)
Path(__file__).with_name('furniture-sources.json').write_text(json.dumps(p.LEDGER,indent=2)+'\n')

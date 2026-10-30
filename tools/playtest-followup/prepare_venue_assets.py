import sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/playtest-repair'));import prepare_assets as p
from export_assets import guid,OUT
# Select a bounded subset of original dojo-master motions for inspection/use.
allowed={'000','010','020','081','082','086','088','089','09a','09b','09c','09d','09f','0a1','0a2','0a5','0a6','0a7','0a8'}
p.ROWS=[r for r in p.ROWS if not(r['group']=='HM' and r['package']=='hm08' and r['type']=='MOT') or r['name'].split('_')[-1] in allowed]
p.native('HM','hm08',all_motions=True)
for f in [OUT,*OUT.rglob('*')]:
 if not f.name.endswith('.meta'):guid(f)
Path(__file__).with_name('extra-assets.json').write_text(json.dumps(p.LEDGER,indent=2)+'\n')

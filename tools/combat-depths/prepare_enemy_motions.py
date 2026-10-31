"""Inspect each enemy's own variant motions; do not infer identity from shared numbers."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/third-playtest'));from rebuild_motions import append
plans={'em00':['em00_080','em00_081','em00_082'],'em01':['em00_180','em00_181','em00_182'],'em02':['em00_150','em00_151','em00_152','em00_153'],'em03':['em00_050','em00_051','em00_052'],'em04':['em00_190','em00_191','em00_193','em00_194'],'em11':['em65_022','em65_023','em65_024']}
ledger=[]
for p,names in plans.items():ledger+=append('EM',p,names)
Path(__file__).with_name('enemy-motion-sources.json').write_text(json.dumps(ledger,indent=2)+'\n');print('Prepared',len(ledger),'own-archive variant clips')
if __name__=='__main__':
 sys.path.insert(0,str(ROOT/'tools/playtest-followup'));from pose_audit import render
 from PIL import Image
 out=Path('/workspace/work/combat-depths')
 for p,names in plans.items():
  im=Image.new('RGB',(240*4,190*len(names)))
  for i,n in enumerate(names):
   for j,phase in enumerate([.05,.3,.6,.85]):im.paste(render(ROOT/('Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami/'+p),n,phase),(j*240,i*190))
  im.save(out/(p+'-native-actions.jpg'))

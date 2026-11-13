from pathlib import Path
import sys,numpy as np
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parents[2];W=Path('/workspace/work/celestial-guardians');sys.path.insert(0,str(R/'tools/trailer30'));import native_renderer as nr
nr.Renderer.load_scene=lambda self:None;r=nr.Renderer(480,400)
for resource,clips in [('guardian-sentinel',['em60_001','em60_010','em60_030','em60_031','em60_035','em60_043']),('guardian-eclipse',['em62_000','em62_010','em62_030','em62_031','em62_032','em62_033','em62_040','em62_050'])]:
 n=nr.Native(r,'Okami/'+resource,2.1 if resource=='guardian-sentinel' else .34);n.visible=True;r.actors=[n];fox=None
 if resource=='guardian-eclipse':fox=nr.Native(r,'Okami/guardian-fox',.34);fox.visible=True;r.actors.append(fox)
 sheet=Image.new('RGB',(480*5,400*len(clips)),'white');d=ImageDraw.Draw(sheet)
 for row,clip in enumerate(clips):
  for col,phase in enumerate([0,.25,.5,.75,.98]):
   n.update(clip,n.bank[clip][1]*phase,loop=False)
   if fox:fox.update(clip.replace('em62','em61'),fox.bank[clip.replace('em62','em61')][1]*phase,loop=False)
   r.begin(np.array([6,4,7]),[0,1.5,-.5],0,0,'garden',42);r.geometry();sheet.paste(Image.frombytes('RGB',(480,400),r.end()).transpose(Image.Transpose.FLIP_TOP_BOTTOM),(col*480,row*400));d.text((col*480+4,row*400+4),f'{clip} {phase}',fill='black')
 sheet.resize((1500,int(sheet.height*1500/sheet.width))).save(W/(resource+'-motions.jpg'));print(resource,flush=True)

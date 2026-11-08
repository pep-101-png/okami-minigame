from pathlib import Path
import sys,re,json,numpy as np
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/trailer30'));import native_renderer as nr
from PIL import Image,ImageDraw
W=Path('/workspace/work/imp-rework');nr.Renderer.load_scene=lambda self:None;r=nr.Renderer(480,400)
for idx,role in enumerate(['wisp','reed','ranged','heavy','elite']):
 text=(R/f'Sunward-Unity/Assets/Sunward/Generated/Enemy-{role}.prefab').read_text();scale=float(re.search('  modelScale: (.*)',text)[1]);off=[float(x) for x in re.search(r'  modelOffset: \{x: (.*), y: (.*), z: (.*)\}',text).groups()];n=nr.Native(r,f'Okami/em0{idx}',scale,off);n.visible=True;r.actors=[n];clips=list(n.bank);sheet=Image.new('RGB',(480*6,400*len(clips)),'white');d=ImageDraw.Draw(sheet)
 for row,clip in enumerate(clips):
  for col,phase in enumerate([0,.18,.36,.54,.72,.94]):
   n.update(clip,n.bank[clip][1]*phase,loop=False);r.begin(np.array([3,2.7,4]),[0,.9,0],0,0,'village',43);r.geometry();im=Image.frombytes('RGB',(480,400),r.end()).transpose(Image.Transpose.FLIP_TOP_BOTTOM);sheet.paste(im,(col*480,row*400));d.text((col*480+8,row*400+8),f'{role} {clip} {phase}',fill='black')
 sheet.resize((1800,int(sheet.height*1800/sheet.width))).save(W/f'{role}-clips.jpg')
 # All groups independently, same idle pose, to find props versus duplicate bodies.
 gs=sorted({g for g,_ in n.parts});sheet=Image.new('RGB',(480*len(gs),400),'white');d=ImageDraw.Draw(sheet)
 for col,g in enumerate(gs):
  n.groups={g};n.update('em00_000',.2);r.begin(np.array([3,2.7,4]),[0,.9,0],0,0,'village',43);r.geometry();sheet.paste(Image.frombytes('RGB',(480,400),r.end()).transpose(Image.Transpose.FLIP_TOP_BOTTOM),(col*480,0));d.text((col*480+5,5),f'{role} group{g}',fill='black')
 sheet.save(W/f'{role}-groups.jpg');print(role,flush=True);n.visible=False

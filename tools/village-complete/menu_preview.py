"""Offline native-art layout diagnostic matching MemoryMirrorMenu's 960x640 canvas."""
from pathlib import Path
from PIL import Image,ImageChops
import json
R=Path(__file__).resolve().parents[2];D=R/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami';U=D/'UI';atlas=Image.open(U/'MessageGlyphs.png').convert('RGBA');glyphs={g['code']:g for g in json.loads((U/'MessageGlyphs.json').read_text())['glyphs']};out=Image.new('RGBA',(960,640))
def draw(path,rect,tint=(1,1,1,1)):
 im=Image.open(path).convert('RGBA').resize((round(rect[2]),round(rect[3])));color=Image.new('RGBA',im.size,tuple(round(c*255) for c in tint));im=ImageChops.multiply(im,color);out.alpha_composite(im,(round(rect[0]),round(rect[1])))
def paper(rect,tint):
 x,y,w,h=rect;draw(U/'MenuScrollBody.png',rect,tint);draw(U/'MenuScrollRoll.png',(x-7,y,14,h));draw(U/'MenuScrollRoll.png',(x+w-7,y,14,h))
def text(s,x,y,em,color=(.1,.12,.055,1)):
 for c in s:
  g=glyphs.get(ord(c),glyphs.get(ord('?')));assert g or c==' ',repr(c)
  if c!=' ':
   im=atlas.crop((g['x'],g['y'],g['x']+g['width'],g['y']+g['height']));im=im.resize((max(1,round(g['width']*em/160)),max(1,round(g['height']*em/160))));im=ImageChops.multiply(im,Image.new('RGBA',im.size,tuple(round(t*255) for t in color)));out.alpha_composite(im,(round(x),round(y+g['top']*em/160)))
  x+=(65 if c==' ' else g['advance'])*em/160
x,y=30,20;draw(U/'MenuPaper.png',(0,0,960,640),(.78,.76,.65,1));paper((x+25,y+20,360,56),(.88,.88,.74,1));text('Save',x+155,y+31,34)
for i in range(4):
 rx,ry=x+65,y+100+i*67;paper((rx,ry,780,59),(.75,.84,.58,1) if i==0 else (.91,.87,.73,1));text(str(i+1)+'   '+('Windflower Village' if i==0 else 'Empty memory'),rx+15,ry+12,28)
 if i==0:text('→',rx-37,ry+10,32,(.25,.42,.08,1));text('2 hr. 58 min. 45 sec.',rx+465,ry+15,24)
paper((x+45,y+382,820,132),(.68,.82,.43,1));text('Life 170    Ink 110    Level 15',x+72,y+399,28);text('450 coins    15 instruments    3 Crimson Helm victories',x+72,y+443,21)
for i,wp in enumerate(['wp24','wp29','wp2e']):draw(D/'WeaponPortraits'/(wp+'.png'),(x+72+i*62,y+473,55,35))
for s,rx,w in [('Load →',65,220),('Inscribe memory',325,310),('Return',700,150)]:text(s,x+rx,y+535,28)
p=Path('/workspace/work/village-complete/previews/save-menu.png');out.convert('RGB').save(p);print(p)

from pathlib import Path
from PIL import Image,ImageDraw
R=Path(__file__).resolve().parent
for folder in sorted((R/'review/final-renders').iterdir()):
 files=sorted(folder.glob('*.png'))
 if not files:continue
 if folder.name=='Showcase':
  for start in range(0,len(files),8):
   chunk=files[start:start+8];im=Image.new('RGB',(1600,650),'#e6e3d7');d=ImageDraw.Draw(im)
   for j,p in enumerate(chunk):
    thumb=Image.open(p).convert('RGB');thumb.thumbnail((400,300));x=j%4*400;y=j//4*325;im.paste(thumb,(x,y));d.text((x+8,y+303),'Showcase frame '+p.stem,fill='#252421')
   im.save(R/f'review/Showcase-{start//8+1}.jpg',quality=92)
  continue
 im=Image.new('RGB',(1600,325*((len(files)+3)//4)),'#e6e3d7');d=ImageDraw.Draw(im)
 for j,p in enumerate(files):
  thumb=Image.open(p).convert('RGB');thumb.thumbnail((400,300));x=j%4*400;y=j//4*325;im.paste(thumb,(x,y));d.text((x+8,y+303),folder.name+' '+p.stem,fill='#252421')
 im.save(R/f'review/{folder.name}.jpg',quality=92)

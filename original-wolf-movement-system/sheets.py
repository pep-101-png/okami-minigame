from pathlib import Path
from PIL import Image,ImageDraw
import json
R=Path(__file__).resolve().parent
names=['Walk_Turn_L','Walk_Turn_R','Jog_Turn_L','Jog_Turn_R','Sprint_Turn_L','Sprint_Turn_R','Idle_Turn_L90','Idle_Turn_R90','Idle_Natural']
def sheet(files,out,labels=None):
 im=Image.new('RGB',(1600,310*((len(files)+3)//4)),'#e4e1d7');d=ImageDraw.Draw(im)
 for j,p in enumerate(files):
  thumb=Image.open(p).convert('RGB');thumb.thumbnail((400,287));x=j%4*400;y=j//4*310;im.paste(thumb,(x,y));d.text((x+8,y+290),labels[j]if labels else p.stem,fill='#272321')
 im.save(out,quality=92)
for name in names:
 files=sorted((R/f'review/renders/{name}').glob('*.png'));assert len(files)==(8 if'Turn_'in name and not name.startswith('Idle')else 5 if'90'in name else 4),(name,len(files));sheet(files,R/f'review/{name}.jpg')
if(R/'review/showcase-frames.json').exists():
 rows=json.load(open(R/'review/showcase-frames.json'))
 for start in range(0,len(rows),8):
  chunk=rows[start:start+8];sheet([R/f'review/renders/ShowcaseFinal/{row["frame"]:04}.png'for row in chunk],R/f'review/Showcase-{start//8+1}.jpg',[str(row['frame'])+' '+row['label']for row in chunk])
print('SHEETS_READY')

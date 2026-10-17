from pathlib import Path
from PIL import Image,ImageDraw
import subprocess
R=Path(__file__).resolve().parent;root=R/'review/renders/Sprint_Fluid'
for view in ['side','neck','front']:
 files=sorted((root/view).glob('*.png'));assert len(files)==(8 if view=='front'else 32)
 for start in range(0,len(files),8):
  sheet=Image.new('RGB',(1600,592),'#e4e1d7');d=ImageDraw.Draw(sheet)
  for j,p in enumerate(files[start:start+8]):
   im=Image.open(p).convert('RGB');im.thumbnail((400,276));x=j%4*400;y=j//4*296;sheet.paste(im,(x,y));d.text((x+8,y+279),f'{view} frame {int(p.stem):02}',fill='black')
  sheet.save(R/f'review/{view}-{start//8+1}.jpg',quality=92)
 if view!='front':
  subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','60','-i',str(root/view/'%03d.png'),'-c:v','libx264','-threads','2','-pix_fmt','yuv420p','-crf','18',str(R/f'review/{view}-cycle.mp4')],check=True)
  subprocess.run(['ffmpeg','-y','-loglevel','error','-stream_loop','9','-i',str(R/f'review/{view}-cycle.mp4'),'-c','copy','-movflags','+faststart',str(R/f'review/Sprint-{view}.mp4')],check=True)
# Identical camera/lighting comparisons.
for view in ['side','neck']:
 for f in [1,9,17,25]:
  im=Image.new('RGB',(1800,650),'#e4e1d7');d=ImageDraw.Draw(im)
  for j,name in enumerate(['Sprint_Polished','Sprint_Fluid']):
   src=Image.open(R/f'review/renders/{name}/{view}/{f:03}.png').convert('RGB');im.paste(src,(j*900,24));d.text((j*900+12,7),name,fill='black')
  im.save(R/f'review/compare-{view}-{f:02}.jpg',quality=92)
print('MEDIA_READY')

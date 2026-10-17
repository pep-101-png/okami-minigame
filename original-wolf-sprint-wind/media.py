from PIL import Image,ImageDraw
from pathlib import Path
import subprocess,json
R=Path(__file__).resolve().parent;src=R/'review/final2/Sprint_Polished'
for view in ['side','rear','neck']:
 files=sorted((src/view).glob('*.png'));assert len(files)==32,(view,len(files))
 for start in range(0,32,8):
  sheet=Image.new('RGB',(1600,572),'#e4e1d7');d=ImageDraw.Draw(sheet)
  for j,p in enumerate(files[start:start+8]):
   im=Image.open(p).convert('RGB');im.thumbnail((400,267));x=(j%4)*400;y=(j//4)*286;sheet.paste(im,(x,y));d.text((x+10,y+269),f'{view} / frame {int(p.stem):02}',fill='#272321')
  sheet.save(R/f'review/{view}-{start//8+1}.jpg',quality=91)
 subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','60','-i',str(src/view/'%03d.png'),'-c:v','libx264','-pix_fmt','yuv420p','-crf','18',str(R/f'review/{view}-cycle.mp4')],check=True)
 subprocess.run(['ffmpeg','-y','-loglevel','error','-stream_loop','9','-i',str(R/f'review/{view}-cycle.mp4'),'-c','copy','-movflags','+faststart',str(R/f'review/Sprint-{view}.mp4')],check=True)
print('MEDIA_READY')

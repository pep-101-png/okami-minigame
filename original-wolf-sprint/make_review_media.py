from pathlib import Path
from PIL import Image,ImageDraw
import subprocess
ROOT=Path(__file__).resolve().parent;R=ROOT/'review'
for view in ['side','front','rear']:
 files=sorted((R/'final5'/view).glob('*.png'));assert len(files)==32,(view,len(files))
 batchsize=8 if view=='side' else 16
 for batch in range(32//batchsize):
  out=Image.new('RGB',(1680,324*(batchsize//4)),'#e8dfd1');d=ImageDraw.Draw(out)
  for j,f in enumerate(files[batch*batchsize:(batch+1)*batchsize]):
   im=Image.open(f);im.thumbnail((420,300));x=j%4*420;y=j//4*324;out.paste(im,(x,y));d.text((x+8,y+303),f'Sprint / {view} / frame {int(f.stem)}',fill='black')
  out.save(R/f'sprint-{view}-{batch+1}.jpg',quality=94)
 cycle=f'/tmp/sprint-{view}-cycle.mp4'
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-framerate','60','-start_number','1','-i',str(R/'final5'/view/'%03d.png'),'-frames:v','32','-c:v','libx264','-crf','18','-pix_fmt','yuv420p',cycle],check=True)
 subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-stream_loop','9','-i',cycle,'-c','copy',str(R/f'Sprint-{view}.mp4')],check=True)
files=sorted((R/'final5/hip').glob('*.png'))+sorted((R/'shoulder').glob('*.png'));assert len(files)==11
out=Image.new('RGB',(1920,1320),'#e8dfd1');d=ImageDraw.Draw(out)
for j,f in enumerate(files):
 im=Image.open(f);im.thumbnail((480,410));x=j%4*480;y=j//4*440;out.paste(im,(x,y));d.text((x+8,y+413),f'{f.parent.name} / frame {int(f.stem)}',fill='black')
out.save(R/'joint-closeups.jpg',quality=94)
print('REVIEW_MEDIA_COMPLETE')

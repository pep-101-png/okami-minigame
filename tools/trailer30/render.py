from pathlib import Path
import argparse,sys,os,time,subprocess,json
from PIL import Image
from native_renderer import *
from director import Director
from titles import Titles
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--preview',action='store_true');p.add_argument('--width',type=int,default=1920);p.add_argument('--height',type=int,default=1080);p.add_argument('--frames',type=int,default=1800);p.add_argument('--start',type=int,default=0);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
r=Renderer(a.width,a.height);d=Director(r,a.out);r.batch_static(d.lanterns,d.stand);titles=Titles(r,a.out)
if a.preview:
 for i in range(len(d.names)):
  t=(d.cuts[i]+d.cuts[i+1])/2;b,shot=d.frame(t,read=False);titles.draw(t,shot,d.cuts[i],d.cuts[i+1]);b=r.end();im=Image.frombytes('RGB',(a.width,a.height),b).transpose(Image.Transpose.FLIP_TOP_BOTTOM);im.save(a.out/(shot+'.png'));print('PREVIEW',shot,flush=True)
else:
 cmd=['ffmpeg','-v','warning','-y','-f','rawvideo','-pixel_format','rgb24','-video_size',str(a.width)+'x'+str(a.height),'-framerate','60','-i','-','-vf','vflip','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-threads','2','-movflags','+faststart',str(a.out/'picture.mp4')];process=subprocess.Popen(cmd,stdin=subprocess.PIPE);beg=time.monotonic()
 for frame in range(a.start,a.start+a.frames):
  t=frame/60;b,shot=d.frame(t,read=False);i=d.names.index(shot);titles.draw(t,shot,d.cuts[i],d.cuts[i+1]);b=r.end();process.stdin.write(b)
  if frame%60==0:print('FRAME',frame,shot,'elapsed',round(time.monotonic()-beg,1),flush=True)
 process.stdin.close();assert process.wait()==0
 (a.out/'render-receipt.json').write_text(json.dumps(dict(type='Standalone offline native-asset cinematic, not recorded Unity gameplay',fps=60,frames=a.frames,width=a.width,height=a.height,duration=a.frames/60,cuts=d.cuts,shots=d.names,renderer=r.ctx.info['GL_RENDERER'],secondsElapsed=round(time.monotonic()-beg,1)),indent=2))

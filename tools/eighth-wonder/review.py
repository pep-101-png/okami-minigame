from pathlib import Path
import sys,numpy as np
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/trailer30'));import native_renderer as nr
W=Path('/workspace/work/eighth-wonder');nr.Renderer.load_scene=lambda self:None;r=nr.Renderer(900,750)
body=nr.Native(r,'NativePlayer/pl00');body.visible=True;weapon=nr.Native(r,'Okami/wp28');weapon.visible=True
for mode,groups in [('current',{1,2}),('metal',{1,2,3,4}),('all',{0,1,2,3,4})]:
 weapon.groups=groups
 for clip in ['wp28_000','wp28_001']:
  for t in [.1,2.0]:
   body.update('pl00_000',.3,nr.matrix(yaw=90));weapon.update(clip,t,body.dorsal());r.actors=[body,weapon];r.begin(np.array([3,3.5,3.5]),[0,.9,0],t,0,'village',43);r.geometry();nr.Image.frombytes('RGB',(900,750),r.end()).transpose(nr.Image.Transpose.FLIP_TOP_BOTTOM).save(W/f'{mode}-{clip}-{t}.png')
print('Compared original sections and native idle poses on the native back socket.')
weapon.groups={1,2,3,4}
from PIL import Image,ImageDraw
canvas=Image.new('RGB',(1800,1050));draw=ImageDraw.Draw(canvas)
for row,weaponclip in enumerate(['wp28_000','wp28_001','wp28_002']):
 for col,phase in enumerate([0,.23,.48,.72,.97]):
  clip='pl00_520';duration=body.bank[clip][1];body.update(clip,duration*phase,nr.matrix(yaw=90),loop=False);weapon.update(weaponclip,phase,body.dorsal());r.actors=[body,weapon];r.begin(np.array([3,3,3.5]),[0,.8,0],phase,0,'village',43);r.geometry();frame=nr.Image.frombytes('RGB',(900,750),r.end()).transpose(nr.Image.Transpose.FLIP_TOP_BOTTOM).resize((360,350));canvas.paste(frame,(col*360,row*350));draw.text((col*360+8,row*350+8),weaponclip+' / '+str(phase),fill='black')
canvas.save(W/'attack-carriers.png')
# A short actual-pose moving sequence for internal review; never placed in Assets.
import subprocess
movie=W/'motion';movie.mkdir(exist_ok=True);weapon.groups={1,2,3,4}
for i in range(240):
 t=i/60;clip='pl00_000' if t<1.5 else 'pl00_520';phase=t if t<1.5 else (t-1.5)%body.bank[clip][1];body.update(clip,phase,nr.matrix(yaw=90));weapon.update('wp28_000',t,body.dorsal());r.actors=[body,weapon];r.begin(np.array([3,3.5,3.5]),[0,.9,0],t,0,'village',43);r.geometry();nr.Image.frombytes('RGB',(900,750),r.end()).transpose(nr.Image.Transpose.FLIP_TOP_BOTTOM).save(movie/f'{i:04d}.png')
subprocess.run(['ffmpeg','-v','error','-y','-framerate','60','-i',str(movie/'%04d.png'),'-frames:v','240','-c:v','libx264','-crf','18','-pix_fmt','yuv420p',str(W/'Eighth-Wonder-Offline-Review.mp4')],check=True)

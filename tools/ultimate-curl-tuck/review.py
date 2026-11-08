"""Actual captured ultimate with a side-view inset to inspect the chosen forward rolls."""
from pathlib import Path
import sys,json,hashlib,numpy as np,subprocess,wave
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[2];W=Path('/workspace/work/solar-ultimate');OUT=Path('/workspace/work/ultimate-curl-tuck')
# Reuse the existing renderer's source/capture checks, exact original alpha/additive
# effects and actual recorded camera. Do not substitute a second animation.
source=(R/'tools/solar-ultimate/review.py').read_text();exec(source[:source.index("if '--stills'")])
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
def compose(f):
 im=frame(f,'ultimate');centre=np.array(f['centre'])-[35,0,0];heading=nr.rotation(f['rotation']);eye=centre+heading@np.array([4.5,.8,0]);r.actors=[body];saved=r.static;r.static=[];r.begin(eye,centre,f['t'],0,'village',32);r.framebuffer.clear(.94,.92,.86,1,depth=1);r.geometry();detail=Image.frombytes('RGB',(1280,720),r.end()).transpose(Image.Transpose.FLIP_TOP_BOTTOM).resize((480,270),Image.Resampling.LANCZOS);r.static=saved;im.paste(detail,(785,425));d=ImageDraw.Draw(im);label='Approved spiral rise' if f['t']<2.1 else '3 · Folded curl / forward roll' if f['t']<3.05 else '3 → 2 · continuing forward' if f['t']<3.65 else '2 · Airborne tuck / forward roll' if f['t']<4.65 else 'Release';d.rectangle((785,395,1265,425),fill='#172126');d.text((795,400),label,font=font,fill='white');return im
out=OUT/'Shiranui-Curl-to-Tuck-Offline-Preview.mp4';silent=OUT/'silent.mp4'
pipe=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','30','-i','-','-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p',str(silent)],stdin=subprocess.PIPE)
for i,f in enumerate(ud['frames']):
 im=compose(f);pipe.stdin.write(im.tobytes())
 if i in [60,75,85,95,105,115,125,135]:im.save(OUT/f'pose-{i}.jpg')
 if i%90==0:print('frames',i,flush=True)
pipe.stdin.close();assert pipe.wait()==0
# Use the unchanged ultimate portion of the full review's exact audio scheduling.
subprocess.run(['ffmpeg','-v','error','-y','-i',str(silent),'-ss','1.8','-i',str(W/'Solar-Ultimate-and-Sword-Offline-Review.mp4'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',str(out)],check=True)
for t in [2.5,2.85,3.2,3.5,3.85,4.25]:subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(out),'-frames:v','1',str(OUT/f'encoded-{t}.jpg')],check=True)
(OUT/'review-receipt.json').write_text(json.dumps(dict(scope='Offline original-asset render of actual C# pose/camera/effect outputs, with recorded side-view inset; not Unity Play Mode',runtimeReceipt=hashlib.sha256((W/'runtime-receipt.json').read_bytes()).hexdigest(),sha256=hashlib.sha256(out.read_bytes()).hexdigest()),indent=2));print(out,flush=True)

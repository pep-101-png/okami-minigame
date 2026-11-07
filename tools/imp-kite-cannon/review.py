"""Render actual captured C# poses, shell paths and exact painted effect meshes."""
from pathlib import Path
import sys,json,numpy as np,subprocess,hashlib,wave
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/trailer30'));import native_renderer as nr
from PIL import Image,ImageDraw,ImageFont
W=Path('/workspace/work/imp-kite-cannon');D=R/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami'
receipt=json.loads((W/'runtime-receipt.json').read_text())
for name,sha in receipt['sourceHashes'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==sha,'Stale source: '+name
# Source sprite shader blends continuously; don't use the inspection renderer's cutout threshold.
nr.FRAG=nr.FRAG.replace('if(c.a<.22)discard;','if(mode==5){out_color=vec4(c.rgb*tint,c.a*opacity);return;}if(c.a<.22)discard;')
nr.Renderer.load_scene=lambda self:None;r=nr.Renderer(640,480);r.static=[]
floor=nr.Draw(r,[[-15,0,-15],[-15,0,15],[15,0,15],[15,0,-15]],[[0,1,2],[0,2,3]],[[0,0],[0,7],[7,7],[7,0]],np.ones((4,4)),R/'Sunward-Unity/Assets/OkamiRemaster/Original/Textures/Kamiki-earth.png',twosided=True);r.static=[floor]
roles=['wisp','reed','ranged','heavy','elite'];names=['Green Imp · lute','Purple/Red Imp · kite','Yellow Imp · barrel cannon','Blue Imp · flute','Black Imp · drum'];datasets=[json.loads((W/(role+'-runtime.json')).read_text()) for role in roles];actors=[nr.Native(r,d['resource']) for d in datasets];hero=nr.Native(r,'NativePlayer/pl00');hero.visible=True
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
def render(k,f,angle=None):
 n=actors[k];n.scale=f['modelScale']*f['scale'];n.offset=np.array(f['offset'])*f['scale'];n.visible=f['visible'];rot=np.eye(4);rot[:3,:3]=nr.rotation(f['rotation']);rot[:3,3]=np.array(f['position'])-[35,0,0];n.update(f['clip'],f['sourceTime'],rot,False,pose=np.array(f['pose']))
 hero.visible=angle is None;hero.update('pl00_000',f['t'],nr.matrix(np.array(f['hero'])-[35,0,0],180));r.actors=[n,hero]
 eye=np.array(f['eye'])-[35,0,0];target=np.array(f['target'])-[35,0,0]
 if angle is not None:target=rot[:3,3]+[0,1.1,0];eye=target+np.array(angle)
 r.begin(eye,target,f['t'],0,'village',50 if angle is None else 43);r.geometry();r.framebuffer.depth_mask=False
 for p in f['paint']:
  ob=nr.Draw(r,np.array(p['vertices'])+np.array(p['position'])-[35,0,0],np.array(p['triangles']).reshape(-1,3),p['uv'],p['colors'],D/'Effects'/(p['sprite']+'.png'),mode=5,twosided=True);ob.render();ob.vao.release();ob.vbo.release();ob.ibo.release()
 r.framebuffer.depth_mask=True
 im=Image.frombytes('RGB',(640,480),r.end()).transpose(Image.Transpose.FLIP_TOP_BOTTOM);n.visible=False;return im
output=W/'Imp-Kite-Cannon-Offline-Review.mp4';silent=W/'silent-review.mp4'
if '--reuse-silent' not in sys.argv:
 pipe=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1920x960','-r','30','-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(silent)],stdin=subprocess.PIPE)
 for i in range(720):
  sheet=Image.new('RGB',(1920,960),'#20282e');draw=ImageDraw.Draw(sheet)
  for k,d in enumerate(datasets):
   f=d['frames'][i];p=(k%3*640,k//3*480);sheet.paste(render(k,f),p);draw.rectangle([p[0],p[1],p[0]+640,p[1]+58],fill='#162128');draw.text((p[0]+12,p[1]+7),names[k],font=font,fill='white');draw.text((p[0]+12,p[1]+32),f"{f['state']} · {f['clip']} · {f['move']} {'FROZEN' if f['frozen'] else ''}",font=small,fill='#b9dfd2')
  draw.text((1300,525),'IMP REWORK · KITE & CANNON',font=font,fill='white');draw.multiline_text((1300,565),'Actual captured C# driver poses\nExact shell paths and effect meshes\nOriginal game models, paint, sound\n\nAudio focus: Yellow cannon imp\n0–14s: attack variations / shots\n15s: freeze · 17.2s: hit reaction\n22s: defeat / cleanup\n\nOffline native-asset render\nAPI doubles; flat test floor\nNot Unity Play Mode footage',font=font,fill='#c0d0d4',spacing=8);draw.text((1300,915),f'{i/30:.2f}s / 24s · 30 fps',font=font,fill='white');pipe.stdin.write(sheet.tobytes())
  if i%120==0:print('review frames',i,flush=True)
 pipe.stdin.close();assert pipe.wait()==0
# Use only the actual Yellow source scheduler events, with recorded pitch, gain and linear falloff.
mix=np.zeros(24*48000,dtype=np.float64);events=datasets[2]['audio'];print('Audio event example',events[:1],flush=True)
for e in events:
 path=D.parent/(e['cue']+'.wav')
 with wave.open(str(path),'rb') as w:rate=w.getframerate();assert w.getsampwidth()==2;pcm=np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(float)/32768
 pitch=e.get('pitch',1);idx=np.arange(int(len(pcm)*48000/(rate*pitch)))*rate*pitch/48000;sample=np.interp(idx,np.arange(len(pcm)),pcm)
 distance=np.linalg.norm(np.array(e['position'])-e['listener']);falloff=1-np.clip((distance-e['minDistance'])/(e['range']-e['minDistance']),0,1);start=round(e['time']*48000);end=min(len(mix),start+len(sample))
 if end>start:mix[start:end]+=sample[:end-start]*e['gain']*falloff
peak=float(np.max(np.abs(mix)));mix*=min(1,.94/max(peak,1e-9))
with wave.open(str(W/'cannon-scheduled-audio.wav'),'wb') as w:w.setnchannels(1);w.setsampwidth(2);w.setframerate(48000);w.writeframes((mix*32767).astype('<i2').tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',str(silent),'-i',str(W/'cannon-scheduled-audio.wav'),'-c:v','copy','-c:a','aac','-b:a','160k','-shortest','-movflags','+faststart',str(output)],check=True)
for sec in [.7,2.4,3.6,6.2,8.8,12.5,15.4,17.3,22.5,23.7]:subprocess.run(['ffmpeg','-v','error','-y','-ss',str(sec),'-i',str(output),'-frames:v','1',str(W/f'encoded-{sec}.jpg')],check=True)
for k,d in enumerate(datasets):
 for move in d['actions']:
  chosen=[f for f in d['frames'] if f['move']==move and f['state'] in ['windup','aim','strike','recover']];chosen=[chosen[i] for i in np.linspace(0,len(chosen)-1,12).astype(int)];canvas=Image.new('RGB',(1920,1440));draw=ImageDraw.Draw(canvas)
  for j,f in enumerate(chosen):
   p=(j%4*480,j//4*480);canvas.paste(render(k,f,[-4.5,2.7,5.5]).resize((480,480)),p);draw.text((p[0]+6,p[1]+6),f"{f['t']:.2f} {f['state']} {f['clip']}",font=small,fill='black')
  canvas.save(W/f'{roles[k]}-{move}-reviewed.jpg')
# Kite multiview includes movement, each attack, reaction and held defeat.
d=datasets[1];chosen=[next(f for f in d['frames'] if f['state']==state) for state in ['approach','windup','strike','stagger','dead']];chosen.append(d['frames'][683]);canvas=Image.new('RGB',(1920,1440));draw=ImageDraw.Draw(canvas)
for j,f in enumerate(chosen):
 for a,angle in enumerate([[0,1,6],[6,1,0],[0,1,-6]]):
  p=(a*640,j*240);canvas.paste(render(1,f,angle).resize((640,240)),p);draw.text((p[0]+6,p[1]+6),f"{f['t']:.2f} {f['state']} {f['clip']}",font=small,fill='black')
canvas.save(W/'kite-multiview-reviewed.jpg')
(W/'review-receipt.json').write_text(json.dumps(dict(scope='Offline render of actual captured C# poses, paths, effect meshes and scheduled Yellow audio; not Unity Play Mode',runtimeReceipt=hashlib.sha256((W/'runtime-receipt.json').read_bytes()).hexdigest(),movieSHA256=hashlib.sha256(output.read_bytes()).hexdigest(),audioPeakBeforeAttenuation=peak,sourceHashes=receipt['sourceHashes']),indent=2))
print(output,flush=True)

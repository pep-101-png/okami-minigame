"""Render actual captured native poses, camera and original-painted effect meshes."""
from pathlib import Path
import sys,json,hashlib,numpy as np,subprocess,wave
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[2];W=Path('/workspace/work/solar-ultimate');sys.path.insert(0,str(R/'tools/trailer30'));import native_renderer as nr
receipt=json.load(open(W/'runtime-receipt.json'))
for p,sha in receipt['sourceHashes'].items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==sha,'Stale capture: '+p
nr.Renderer.load_scene=lambda self:None
nr.FRAG=nr.FRAG.replace('if(c.a<.22)discard;','if(mode==5){out_color=vec4(c.rgb*pigment.rgb*tint,c.a*pigment.a*opacity);return;}if(c.a<.22)discard;')
nr.FRAG=nr.FRAG.replace('if(c.a<.22)discard;','if(mode==8){vec2 local=fract(uv*atlasTiles);vec2 edge=min(local,1.-local);out_color=vec4(c.rgb*pigment.rgb*tint,c.a*pigment.a*opacity*smoothstep(0.,.14,min(edge.x,edge.y)));return;}if(c.a<.22)discard;')
nr.FRAG=nr.FRAG.replace('uniform sampler2D paint,','uniform float atlasTiles;uniform sampler2D paint,')
nr.Renderer.load_scene=lambda self:None;r=nr.Renderer(1280,720);r.static=[]
floor=nr.Draw(r,[[-42,-.02,-42],[-42,-.02,42],[42,-.02,42],[42,-.02,-42]],[[0,1,2],[0,2,3]],[[0,0],[0,12],[12,12],[12,0]],np.ones((4,4)),nr.A/'OkamiRemaster/Original/Textures/Kamiki-earth.png',twosided=True);r.static=[floor]
body=nr.Native(r,str(W/'es3a'));enemies=[];blade=nr.Native(r,'Okami/wp28');font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
def root(pos,q,scale=1):
 m=np.eye(4);m[:3,:3]=nr.rotation(q)@np.diag(np.repeat(scale,3) if np.isscalar(scale) else scale);m[:3,3]=np.array(pos)-[35,0,0];return m
def frame(f,mode):
 if mode=='ultimate':
  body.visible=True;body.scale=1;body.update('pl00_017',0,root(f['bodyPosition'],f['bodyRotation'],f['bodyScale']),False,pose=np.array(f['pose']));r.actors=[body]
  for n,e in zip(enemies,f['enemies']):
   n.visible=e['visible'];n.scale=e['scale'];n.offset=np.array(e['offset']);n.update('unused',0,root(e['position'],e['rotation']),False,pose=np.array(e['pose']));r.actors.append(n)
 else:
  blade.visible=f['visible'];blade.update('wp28_000',0,root(f['position'],f['rotation'],f['scale']),False,pose=np.array(f['pose']));body.visible=False;r.actors=[blade]
 eye=np.array(f['eye'])-[35,0,0];forward=nr.rotation(f['cameraRotation'])@np.array([0,0,1]);target=eye+forward*10;r.begin(eye,target,f['t'],0,'village',f['fov']);r.geometry();r.framebuffer.depth_mask=False
 for p in sorted(f['paint'],key=lambda p:np.linalg.norm(np.array(p['position'])+np.mean(p['vertices'],axis=0)-[35,0,0]-eye),reverse=True):
  ob=nr.Draw(r,np.array(p['vertices'])+np.array(p['position'])-[35,0,0],np.array(p['triangles']).reshape(-1,3),p['uv'],p['colors'],nr.D/'Effects'/(p['sprite']+'.png'),mode=8 if p['sprite'] in ['ImpactDust','SolarPuff','SolarBlast'] else 5,twosided=True);r.program['atlasTiles'].value=4 if p['sprite']=='SolarPuff' else 1;r.ctx.blend_func=(nr.moderngl.SRC_ALPHA,nr.moderngl.ONE if p['sprite'] in ['SolarGlow','SpiritGlow'] else nr.moderngl.ONE_MINUS_SRC_ALPHA);ob.render();ob.vao.release();ob.vbo.release();ob.ibo.release()
 r.ctx.blend_func=(nr.moderngl.SRC_ALPHA,nr.moderngl.ONE_MINUS_SRC_ALPHA)
 r.framebuffer.depth_mask=True
 im=Image.frombytes('RGB',(1280,720),r.end()).transpose(Image.Transpose.FLIP_TOP_BOTTOM);draw=ImageDraw.Draw(im);draw.rectangle((0,0,1280,30),fill='#172126');draw.text((12,5),('THIRD-FORM SUNBURST' if mode=='ultimate' else 'EIGHTH WONDER · BRUSH SLASH IMPACT')+f" · {f['t']:.2f}s · offline native-asset render / actual driver output",font=font,fill='white');return im
ud=json.load(open(W/'ultimate-runtime.json'));sd=json.load(open(W/'sword-runtime.json'));enemies=[nr.Native(r,e['resource']) for e in ud['frames'][0]['enemies']]
if '--stills' in sys.argv:
 for mode,d,times in [('ultimate',ud,[0,.6,1.4,2.2,3.5,4.4,4.7,4.85,5.05,5.35,5.8,6.5]),('sword',sd,[.1,.3,.4,.5,.7,1])]:
  for t in times:frame(d['frames'][min(len(d['frames'])-1,round(t*30))],mode).save(W/f'{mode}-{t}.jpg')
 sys.exit()
silent=W/'silent-review.mp4';out=W/'Solar-Ultimate-and-Sword-Offline-Review.mp4'
pipe=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','30','-i','-','-an','-c:v','libx264','-preset','fast','-crf','17','-pix_fmt','yuv420p',str(silent)],stdin=subprocess.PIPE)
for mode,d in [('sword',sd),('ultimate',ud)]:
 for i,f in enumerate(d['frames']):
  pipe.stdin.write(frame(f,mode).tobytes())
  if i%90==0:print(mode,i,flush=True)
pipe.stdin.close();assert pipe.wait()==0
# Mix precisely the scheduled one-shot source clips. The continuously controlled
# charge source uses its recorded per-frame control values in the capture below.
mix=np.zeros((len(sd['frames'])+len(ud['frames']))*1600,dtype=float)
for d,offset in [(sd,0),(ud,len(sd['frames'])/30)]:
 for e in d['audio']:
  if e['cue'].endswith('/flame-0'):continue
  p=nr.D.parent/(e['cue']+'.wav')
  if not p.exists():continue
  with wave.open(str(p),'rb') as f:rate=f.getframerate();v=np.frombuffer(f.readframes(f.getnframes()),'<i2').astype(float).reshape(-1,f.getnchannels()).mean(1)/32768
  pitch=e.get('pitch',1);idx=np.arange(round(len(v)*48000/(rate*pitch)))*rate*pitch/48000;v=np.interp(idx,np.arange(len(v)),v)*e['gain'];start=round((e['time']+offset)*48000);n=min(len(v),len(mix)-start)
  if n>0:mix[start:start+n]+=v[:n]
# Reconstruct the charge loop's changing gain and pitch from captured controls.
path=nr.D/'NativeAudio/flame-0.wav'
with wave.open(str(path),'rb') as f:
 rate=f.getframerate();v=np.frombuffer(f.readframes(f.getnframes()),'<i2').astype(float).reshape(-1,f.getnchannels()).mean(1)/32768
phase=0
for i,f in enumerate(ud['frames']):
 c=f['charge']
 if not c or not c['playing']:continue
 idx=(phase+np.arange(1600)*rate*c['pitch']/48000)%len(v);chunk=np.interp(idx,np.arange(len(v)),v)*c['gain'];start=(len(sd['frames'])+i)*1600;mix[start:start+1600]+=chunk;phase=(phase+1600*rate*c['pitch']/48000)%len(v)
peak=max(abs(mix));mix*=min(1,.95/max(peak,1e-9))
with wave.open(str(W/'scheduled-review.wav'),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(48000);f.writeframes((mix*32767).astype('<i2').tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',str(silent),'-i',str(W/'scheduled-review.wav'),'-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',str(out)],check=True)
for t in [.4,2.4,4,5.8,6.5,6.8,7.2,8.3]:subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(out),'-frames:v','1',str(W/f'encoded-{t}.jpg')],check=True)
(W/'review-receipt.json').write_text(json.dumps(dict(scope='Offline native-asset render of actual C# poses, camera, effect meshes and scheduled one-shot/charge-loop audio; not Unity Play Mode',runtimeReceipt=hashlib.sha256((W/'runtime-receipt.json').read_bytes()).hexdigest(),sha256=hashlib.sha256(out.read_bytes()).hexdigest(),audioPeakBeforeAttenuation=float(peak)),indent=2));print(out,flush=True)

"""Offline render of captured guardian driver poses and recorded arena prop transforms."""
from pathlib import Path
import sys,json,subprocess,hashlib,numpy as np
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[2];W=Path('/workspace/work/celestial-guardians');sys.path.insert(0,str(R/'tools/trailer30'));import native_renderer as nr
receipt=json.loads((W/'runtime-receipt.json').read_text())
for p,sha in receipt['sourceHashes'].items():assert hashlib.sha256((R/p).read_bytes()).hexdigest()==sha,'Stale capture: '+p
for p,sha in receipt['captureHashes'].items():assert hashlib.sha256((W/p).read_bytes()).hexdigest()==sha,'Stale capture: '+p
nr.Renderer.load_scene=lambda self:None
nr.FRAG=nr.FRAG.replace('uniform sampler2D paint,','uniform sampler2D courtCloud;uniform float courtEclipse;uniform sampler2D paint,')
nr.FRAG=nr.FRAG.replace('if(c.a<.22)discard;',"""if(mode==9){float radius=length(world.xz);vec3 cloud=texture(courtCloud,world.xz*.032+clock*.001).rgb;float curl=dot(cloud,vec3(.333));vec3 stone=texture(paint,world.xz*.11).rgb;vec3 meadow=texture(grass,world.xz*.16).rgb*vec3(.8,.93,.84);vec3 ground=mix(stone*.92,meadow,smoothstep(16.+curl,22.+curl,radius));ground=mix(ground,ground*vec3(.63,.67,.87),courtEclipse*.55);vec3 mist=mix(vec3(.98,.98,1),vec3(.81,.85,.96),clamp((.85-curl)*2.,0.,1.));ground=mix(ground,mist,smoothstep(24.,29.+curl,radius));float ring=(1.-smoothstep(.04,.12,abs(radius-13.5)))*.35;out_color=vec4(mix(ground,vec3(.9,.76,.47),ring),1);return;}if(c.a<.22)discard;""")
r=nr.Renderer(1280,720);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',20)
def root(pos,q,scale,centre):
 m=np.eye(4);m[:3,:3]=nr.rotation(q)@np.diag(scale);m[:3,3]=np.array(pos)-centre;return m
out=W/'Celestial-Guardians-Offline-Preview.mp4';silent=W/'silent-preview.mp4';pipe=None;contact=Image.new('RGB',(1280,720*4),'white')
for kind in [1,2]:
 r.program['courtCloud'].value=6;r.texture(nr.D/'Effects/Cloud.png').use(6);r.program['courtEclipse'].value=kind-1
 centre=np.array([380,70,0] if kind==1 else [380,100,140]);r.static=[];r.dynamic=[];r.actors=[];props=json.loads((W/f'arena-{kind}.json').read_text())
 for p in props:
  folder=nr.D/p['resource'].removeprefix('Okami/');model=json.loads((folder/'Model.json').read_text());matrix=root(p['position'],p['rotation'],p['scale'],centre)
  for part in model['parts']:
   if model.get('visibleGroups') and int(part['name'].split('-')[1]) not in model['visibleGroups']:continue
   texture=next(t for t in model['textures'] if t['index']==part['texture']);path=None if texture.get('vertexOnly') else folder/texture['path'];mode=7 if p['resource']=='Okami/heaven-cloud' else 9 if p['resource']=='Okami/celestial-grounded' else 0
   if mode==9:path=nr.D/'celestial-stair/Texture-0.png'
   r.static.append(nr.Draw(r,np.array(part['positions']).reshape(-1,3),np.array(part['indices']).reshape(-1,3),np.array(part['uv']).reshape(-1,2),np.array(part['colors']).reshape(-1,4),path,matrix,mode=mode,twosided=mode in [7,9],realm='garden'))
 data=json.loads((W/f'guardian-{kind}-runtime.json').read_text());actors=[nr.Native(r,a['resource'],realm='garden') for a in data['frames'][0]['actors']]
 # Scripted target marker makes the contact distance visible without inventing player animation.
 for actor in actors:actor.visible=True
 if '--stills' not in sys.argv and pipe is None:pipe=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','30','-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(silent)],stdin=subprocess.PIPE)
 for i,f in enumerate(data['frames'][:480]):
  if '--stills' in sys.argv and i not in [50,160,290,420]:continue
  for actor,a in zip(actors,f['actors']):actor.update(a['clip'],0,root(a['position'],a['rotation'],a['scale'],centre),False,pose=np.array(a['pose']))
  r.actors=actors;eye=np.array(f['eye'])-centre;target=eye+nr.rotation(f['cameraRotation'])@np.array([0,0,10]);r.begin(eye,target,f['t'],0,'garden',f['fov']);r.geometry();im=Image.frombytes('RGB',(1280,720),r.end()).transpose(Image.Transpose.FLIP_TOP_BOTTOM);d=ImageDraw.Draw(im);d.rectangle((0,0,1280,36),fill='#172126');d.text((12,8),('VEILED SENTINEL' if kind==1 else 'ECLIPSE WARDEN')+f" · {f['state']} / {f['move']} · {f['t']:.2f}s · offline actual driver output",font=font,fill='white')
  if i in [50,160,290,420]:im.save(W/f'guardian-{kind}-{i}.jpg')
  if pipe:pipe.stdin.write(im.tobytes())
  if i%120==0:print(kind,i,flush=True)
 if '--stills' in sys.argv:continue
if pipe:
 pipe.stdin.close();assert pipe.wait()==0
 # The existing recovered battle track remains separate from the NPC flute music.
 audio=json.loads((nr.D/'NativeAudio.json').read_text());cue=next(e for e in audio['cues'] if e['cue']=='battle');path=next(p/(cue['resource']+ext) for p in nr.A.rglob('Resources') for ext in ['.wav','.ogg'] if (p/(cue['resource']+ext)).exists())
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(silent),'-stream_loop','-1','-i',str(path),'-filter:a','volume=0.12','-c:v','copy','-c:a','aac','-b:a','192k','-shortest','-movflags','+faststart',str(out)],check=True)
 (W/'review-receipt.json').write_text(json.dumps(dict(scope='Offline native asset render of actual captured guardian C# driver poses and arena placements. Scripted target, no Unity physics or Play Mode. Original battle track added at review gain; attack SFX are not rendered.',runtimeReceipt=hashlib.sha256((W/'runtime-receipt.json').read_bytes()).hexdigest(),sha256=hashlib.sha256(out.read_bytes()).hexdigest()),indent=2));print(out)

"""Offline native-asset review of actual activity-driver placements and poses.
This does not run Unity or render game UI/physics. Village terrain is a flat fixture.
"""
from pathlib import Path
import sys,json,hashlib,numpy as np,subprocess
from PIL import Image,ImageDraw,ImageFont
R=Path(__file__).resolve().parents[2];W=Path('/workspace/work/village-adventures');sys.path.insert(0,str(R/'tools/trailer30'));import native_renderer as nr
# Reuse the earlier review's faithful CelestialCourt shader port.
old=(R/'tools/celestial-guardians/review.py').read_text();start=old.index('nr.Renderer.load_scene=');end=old.index('r=nr.Renderer(');exec(old[start:end])
nr.FRAG=nr.FRAG.replace('uniform float courtEclipse;', 'uniform float courtEclipse;uniform float courtMoonlit;')
nr.FRAG=nr.FRAG.replace('void main(){','float segmentDistance(vec2 p,vec2 a,vec2 b){vec2 d=b-a;return length(p-a-d*clamp(dot(p-a,d)/dot(d,d),0.,1.));}void main(){')
nr.FRAG=nr.FRAG.replace('ground=mix(ground,ground*vec3(.63,.67,.87)', 'if(courtMoonlit>.5){vec2 p=world.xz;float path=min(min(segmentDistance(p,vec2(0,-22),vec2(-12,-10)),segmentDistance(p,vec2(-12,-10),vec2(8,2))),min(segmentDistance(p,vec2(8,2),vec2(-4,14)),segmentDistance(p,vec2(-4,14),vec2(0,20))));float edge=smoothstep(1.1,2.2,path+sin(p.x*1.7+p.y)*.16);ground=mix(texture(paint,p*.5).rgb*.75,meadow,edge);}ground=mix(ground,ground*vec3(.63,.67,.87)')
nr.FRAG=nr.FRAG.replace(')*.35;out_color',')*.35*(1.-courtMoonlit);out_color')
r=nr.Renderer(1280,720);font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',18)
def matrix(p,q,s,c):
 m=np.eye(4);m[:3,:3]=nr.rotation(q)@np.diag(s);m[:3,3]=np.array(p)-c;return m
def add_prop(p,c):
 folder=nr.D/p['resource'].removeprefix('Okami/');model=json.loads((folder/'Model.json').read_text());m=matrix(p['position'],p['rotation'],p['scale'],c)
 for part in model['parts']:
  if model.get('visibleGroups') and int(part['name'].split('-')[1]) not in model['visibleGroups']:continue
  texture=next(t for t in model['textures'] if t['index']==part['texture']);path=None if texture.get('vertexOnly') else folder/texture['path'];mode=7 if p['resource']=='Okami/heaven-cloud' else 9 if p['resource']=='Okami/celestial-grounded' else 0
  if mode==9:path=nr.D/'celestial-stair/Texture-0.png'
  r.static.append(nr.Draw(r,np.array(part['positions']).reshape(-1,3),np.array(part['indices']).reshape(-1,3),np.array(part['uv']).reshape(-1,2),np.array(part['colors']).reshape(-1,4),path,m,mode=mode,twosided=mode in [7,9],realm='garden'))
def plane(y,rx,rz,texture,colour=(1,1,1,1)):
 v=np.array([[-rx,y,-rz],[-rx,y,rz],[rx,y,rz],[rx,y,-rz]]);r.static.append(nr.Draw(r,v,np.array([[0,1,2],[0,2,3]]),np.array([[0,0],[0,1],[1,1],[1,0]]),np.tile(colour,(4,1)),texture,realm='garden',twosided=True))
scenes=[('mastery',(0,1,0),(15,16,-21)),('fishing',(0,-.2,0),(0,4.5,5.5)),('restoration',(0,.8,0),(6,6,-8)),('farm',(52.8,1,31),(60.8,8,23)),('bridge',(-10,1,-18),(0,12,-27)),('pond',(1,1,-24),(8,8,-31)),('moonlit',(0,1,2),(27,27,-32))]
contact=Image.new('RGB',(1280*2,720*4));stills=[]
for idx,(name,target,eye) in enumerate(scenes):
 source=name if name in ['mastery','fishing','restoration','moonlit'] else 'restoration';data=json.loads((W/(source+'-runtime.json')).read_text());c=np.array(data['centre']);r.static=[];r.actors=[];r.dynamic=[]
 r.program['courtCloud'].value=6;r.texture(nr.D/'Effects/Cloud.png').use(6);r.program['courtEclipse'].value=int(name=='moonlit');r.program['courtMoonlit'].value=int(name=='moonlit')
 if source in ['restoration','fishing']:plane(-.02,65,65,nr.A/'OkamiRemaster/Original/Textures/Kamiki-grass.png')
 for p in data['props']:
  if np.linalg.norm((np.array(p['position'])-c)[[0,2]])<75:add_prop(p,c)
 for a in data['actors']:
  if np.linalg.norm((np.array(a['position'])-c)[[0,2]])>75:continue
  actor=nr.Native(r,a['resource'],realm='garden');actor.visible=True;actor.update(a['clip'],0,matrix(a['position'],a['rotation'],a['scale'],c),False,pose=np.array(a['pose']));r.actors.append(actor)
 # Fish visibility/scale can be inspected without pretending the flat fixture is the actual pond shader.
 if name=='fishing':r.static=[]
 r.begin(eye,target,2,0,'garden',48);r.geometry();im=Image.frombytes('RGB',(1280,720),r.end()).transpose(Image.Transpose.FLIP_TOP_BOTTOM);d=ImageDraw.Draw(im);d.rectangle((0,0,1280,34),fill='#162020');d.text((12,7),name.upper()+' · actual driver transforms / native poses · offline fixture, not Unity',font=font,fill='white');im.save(W/(name+'-review.jpg'));contact.paste(im,((idx%2)*1280,(idx//2)*720));stills.append(W/(name+'-review.jpg'));print(name,flush=True)
contact.thumbnail((1280,1440));contact.save(W/'review-contact.jpg')
# Review recovered swimming and tea gestures through the actual sampled C# poses.
for kind,centre,eye,target in [('fish',np.array([-15,0,-22]),(0,3.1,4.3),(0,-.2,0)),('tea',np.array([-13,0,6]),(4,3.5,-5),(0,.8,0))]:
 frames=json.loads((W/(kind+'-motion-runtime.json')).read_text());r.static=[];r.actors=[];r.dynamic=[]
 if kind=='tea':
  plane(-.02,65,65,nr.A/'OkamiRemaster/Original/Textures/Kamiki-grass.png')
  for p in json.loads((W/'restoration-runtime.json').read_text())['props']:
   if not p.get('held') and np.linalg.norm((np.array(p['position'])-centre)[[0,2]])<10:add_prop(p,centre)
 rows=[a for a in frames[0]['actors'] if np.linalg.norm((np.array(a['position'])-centre)[[0,2]])<(8 if kind=='fish' else 10)]
 actors=[nr.Native(r,a['resource'],realm='garden') for a in rows]
 for a in actors:a.visible=True
 held=[]
 for p in frames[0]['held']:
  if np.linalg.norm((np.array(p['position'])-centre)[[0,2]])<10:
   before=len(r.static);add_prop(p,centre);held.append(r.static[before:])
 r.actors=actors;out=W/(kind+'-motion.mp4');pipe=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1280x720','-r','30','-i','-','-an','-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p',str(out)],stdin=subprocess.PIPE)
 for i,frame in enumerate(frames):
  rows=[a for a in frame['actors'] if np.linalg.norm((np.array(a['position'])-centre)[[0,2]])<(8 if kind=='fish' else 10)]
  assert len(rows)==len(actors)
  for actor,a in zip(actors,rows):actor.update(a['clip'],0,matrix(a['position'],a['rotation'],a['scale'],centre),False,pose=np.array(a['pose']))
  props=[p for p in frame['held'] if np.linalg.norm((np.array(p['position'])-centre)[[0,2]])<10]
  assert len(props)==len(held)
  for group,p in zip(held,props):
   for ob in group:ob.root=matrix(p['position'],p['rotation'],p['scale'],centre)
  r.begin(eye,target,frame['t'],0,'garden',48);r.geometry();im=Image.frombytes('RGB',(1280,720),r.end()).transpose(Image.Transpose.FLIP_TOP_BOTTOM);d=ImageDraw.Draw(im);d.rectangle((0,0,1280,34),fill='#162020');d.text((12,7),kind.upper()+' · actual C# native motion samples · offline rig review; no Unity physics / water',font=font,fill='white');pipe.stdin.write(im.tobytes())
  if i in [0,40,80,119]:im.save(W/(kind+'-motion-'+str(i)+'.jpg'))
 pipe.stdin.close();assert pipe.wait()==0;print(kind+' motion',flush=True)
# A separate review reel, not an in-game trailer.
concat=W/'review-concat.txt';concat.write_text(''.join("file '"+str(p)+"'\nduration 2\n" for p in stills)+"file '"+str(stills[-1])+"'\n")
subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(concat),'-r','30','-c:v','libx264','-pix_fmt','yuv420p','-crf','20','-movflags','+faststart',str(W/'stills.mp4')],check=True)

concat.write_text("file '"+str(W/'stills.mp4')+"'\nfile '"+str(W/'fish-motion.mp4')+"'\nfile '"+str(W/'tea-motion.mp4')+"'\n")
subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(W/'Village-Adventures-Offline-Review.mp4')],check=True)
(W/'review-receipt.json').write_text(json.dumps(dict(scope='Offline native original-asset review of actual C# village activity driver placements and sampled fish/tea poses. Flat fixture terrain; no Unity UI, physics, water or PC performance validation.',runtimeReceipt=hashlib.sha256((W/'runtime-receipt.json').read_bytes()).hexdigest(),sha256=hashlib.sha256((W/'Village-Adventures-Offline-Review.mp4').read_bytes()).hexdigest()),indent=2))

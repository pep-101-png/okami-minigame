"""Render exact poses captured from the real C# drivers, not substitute choreography."""
from pathlib import Path
import sys,json,numpy as np,subprocess
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/trailer30'));import native_renderer as nr
from PIL import Image,ImageDraw,ImageFont
W=Path('/workspace/work/imp-rework');import hashlib
receipt=json.loads((W/'runtime-receipt.json').read_text())
for name,sha in receipt['sourceHashes'].items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==sha,'Stale source capture: '+name
nr.Renderer.load_scene=lambda self:None;r=nr.Renderer(640,480);r.static=[]
tex=R/'Sunward-Unity/Assets/OkamiRemaster/Original/Textures/Kamiki-earth.png'
floor=nr.Draw(r,[[-10,0,-10],[-10,0,10],[10,0,10],[10,0,-10]],[[0,1,2],[0,2,3]],[[0,0],[0,5],[5,5],[5,0]],np.ones((4,4)),tex,twosided=True);r.static=[floor]
roles=['wisp','reed','ranged','heavy','elite'];names=['Green Imp · lute','Red Imp · scroll','Yellow Imp · drum','Blue Imp · flute','Black Imp · drum'];datasets=[json.loads((W/(role+'-runtime.json')).read_text()) for role in roles];actors=[nr.Native(r,d['resource']) for d in datasets];hero=nr.Native(r,'NativePlayer/pl00');hero.visible=True
font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',17);small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',14)
output=W/'Imp-Rework-Offline-Motion-Review.mp4';cmd=['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1920x960','-r','60','-i','-','-an','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p',str(output)];pipe=subprocess.Popen(cmd,stdin=subprocess.PIPE)
for i in range(720):
 sheet=Image.new('RGB',(1920,960),'#20282e');draw=ImageDraw.Draw(sheet)
 for k,(d,n) in enumerate(zip(datasets,actors)):
  f=d['frames'][i];n.scale=f['modelScale']*f['scale'];n.offset=np.array(f['offset'])*f['scale'];n.visible=True;pos=np.array(f['position'])-[35,0,0];rot=np.eye(4);rot[:3,:3]=nr.rotation(f['rotation']);rot[:3,3]=pos;n.update(f['clip'],f['sourceTime'],rot,False,pose=np.array(f['pose']))
  hero.update('pl00_000',f['t'],nr.matrix([0,0,7 if k==2 else 4.8],180));r.actors=[n,hero]
  # A fixed oblique view reveals approach/root motion, ground contact and leaps.
  mid=(pos[2]+(7 if k==2 else 4.8))/2;r.begin(np.array([6.4,4.8,mid+7.8]),[0,1.0,mid],f['t'],0,'village',50);r.geometry();im=Image.frombytes('RGB',(640,480),r.end()).transpose(Image.Transpose.FLIP_TOP_BOTTOM);p=(k%3*640,k//3*480);sheet.paste(im,p);draw.rectangle([p[0],p[1],p[0]+640,p[1]+58],fill='#162128');draw.text((p[0]+12,p[1]+7),names[k],font=font,fill='white');draw.text((p[0]+12,p[1]+32),f"{f['state']} · {f['clip']} · {'FROZEN' if f['frozen'] else 'source '+str(round(f['sourceTime'],2))+'s'}",font=small,fill='#b9dfd2');n.visible=False
 draw.text((1300,535),'IMP MOTION REVIEW',font=font,fill='white');draw.multiline_text((1300,575),'Exact captured C# driver poses\nOriginal models, textures and MOTs\n\n0–5s: approach and attacks\n5s: freeze; 7s: hit interruption\n10.17s: defeat, then held fall\n\nOffline native-asset render\nEngine doubles; flat test floor\nNot Unity Play Mode footage',font=font,fill='#c0d0d4',spacing=9);draw.text((1300,885),f'{i/60:.2f}s / 12s · 60 fps',font=font,fill='white');pipe.stdin.write(sheet.tobytes())
 if i%120==0:print('review frames',i,flush=True)
pipe.stdin.close();assert pipe.wait()==0
# Inspect encoded frames, so this also catches framing and encoding faults.
for sec in [0.7,2.4,3.6,5.4,7.2,8.8,11.5]:
 subprocess.run(['ffmpeg','-v','error','-y','-ss',str(sec),'-i',str(output),'-frames:v','1',str(W/f'encoded-{sec}.jpg')],check=True)
# Dense phase strips, including native windup->strike and strike->recover joins.
for k,(d,n) in enumerate(zip(datasets,actors)):
 frames=d['frames'];start=next(i for i,f in enumerate(frames) if f['state']=='windup');end=next(i for i in range(start+1,len(frames)) if frames[i-1]['state']=='recover' and frames[i]['state']=='approach');chosen=list(np.linspace(start,end,24).astype(int));canvas=Image.new('RGB',(1920,1440));draw=ImageDraw.Draw(canvas)
 for col,i in enumerate(chosen):
  f=frames[i];n.scale=f['modelScale']*f['scale'];n.offset=np.array(f['offset'])*f['scale'];n.visible=True;root=np.eye(4);root[:3,:3]=nr.rotation(f['rotation']);root[:3,3]=np.array(f['position'])-[35,0,0];n.update(f['clip'],f['sourceTime'],root,False,pose=np.array(f['pose']));hero.visible=False;r.actors=[n];at=np.array(f['position'])-[35,0,0];r.begin(at+np.array([-4.5,2.7,5.5]),at+[0,1.2,0],f['t'],0,'village',43);r.geometry();im=Image.frombytes('RGB',(640,480),r.end()).transpose(Image.Transpose.FLIP_TOP_BOTTOM).resize((480,240));p=(col%4*480,col//4*240);canvas.paste(im,p);draw.text((p[0]+5,p[1]+5),f"{f['t']:.2f} {f['state']} {f['sourceTime']:.2f}",font=small,fill='black')
 canvas.save(W/f'{roles[k]}-attack-reviewed.jpg');n.visible=False
print('Wrote exact-pose moving review and encoded-frame phase strips',flush=True)

(W/'review-receipt.json').write_text(json.dumps(dict(scope='Offline render of exact C# driver poses; not Unity Play Mode',runtimeReceipt=hashlib.sha256((W/'runtime-receipt.json').read_bytes()).hexdigest(),movieSHA256=hashlib.sha256(output.read_bytes()).hexdigest(),sourceHashes=receipt['sourceHashes']),indent=2))

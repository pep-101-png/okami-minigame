from pathlib import Path
import sys,numpy as np,shutil,math,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/trailer30'));import native_renderer as nr
W=Path('/workspace/work/spirit-trailing-motion');D=nr.D
nr.FRAG=nr.FRAG.replace('if(c.a<.22)discard;','''if(mode==8){vec3 normal=normalize(cross(dFdx(world),dFdy(world)));float shade=.82+.16*abs(dot(normal,normalize(vec3(.4,.8,.3))));float energy=max(pigment.r,max(pigment.g,pigment.b));vec3 hue=energy>.001?pigment.rgb/energy:vec3(1);out_color=vec4(clamp(c.rgb*hue*tint*shade,0.,1.),c.a*pigment.a*sqrt(clamp(energy,0.,1.))*opacity);return;}if(c.a<.22)discard;''')
nr.Renderer.load_scene=lambda self:None;r=nr.Renderer(1000,800);r.static=[]
r.place('Okami/celestial-grounded',[0,-.055,-1],[24,.02,20],mode=1)
tempBody=W/'preview-es3a';tempBody.mkdir(exist_ok=True)
for p in (D/'es3a').iterdir():
 if p.suffix in ['.json','.png']:shutil.copyfile(p,tempBody/p.name)
shutil.copyfile(nr.A/'OkamiRemaster/Player/Resources/NativePlayer/pl00/Poses.bytes',tempBody/'Poses.bytes');body=nr.Native(r,str(tempBody));body.visible=True
ribbons=[]
for i in range(6):
 source=D/('es4a-flow' if i%2==0 else 'es4b-flow');temp=W/source.name;temp.mkdir(exist_ok=True)
 for p in source.iterdir():
  if p.suffix in ['.json','.png']:shutil.copyfile(p,temp/p.name)
 shutil.copyfile(D/'es4a/Poses.bytes',temp/'Poses.bytes');n=nr.Native(r,str(temp));n.visible=True;ribbons.append(n)
 for _,ob in n.parts:ob.mode=8;ob.tint=(.94,.96,1);ob.opacity=.72;ob.twosided=True
heading=nr.matrix(yaw=90);rot=heading[:3,:3]
views={'overhead-close':([3,4.5,3],[0,.65,-.3]),'overhead':([4,6,4],[0,.65,-.3]),'side':([5,1.8,-1],[0,.7,-.7]),'rear':([-4,2.7,-5],[0,.7,-.8]),'top':([0,9,.1],[0,.7,-.5])}
# Read profiles from the actual implementation, rather than inventing preview values.
import re,subprocess
source=(nr.A/'OkamiRemaster/Original/Scripts/SpectralTendrils.cs').read_text()
def floats(name):return [float(x.strip().rstrip('f')) for x in re.search(r'float\[\] '+name+r'=\{([^}]+)',source)[1].split(',')]
lengths,rates,phases,headings,gains,rolls,bows=[floats(k) for k in ['lengths','rates','phases','headings','gains','rolls','bows']]
mounttext=re.search(r'Vector3\[\] mounts=\{([^}]+)',source)[1];mounts=[np.array([float(x.strip().rstrip('f')) for x in row.split(',')]) for row in re.findall(r'new Vector3\(([^)]+)\)',mounttext)]
motions=re.findall(r'"([^"]+)"',re.search(r'string\[\] motions=\{([^}]+)',source)[1])
def multiply(a,b):return np.c_[a[:,3,None]*b[:,:3]+b[:,3,None]*a[:,:3]+np.cross(a[:,:3],b[:,:3]),a[:,3]*b[:,3]-np.sum(a[:,:3]*b[:,:3],axis=1)]
def animate(clock,bodyclip='pl00_000'):
 body.update(bodyclip,clock,nr.matrix(yaw=90,scale=1.2));torso=(body.root@body.transforms[1])[:3,3]
 for i,n in enumerate(ribbons):
  point=torso+rot@mounts[i];root=nr.matrix(point,90+180+headings[i],lengths[i]);a=np.deg2rad(rolls[i]);root[:3,:3]=root[:3,:3]@np.array([[np.cos(a),-np.sin(a),0],[np.sin(a),np.cos(a),0],[0,0,1]]);clip=motions[i];data=n.bank[clip][0];base=data[:,:,3:7].copy();base[np.sum(base*base[0],axis=2)<0]*=-1;base=base.sum(0);base/=np.linalg.norm(base,axis=1,keepdims=True);base[:,:3]*=-1
  samples=np.array([n.pose(clip,clock*rates[i]+phases[i]-b*.19)[b] for b in range(len(base))]);delta=multiply(base,samples[:,3:7]);delta/=np.linalg.norm(delta,axis=1,keepdims=True);delta[delta[:,3]<0]*=-1
  def blend(q,g):
   q=q.copy();q[q[:,3]<0]*=-1;a=np.arccos(np.clip(q[:,3],-1,1));v=np.sin(a*g)/np.maximum(np.sin(a),1e-8);return np.c_[q[:,:3]*v[:,None],np.cos(a*g)]
  shallow=blend(base,bows[i]);shallow[:2]=[0,0,0,1];samples[:,3:7]=multiply(shallow,blend(delta,gains[i]));samples[:,:3]=np.vstack([[0,0,0],np.array([b['position'] for b in n.model['bones']])]);samples[:,7:]=1;n.update(clip,0,root,pose=samples)

def frame(eye,target,clock,night=0):
 r.actors=[body];r.begin(np.array(eye),target,clock,night,'village',47);r.geometry();r.ctx.depth_mask=False
 for n in ribbons:n.draw()
 r.ctx.depth_mask=True
 return nr.Image.frombytes('RGB',(1000,800),r.end()).transpose(nr.Image.Transpose.FLIP_TOP_BOTTOM)
for clock in [0,1.2,2.8,4.7]:
 animate(clock)
 for name,(eye,target) in views.items():frame(eye,target,clock).save(W/f'{name}-{clock}.png')
# Inspect a complete moving sequence; 90 original renders, no frame interpolation.
movie=W/'motion';movie.mkdir(exist_ok=True)
for i in range(90):
 t=i/15;animate(t);frame([3.5,5,3.5],[-.7,.65,0],t,.65).save(movie/f'{i:04d}.png')
subprocess.run(['ffmpeg','-v','error','-y','-framerate','15','-i',str(movie/'%04d.png'),'-c:v','libx264','-crf','18','-pix_fmt','yuv420p',str(W/'Shiranui-Trailing-Motion-Preview.mp4')],check=True)
print('Twenty still views and ninety-frame offline motion preview; actual profiles and native motion residuals, not Unity')

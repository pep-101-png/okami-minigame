from pathlib import Path
import sys,numpy as np,re,shutil,subprocess
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/trailer30'));import native_renderer as nr
W=Path('/workspace/work/spirit-wisp-flow');D=nr.D
curve='''uniform vec4 curvePoints[41];uniform float curveLength;uniform float strandWidth;uniform int mode;out vec3 wispN;
vec3 curve(float u){float f=clamp(u,0.,1.)*40.;int k=min(39,int(floor(f)));float t=f-float(k);vec3 a=curvePoints[max(0,k-1)].xyz,b=curvePoints[k].xyz,c=curvePoints[k+1].xyz,d=curvePoints[min(40,k+2)].xyz;return .5*((2.*b)+(-a+c)*t+(2.*a-5.*b+4.*c-d)*t*t+(-a+3.*b-3.*c+d)*t*t*t);}
'''
nr.VERT=nr.VERT.replace('void main(){',curve+'void main(){wispN=vec3(0,1,0);').replace('p=root*p;world=p.xyz;', '''if(mode==8){float u=clamp(p.z/curveLength,0.,1.);vec3 tangent=normalize(curve(min(1.,u+.002))-curve(max(0.,u-.002)));vec3 right=normalize(cross(vec3(0,1,0),tangent)),up=cross(tangent,right);float width=(.9+2.1*sin(u*3.14159265))*strandWidth;vec2 radial=length(p.xy)>.00001?normalize(p.xy):vec2(1,0);wispN=mat3(root)*(right*radial.x+up*radial.y);p=vec4(curve(u)+(right*p.x+up*p.y)*width,1);}p=root*p;world=p.xyz;''')
nr.FRAG=nr.FRAG.replace('in vec2 uv;', 'in vec3 wispN;in vec2 uv;').replace('if(c.a<.22)discard;', '''if(mode==8){float energy=max(pigment.r,max(pigment.g,pigment.b));vec3 hue=energy>.001?pigment.rgb/energy:vec3(1);float facing=abs(dot(normalize(wispN),normalize(cameraPos-world)));float soft=smoothstep(.02,.85,facing);out_color=vec4(clamp(c.rgb*hue*tint,0.,1.),c.a*pigment.a*sqrt(clamp(energy,0.,1.))*opacity*soft);return;}if(c.a<.22)discard;''')
originalDraw=nr.Draw.render
def draw(self):
 if self.mode==8:self.r.program['curvePoints'].write(self.curve.astype('f4').tobytes());self.r.program['curveLength'].value=3.8271732;self.r.program['strandWidth'].value=self.strandWidth
 originalDraw(self)
nr.Draw.render=draw;nr.Renderer.load_scene=lambda self:None;r=nr.Renderer(1000,800);r.place('Okami/celestial-grounded',[0,-.055,-1],[24,.02,20],mode=1)
temp=W/'body';temp.mkdir(exist_ok=True)
for p in (D/'es3a').iterdir():
 if p.suffix in ['.json','.png']:shutil.copyfile(p,temp/p.name)
shutil.copyfile(nr.A/'OkamiRemaster/Player/Resources/NativePlayer/pl00/Poses.bytes',temp/'Poses.bytes');body=nr.Native(r,str(temp));body.visible=True
source=(nr.A/'OkamiRemaster/Original/Scripts/SpectralTendrils.cs').read_text()
def vals(name):return np.array([float(x.strip().rstrip('f')) for x in re.search(r'float\[\] '+name+r'=\{([^}]+)',source)[1].split(',')])
lengths,rates,phases,headings,breadth,widths=[vals(x) for x in ['lengths','rates','phases','headings','breadth','widths']];mounts=[np.array([float(x.strip().rstrip('f')) for x in row.split(',')]) for row in re.findall(r'new Vector3\(([^)]+)\)',re.search(r'Vector3\[\] mounts=\{([^}]+)',source)[1])]
ribbons=[]
for i in range(len(lengths)):
 original=D/('es4a-flow' if i%2==0 else 'es4b-flow');temp=W/original.name;temp.mkdir(exist_ok=True)
 for p in original.iterdir():
  if p.suffix in ['.json','.png']:shutil.copyfile(p,temp/p.name)
 shutil.copyfile(D/'es4a/Poses.bytes',temp/'Poses.bytes');n=nr.Native(r,str(temp));n.visible=True;ribbons.append(n)
 for _,ob in n.parts:ob.mode=8;ob.strandWidth=widths[i];ob.tint=(.92,.95,1);ob.opacity=.38;ob.twosided=True
rot=nr.matrix(yaw=90)[:3,:3]
def controls(i,t):
 out=[np.zeros(4)];step=3.8271732/40;point=np.zeros(3)
 for j in range(40):
  s=(j+.5)*step;seed=phases[i];phase=s*1.85-t*rates[i]+seed;cross=breadth[i]*(.78*np.sin(phase)+.22*np.sin(s*3.1-t*.68+seed*1.37));rise=.1+.25*np.sin(s*1.35-t*.63+seed*1.7);d=np.array([cross,rise,1]);point=point+d/np.linalg.norm(d)*step;out.append(np.r_[point,0])
 return np.array(out)
def animate(t):
 body.update('pl00_000',t,nr.matrix(yaw=90,scale=1.2));torso=(body.root@body.transforms[1])[:3,3]
 for i,n in enumerate(ribbons):
  pose=n.bank['et03_002'][0][0].copy();pose[:,:3]=np.vstack([[0,0,0],np.array([b['position'] for b in n.model['bones']])]);pose[:,3:7]=[0,0,0,1];pose[:,7:]=1;n.update('et03_002',0,nr.matrix(torso+rot@mounts[i],270+headings[i],lengths[i]),pose=pose)
  for _,ob in n.parts:ob.curve=controls(i,t)
def frame(t,eye,target,night=0):
 animate(t);r.actors=[body];r.begin(np.array(eye),target,t,night,'village',47);r.geometry();r.framebuffer.depth_mask=False
 for n in ribbons:n.draw()
 r.framebuffer.depth_mask=True
 return nr.Image.frombytes('RGB',(1000,800),r.end()).transpose(nr.Image.Transpose.FLIP_TOP_BOTTOM)
views={'overhead':([3,4.5,3],[-.3,.65,0]),'side':([0,1.9,6],[-.8,.7,0]),'rear':([-5,3,-3],[-.8,.7,0])}
for t in [0,1.3,2.9,4.8]:
 for name,(eye,target) in views.items():frame(t,eye,target,.55).save(W/f'{name}-{t}.png')
print('Twelve faithful shader/curve stills rendered',flush=True)
movie=W/'motion';movie.mkdir(exist_ok=True)
for i in range(240):frame(i/60,[3.5,5,3.5],[-.7,.65,0],.6).save(movie/f'{i:04d}.png')
subprocess.run(['ffmpeg','-v','error','-y','-framerate','60','-i',str(movie/'%04d.png'),'-frames:v','240','-c:v','libx264','-crf','18','-pix_fmt','yuv420p',str(W/'Shiranui-Soft-Wisp-Preview.mp4')],check=True)
print('Four-second motion preview: 240 original renders, not Unity',flush=True)

"""Offline original-data visual diagnostics; not a Unity capture."""
from pathlib import Path
import sys,numpy as np,shutil,math
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools/trailer30'));import native_renderer as nr
W=Path('/workspace/work/awakening-playtest');D=nr.D
nr.VERT=nr.VERT.replace('void main(){','uniform int mode;void main(){').replace('p=root*p;world=p.xyz;','if(mode==9){float wave=sin(in_uv.x*12.56637+clock*.38+in_uv.y*3.)*.035;p.xz*=1.+wave*sin(in_uv.y*3.14159);}p=root*p;world=p.xyz;').replace('uniform int mode;void main','uniform int mode;uniform float clock;void main')
nr.FRAG=nr.FRAG.replace('if(c.a<.22)discard;','''if(mode==5){out_color=vec4(c.rgb*tint,c.a*opacity);return;}if(mode==9){vec2 u=vec2(.5+.17*sin(uv.x*6.283185+clock*.13+uv.y*2.),.5+.35*sin(uv.y*3.14159-clock*.15+sin(uv.x*6.283185)*.5));vec4 soft=texture(paint,u);float edge=smoothstep(0.,.22,uv.y)*smoothstep(0.,.25,1.-uv.y);out_color=vec4(.38,.62,.95,soft.r*soft.a*edge*.45*.75);return;}if(c.a<.22)discard;''')
nr.Renderer.load_scene=lambda self:None;r=nr.Renderer(1000,800)
bodyDir=W/'es3a';bodyDir.mkdir(exist_ok=True)
for p in (D/'es3a').iterdir():
 if p.suffix in ['.json','.png']:shutil.copyfile(p,bodyDir/p.name)
shutil.copyfile(nr.A/'OkamiRemaster/Player/Resources/NativePlayer/pl00/Poses.bytes',bodyDir/'Poses.bytes');body=nr.Native(r,str(bodyDir));body.visible=True
floor=r.place('Okami/celestial-grounded',[0,-.025,0],[32,.02,32],mode=7,realm='garden')
v=[];uv=[];tri=[]
for y in range(13):
 for i in range(129):
  a=i*np.pi*2/128;v.append([np.sin(a)*3.7,y*.5,np.cos(a)*3.7]);uv.append([i/128,y/12]);at=y*129+i
  if y<12 and i<128:tri.extend([[at,at+129,at+1],[at+1,at+129,at+130]])
seal=nr.Draw(r,v,tri,uv,np.ones((len(v),4)),D/'Effects/SpiritGlow.png',mode=9,twosided=True)
def save(name,eye,target,t,draw):
 r.begin(np.array(eye),target,t,0,'garden',46);r.geometry();r.framebuffer.depth_mask=False;draw();r.framebuffer.depth_mask=True;nr.Image.frombytes('RGB',(1000,800),r.end()).transpose(nr.Image.Transpose.FLIP_TOP_BOTTOM).save(W/name)
r.actors=[body];body.update('pl00_004',.3,nr.matrix(scale=1.2))
for t in [0,2.1,4.3]:save('palace-seal-'+str(t)+'.png',[8,6,9],[0,1.6,0],t,lambda:seal.render())
def bolt(start,end,width,seed):
 start=np.array(start);end=np.array(end);axis=end-start;normal=axis/np.linalg.norm(axis);across=np.cross(normal,[0,1,0]);across=np.array([1,0,0]) if np.linalg.norm(across)<.1 else across/np.linalg.norm(across);other=np.cross(normal,across);points=[]
 for i in range(17):
  t=i/16;offset=(across*np.sin(i*2.37+seed*3.1)+other*np.sin(i*4.13+seed))*min(.75,np.linalg.norm(axis)*.09)*np.sin(t*np.pi);points.append(start+(end-start)*t+offset)
 for layer in [0,1]:
  vertices=[];uv=[];tri=[];w=width*(3.8 if layer==0 else 1)
  for i,point in enumerate(points):
   tangent=np.array(points[min(16,i+1)])-np.array(points[max(0,i-1)]);side=np.cross(tangent,r.eye-point);side/=np.linalg.norm(side);side*=w*(1-i/16*.55)*.5
   vertices.extend([point-side,point+side]);uv.extend([[0,i/16],[1,i/16]])
   if i<16:tri.extend([[2*i,2*i+1,2*i+2],[2*i+1,2*i+3,2*i+2]])
  ob=nr.Draw(r,vertices,tri,uv,np.ones((34,4)),D/('Effects/SpiritGlow.png' if layer==0 else 'es4a/Texture-0.png'),mode=5,twosided=True);ob.tint=(1,.68,.08) if layer==0 else (1,.96,.65);ob.opacity=.25 if layer==0 else .95;ob.render()
body.visible=False
for side,eye in [('wide',[18,13,19]),('low',[12,3,14])]:
 def draw():
  bolt([0,12,0],[0,.04,0],.32,1)
  for i in range(6):a=i*np.pi/3;bolt([0,8,0],[np.sin(a)*5,.12,np.cos(a)*5],.18,i+3)
  r.sprite('SpiritGlow',np.array([0,.12,0]),13,13,np.array([1,0,0]),np.array([0,0,1]),(1,.85,.25),.75)
 save('charged-thunder-'+side+'.png',eye,[0,3,0],0,draw)
body.visible=True;body.update('pl00_004',.3,nr.matrix([0,3.8,0],scale=1.2))
save('ultimate-gather.png',[11,6,12],[0,3,0],4.8,lambda:r.sprite('OriginalSun',np.array([0,4,0]),9,9,r.right,r.up,(1,.79,.34),.9))
body.update('pl00_004',.3,nr.matrix([0,.8,0],scale=1.2))
save('ultimate-blast.png',[20,18,24],[0,2,0],5.5,lambda:r.sprite('SpiritGlow',np.array([0,2,0]),48,48,r.right,r.up,(1,.79,.34),.65))
print('Seven source-derived stills rendered. Original palette/paint; offline GL, not Unity.')

body.visible=False
blades=r.place('Okami/wp28',[0,3,0],[2.5,.7,8],realm='garden')
for blade in blades:
 blade.root[:3,:3]=np.array([[1,0,0],[0,0,1],[0,-1,0]])
save('eighth-wonder-sword.png',[10,7,12],[0,2.5,0],.6,lambda:None)

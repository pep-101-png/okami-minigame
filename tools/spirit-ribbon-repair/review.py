from pathlib import Path
import sys,numpy as np,shutil,math,json
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'tools/trailer30'));import native_renderer as nr
W=Path('/workspace/work/spirit-ribbon-repair');D=nr.D
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
for clock in [0,.8,1.6,2.4]:
 body.update('pl00_000',clock,nr.matrix(yaw=90,scale=1.2));torso=(body.root@body.transforms[1])[:3,3]
 for i,n in enumerate(ribbons):
  side=-1 if i%2==0 else 1;row=i//2;point=torso+rot@np.array([side*.4,-.015+row*.012,-.30-row*.18]);root=nr.matrix(point,90+180+side*(6+row*4),.86+row*.08);clip='et03_002' if i%2==0 else 'et03_003';pose=n.pose(clip,clock*.32+i*.21)
  if side>0:pose[:,0]*=-1;pose[:,4:6]*=-1
  n.update(clip,0,root,pose=pose)
 for name,(eye,target) in views.items():
  r.actors=[body];r.begin(np.array(eye),target,clock,0,'village',47);r.geometry();r.ctx.depth_mask=False
  for n in ribbons:n.draw()
  r.ctx.depth_mask=True
  nr.Image.frombytes('RGB',(1000,800),r.end()).transpose(nr.Image.Transpose.FLIP_TOP_BOTTOM).save(W/f'{name}-{clock}.png')
print('Twenty offline native-asset views; same alpha/blend limits as the new shader, not Unity')

"""Original 2048px watercolour surface paintings for the new mesh library."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np,json,hashlib
R=Path(__file__).resolve().parents[1];out=R/'Assets/Sunward/Textures/Remake';out.mkdir(exist_ok=True);N=2048;rng=np.random.default_rng(8014)
def field(w=32):
 a=rng.uniform(0,255,(w,w)).astype('uint8');return np.asarray(Image.fromarray(a).resize((N,N),Image.Resampling.BICUBIC),float)/255-.5
low=field(18);fine=field(180);grain=rng.normal(0,1,(N,N));yy,xx=np.mgrid[:N,:N]
colors={'Oak':(148,105,67),'Bark':(119,102,80),'Plaster':(222,213,183),'Roof':(89,108,111),'Stone':(142,155,137),'Earth':(153,141,106),'Meadow':(121,146,87),'Indigo':(83,111,135),'Vermilion':(175,87,65),'Jade':(117,154,134),'Paper':(232,217,175),'Skin':(224,184,150)}
report=[]
for name,col in colors.items():
 wash=low*.28+fine*.08+grain*.009
 if name in ['Oak','Bark']:wash+=np.sin(xx*.017+np.sin(yy*.006)*5+fine*2)*.07+np.sin(xx*.19+low*8)*.016
 if name=='Stone':wash+=np.exp(-np.abs(np.sin(xx*.002+yy*.003+low*3))*18)*-.10
 if name=='Roof':wash+=(np.cos(xx*np.pi/128)*.065+np.sin(yy*np.pi/256)*.04)
 if name in ['Indigo','Vermilion','Jade','Paper']:
  wash+=(np.sin(xx*np.pi)*.009+np.sin(yy*np.pi)*.009)
 a=np.clip(np.array(col)[None,None,:]*(1+wash[:,:,None]),0,255).astype('uint8');im=Image.fromarray(a)
 d=ImageDraw.Draw(im,'RGBA')
 if name in ['Indigo','Vermilion','Jade']:
  for y in range(0,N,256):
   for x in range(0,N,256):
    for ring in range(3):d.arc((x-120-ring*21,y-75-ring*15,x+120+ring*21,y+75+ring*15),180,360,fill=(235,220,181,90),width=3)
  d.rectangle((12,12,N-12,N-12),outline=(225,213,168,180),width=14)
 if name=='Paper':
  for x,y in [(450,1400),(1520,1100),(900,750)]:
   d.line([(x,y+350),(x+25,y),(x-40,y-300)],fill=(65,92,83,120),width=12)
   for j in range(5):d.ellipse((x-100,y-j*90,x+10,y+25-j*90),fill=(75,119,94,95))
 if name in ['Oak','Bark']:
  for k in range(130):
   x=int(rng.integers(0,N));y=int(rng.integers(0,N));d.line([(x,y),(x+int(rng.integers(-10,10)),min(N,y+int(rng.integers(40,320))))],fill=(50,43,35,32),width=int(rng.integers(1,4)))
 p=out/(name+'.png');im.quantize(colors=192,dither=Image.Dither.NONE).save(p,optimize=True)
 gray=np.asarray(im.convert('L').filter(ImageFilter.GaussianBlur(2)),float)/255;dy,dx=np.gradient(gray);normal=np.stack((-dx*2,-dy*2,np.ones_like(dx)),axis=-1);normal/=np.linalg.norm(normal,axis=-1,keepdims=True);nm=Image.fromarray(np.clip((normal*.5+.5)*255,0,255).astype('uint8'));nm.save(out/(name+'-normal.png'),optimize=True)
 report.append({'name':name,'size':[N,N],'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(R/'Review/remake-textures.json').write_text(json.dumps({'origin':'Original generated 2048px watercolour surface artwork; no outside assets','textures':report},indent=2));print('Created',len(report),'colour and normal-data pairs')

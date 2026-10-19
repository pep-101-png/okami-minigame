"""Original 1024px tileable watercolour surface paintings and matching relief maps.
No external artwork, upscaling, or changes to the original wolf/Three.js assets.
"""
from pathlib import Path
from PIL import Image,ImageFilter,ImageDraw
import numpy as np,json,hashlib
R=Path(__file__).resolve().parents[1];out=R/'Assets/Sunward/Textures/Art';out.mkdir(parents=True,exist_ok=True);N=1024;y,x=np.mgrid[0:N,0:N]/N;rng=np.random.default_rng(1968)
def noise(seed):
 r=np.random.default_rng(seed);f=np.zeros((N,N))
 # Periodic Fourier washes avoid seams while keeping long flowing pigment pools.
 for freq,amp in [(1,.3),(2,.23),(4,.17),(8,.1),(16,.06),(32,.04),(64,.025)]:
  for j in range(4):
   a,b=r.integers(-freq,freq+1,2);phase=r.random()*np.pi*2
   f+=amp*np.sin(np.pi*2*(a*x+b*y)+phase)/4
 return f
wash=noise(7);paper=noise(17);fine=rng.normal(0,.012,(N,N));manifest=[]
def save(name,color,height):
 color=np.clip(color,0,1);height=np.asarray(height)
 img=Image.fromarray(np.uint8(color*255),'RGB');path=out/('Paint-'+name+'.png');img.save(path)
 dx=(np.roll(height,-1,1)-np.roll(height,1,1))*9;dy=(np.roll(height,-1,0)-np.roll(height,1,0))*9
 n=np.stack([-dx,-dy,np.ones_like(dx)],axis=-1);n/=np.linalg.norm(n,axis=-1,keepdims=True)
 normal=out/('Paint-'+name+'-normal.png');Image.fromarray(np.uint8(np.clip(n*.5+.5,0,1)*255),'RGB').save(normal)
 manifest.append({'family':name,'color':path.name,'normal':normal.name,'size':[N,N],'source':'original procedural watercolour artwork','sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
# Long brush-drag grain with nested knots, warm translucent pigment and worn fibres.
flow=x*38+.85*np.sin(y*np.pi*2)+.3*np.sin(y*np.pi*8+x*np.pi*2)
grain=np.sin(flow*np.pi*2);rings=np.sin(np.sqrt((np.sin(x*np.pi*2)*1.8)**2+(np.sin(y*np.pi*2)*.6)**2)*90)
wood=.69+.11*wash+.06*grain+.035*rings+fine;save('wood',wood[...,None]*np.array([1.10,.99,.86]),.35*grain+.22*wash+.12*rings)
# Hand-laid ceramic tiles: uneven course lines, dark seams, painted ridge highlights.
u=x*16+.08*np.sin(y*np.pi*8);v=y*12+.03*np.sin(x*np.pi*6);groove=np.exp(-((np.sin(u*np.pi))/.13)**2);course=np.exp(-((np.sin(v*np.pi))/.10)**2)
roof=.74+.12*wash+.08*np.cos(u*np.pi*2)-.27*groove-.14*course+fine;save('roof',roof[...,None]*np.array([.92,1.03,1.08]),.3*np.cos(u*np.pi*2)-groove*.35-course*.15+wash*.05)
# Layered mineral planes, broken brush edges and restrained moss pigment pooling.
crack=np.exp(-((np.sin((x*5+y*3+wash*.4)*np.pi))/.07)**2);stone=.78+.16*wash+.055*paper-crack*.14+fine;moss=np.clip(wash+.12,0,.3)
stonecolor=stone[...,None]*np.array([.97,1.02,1.01]);stonecolor+=moss[...,None]*np.array([-.10,.02,-.09]);save('stone',stonecolor,.35*wash+.1*paper-crack*.16)
# Subtle plaster fibres preserve original wall colours and shoji illustrations.
fibers=np.sin((y*160+.2*np.sin(x*np.pi*6))*np.pi*2)*.015
plaster=.91+.075*wash+.05*paper+fine+fibers;save('plaster',plaster[...,None]*np.array([1.03,1.01,.94]),.15*wash+.14*paper+fibers)
# Broad meadow blooms/moss pigment with short directional hand-painted grass.
strokes=np.sin((x*130+np.sin(y*np.pi*18)) *np.pi*2)*np.maximum(0,np.sin(y*np.pi*96))*.035
meadow=.82+.14*wash+.08*paper+strokes+fine;save('meadow',meadow[...,None]*np.array([.92,1.08,.77]),.2*paper+strokes)
pebbles=np.maximum(0,np.sin(x*np.pi*80)*np.sin(y*np.pi*64))**10
path=.85+.13*wash+.05*paper+fine-pebbles*.12;save('path',path[...,None]*np.array([1.08,1.0,.84]),wash*.12+paper*.12+pebbles*.25)
# Long painted currents with tapered white pigment; animation is supplied by the river shader.
current=np.sin((x*14+.6*np.sin(y*np.pi*8))*np.pi*2)
crest=np.maximum(0,np.sin(y*np.pi*40+np.sin(x*np.pi*12)))**14*np.maximum(0,current)**5
water=np.stack([.35+.42*crest+.05*wash,.66+.25*crest+.06*wash,.66+.20*crest+.04*wash],axis=-1)
save('water',water,.25*current+.3*crest+.12*wash)
# Noren crest: an original sun spiral, brushed border and hanging cloth grain.
cloth=np.clip((.88+.08*paper+fine)[...,None]*np.array([.92,1.02,1.07]),0,1);im=Image.fromarray(np.uint8(cloth*255));d=ImageDraw.Draw(im)
for off in range(9):
 c=(46+off*3,69+off*3,79+off*3);d.arc((285+off,240+off,740-off,695-off),20,335,fill=c,width=3)
pts=[]
for t in np.linspace(0,np.pi*4,280):
 radius=170*(1-t/(np.pi*4));pts.append((512+np.cos(t)*radius,465+np.sin(t)*radius))
d.line(pts,fill=(61,85,91),width=13);d.line([(65,70),(960,70)],fill=(83,105,109),width=10);im.save(out/'Paint-noren.png')
manifest.append({'family':'noren','color':'Paint-noren.png','size':[N,N],'source':'original procedural painted sun-spiral crest','sha256':hashlib.sha256((out/'Paint-noren.png').read_bytes()).hexdigest()})
(R/'Review/windflower-art.json').write_text(json.dumps({'resolution':'1024 x 1024; not 4K','artwork':manifest},indent=2));print('Created',len(manifest),'surface paintings and 6 matching RGB normal data maps')

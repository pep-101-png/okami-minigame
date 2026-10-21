"""Original layered cherry blossom / maple bough paintings for existing canopy cards."""
from pathlib import Path
import math, random
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[2]/'Sunward-Unity/Assets/Sunward/Textures'
def paint(maple=False):
 r=random.Random(212 if maple else 211);im=Image.new('RGBA',(1024,1024));d=ImageDraw.Draw(im)
 # Deliberate radial boughs remain visible between clusters, with asymmetric tips.
 for i in range(11):
  angle=i*math.tau/11;cx=512+math.cos(angle)*r.uniform(200,380);cy=570+math.sin(angle)*r.uniform(150,300)
  d.line([(512,850),(500,590),(cx,cy)],fill=(81,54,56,230),width=8)
 # Scumbled underpainting joins clusters into a readable three-dimensional crown.
 for i in range(130):
  a=r.uniform(0,math.tau);rad=math.sqrt(r.random());cx=512+math.cos(a)*rad*405;cy=480+math.sin(a)*rad*285
  radius=r.uniform(22,65)
  shade=r.choice([(145,70,48,105),(180,99,46,140),(115,83,48,110)]) if maple else r.choice([(197,132,154,110),(229,173,180,150),(245,202,190,120)])
  d.ellipse((cx-radius,cy-radius*.65,cx+radius,cy+radius*.65),fill=shade)
 # Paint individually shaped foreground petals/leaves over the pooled wash.
 for layer in range(3):
  for i in range(220):
   a=r.uniform(0,math.tau);rad=math.sqrt(r.random());cx=512+math.cos(a)*rad*455;cy=480+math.sin(a)*rad*345
   size=r.uniform(10,24) if maple else r.uniform(9,19)
   if maple:
    palette=[(132,57,42),(184,73,39),(219,114,48),(241,159,64),(159,62,42)]
    color=palette[r.randrange(len(palette))];rot=r.uniform(0,math.tau)
    pts=[]
    for j in range(14):
     t=j*math.tau/14+rot;radius=size*((.60+.40*math.sin((j/14)*math.pi)) if j%2==0 else .32)
     pts.append((cx+math.cos(t)*radius,cy+math.sin(t)*radius))
    d.polygon(pts,fill=(*color,245));d.line([(cx,cy+size*.6),(cx,cy-size*.6)],fill=(247,177,89,220),width=1)
   else:
    shade=r.choice([(247,199,192),(255,224,205),(225,153,170),(255,236,217),(238,177,184)])
    for j in range(5):
     angle=j*math.tau/5;px=cx+math.cos(angle)*size*.52;py=cy+math.sin(angle)*size*.52
     d.ellipse((px-size*.46,py-size*.46,px+size*.46,py+size*.46),fill=(*shade,245))
    d.ellipse((cx-2,cy-2,cx+2,cy+2),fill=(166,84,108,240))
 return im
if __name__=='__main__':
 paint().save(ROOT/'map-1.png',optimize=True);paint(True).save(ROOT/'map-3.png',optimize=True)

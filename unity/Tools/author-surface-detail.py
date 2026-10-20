"""Original tileable surface maps. No downloaded/copyrighted photographs.
Height-derived tangent normals, albedo and linear URP metallic/smoothness/AO masks.
"""
from pathlib import Path
import numpy as np
from scipy.ndimage import gaussian_filter
from PIL import Image,ImageDraw
import json
out=Path(__file__).resolve().parents[1]/'Assets/Sunward/Textures/SurfaceDetail';out.mkdir(parents=True,exist_ok=True)
n=1024;rng=np.random.default_rng(7931);y,x=np.mgrid[:n,:n]/n

def noise(s):
 a=gaussian_filter(rng.normal(size=(n,n)),s,mode='wrap');return (a-a.mean())/(a.std()+1e-8)
def save(name,h,c,rough,strength):
 h=np.asarray(h);dx=(np.roll(h,-1,1)-np.roll(h,1,1))*strength;dy=(np.roll(h,-1,0)-np.roll(h,1,0))*strength
 normal=np.stack((-dx,dy,np.ones_like(dx)),2);normal/=np.linalg.norm(normal,axis=2)[...,None]
 Image.fromarray(np.uint8(np.clip(c,0,1)*255),'RGB').save(out/(name+'-Color.png'))
 Image.fromarray(np.uint8(np.clip(normal*.5+.5,0,1)*255),'RGB').save(out/(name+'-Normal.png'))
 ao=np.clip(.90+.12*(h-gaussian_filter(h,14,mode='wrap')), .55,1);mask=np.stack((np.zeros_like(h),ao,np.zeros_like(h),np.clip(1-rough,0,1)),2)
 Image.fromarray(np.uint8(mask*255),'RGBA').save(out/(name+'-Mask.png'))
coarse=noise(27);medium=noise(6);fine=noise(.8)
vein=np.exp(-np.abs(np.sin(x*31.4159+y*18.8496+coarse*.65+medium*.13))*26)
h=.17*coarse+.08*medium+.025*fine-.14*vein
c=np.array([.47,.48,.45])+h[...,None]*.30+noise(2)[...,None]*.022
c+=np.maximum(0,noise(50)-.7)[...,None]*np.array([-.025,.025,-.018])
save('Granite',h,c,.86+.06*np.tanh(fine),20)
warp=.014*noise(30)+.004*noise(8);grain=np.sin((x+warp)*2*np.pi*76);finegrain=np.sin((x+warp*.6)*2*np.pi*213)
knots=np.zeros_like(x)
for cx,cy in [(.22,.3),(.72,.82),(.86,.14)]:
 dx=(x-cx+.5)%1-.5;dy=(y-cy+.5)%1-.5;r=np.sqrt((dx/.05)**2+(dy/.15)**2);knots+=np.exp(-r*r)*np.sin(r*19)
h=.06*grain+.017*finegrain+.028*noise(1)+.045*knots
c=np.array([.34,.22,.13])+h[...,None]*.52+noise(30)[...,None]*.028
save('Cedar',h,c,.75+.1*np.tanh(grain),16)
r=np.sqrt((x-.5)**2+(y-.5)**2);ring=np.sin(r*2*np.pi*36+.9*noise(9));h=.035*ring+.012*fine
c=np.array([.55,.38,.23])+h[...,None]*1.4+noise(20)[...,None]*.02
save('Endgrain',h,c,.82+.05*ring,13)
pebble=np.maximum(noise(2)-.65,0);h=.035*noise(15)+.025*noise(2)+pebble*.06
c=np.array([.36,.30,.22])+noise(25)[...,None]*.035+pebble[...,None]*.09+fine[...,None]*.012
save('Earth',h,c,.95+fine*.018,21)
# Grass is a surface microtexture, not a repeated photo of a whole field.
blade=np.sin((x+.004*noise(8))*np.pi*360)*np.sin(y*np.pi*54)
h=.024*noise(3)+.012*blade+.015*fine
c=np.array([.31,.39,.19])+noise(18)[...,None]*np.array([.025,.03,.018])+h[...,None]*.7
save('Meadow',h,c,.92+fine*.025,18)
# Fine lime plaster and weathered slate, for the existing authored buildings.
h=.015*noise(5)+.008*noise(.8)
c=np.array([.73,.68,.56])+h[...,None]*.55+noise(35)[...,None]*.012
save('Plaster',h,c,.94+fine*.01,14)
rows=y*6;seam=np.exp(-np.minimum(rows%1,1-rows%1)*75)
columns=(x*4+np.floor(rows)%2*.5)%1
crease=np.exp(-np.minimum(columns,1-columns)*55)
h=.045*np.sin(columns*np.pi)-.045*seam-.02*crease+.005*noise(2)
c=np.array([.15,.23,.23])+h[...,None]*.55+noise(18)[...,None]*.012
save('Slate',h,c,.73+.07*np.tanh(noise(4)),15)
# A contact sheet is for inspecting material generation, not a Unity screenshot.
can=Image.new('RGB',(512*5,570),(30,30,30));draw=ImageDraw.Draw(can)
for i,name in enumerate(['Granite','Cedar','Endgrain','Earth','Meadow']):
 can.paste(Image.open(out/(name+'-Color.png')).resize((512,512)),(i*512,35));draw.text((i*512+12,12),name,fill='white')
review=out.parents[3]/'Review';review.mkdir(exist_ok=True);can.save(review/'surface-material-contact-sheet.jpg')
(out/'PROVENANCE.txt').write_text('Original procedural surfaces authored for Sunward. No third-party texture assets.\nColor: sRGB; Normal: tangent-space RGB; Mask: linear R=metallic(0), G=AO, B=0, A=smoothness.\nAll seven sets are tileable 1024x1024 PNGs. They are detailed procedural materials, not photographic scans.\n')
print('Wrote 21 texture maps and contact sheet to',out)

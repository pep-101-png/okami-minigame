"""Original bark knots and four mineral/erosion paintings, at modest 512px resolution."""
from native import *
from PIL import Image,ImageDraw,ImageFilter
from pathlib import Path
N=512;y,x=np.mgrid[:N,:N]/N
TEX=ASSETS/'Textures/VillageFinish'

def save(name,color,height):
 TEX.mkdir(exist_ok=True)
 for suffix,image in [('',Image.fromarray(np.uint8(np.clip(color,0,255)))),('-normal',None)]:
  if image is None:
   dx=(np.roll(height,-1,1)-np.roll(height,1,1))*.08;dy=(np.roll(height,-1,0)-np.roll(height,1,0))*.08;n=np.stack([-dx,-dy,np.ones_like(dx)],-1);n/=np.linalg.norm(n,axis=-1,keepdims=True);image=Image.fromarray(np.uint8((n*.5+.5)*255))
  p=TEX/(name+suffix+'.png');image.save(p,optimize=True)
  template=(ASSETS/f'Textures/Art/Paint-stone{suffix}.png.meta').read_text();g=hashlib.md5(str(p.relative_to(ROOT)).encode()).hexdigest();template=re.sub(r'guid: \w+','guid: '+g,template,count=1);Path(str(p)+'.meta').write_text(template)

def bind(mat,name):
 p=OUT/(mat+'.mat');s=p.read_text()
 for slot,suffix in [('_DetailMap',''),('_DetailNormal','-normal')]:s=re.sub(r'(- '+slot+r':\n        m_Texture: )[^\n]+',r'\g<1>{fileID: 2800000, guid: '+guid(TEX/(name+suffix+'.png'))+', type: 3}',s)
 p.write_text(s)

def main():
 rng=np.random.default_rng(608)
 # Flowed fissures bend around knots rather than repeating vertical plank stripes.
 knots=np.zeros((N,N));warp=np.sin(y*math.tau)*.08
 for cx,cy in [(.25,.3),(.7,.72),(.85,.18)]:
  dx=x-cx;dy=y-cy;warp+=.035*dx/(dx*dx+dy*dy+.015);knots+=np.exp(-(dx*dx/.006+dy*dy/.025))*np.sin(np.sqrt(dx*dx+dy*dy)*230)
 fissure=np.sin((x+warp)*math.tau*23)+.35*np.sin((x+warp)*math.tau*57)
 grain=.6*np.sin(x*173+y*7)+.4*np.sin(x*313-y*19)
 h=fissure*10+knots*13+grain*3
 color=np.array([146,113,77])[None,None,:]+h[:,:,None]*np.array([.9,.85,.7]);save('Bark',color,h);bind('Living-bark','Bark')
 for i,name in enumerate(['sandy','granite','basalt','weathered']):
  wash=np.sin(x*math.tau*3+np.sin(y*math.tau*2))*.6+np.cos(y*math.tau*5+np.sin(x*math.tau*4))*.4
  fine=rng.normal(0,1,(N,N));strata=np.sin((y+.035*np.sin(x*math.tau*2))*math.tau*(18 if i==0 else 9))
  h=wash*6+fine*(3 if i==0 else 1.4)+strata*(3 if i in (0,3) else .8)
  if i==2:h+=np.sin((x+.02*np.sin(y*math.tau*3))*math.tau*8)*5
  base=np.array([(184,166,129),(165,176,177),(137,153,161),(167,163,148)][i]);color=base[None,None,:]+h[:,:,None]
  save('Rock-'+name,color,h);bind('Stone-'+name,'Rock-'+name)
 p=Path(str(TEX)+'.meta');p.write_text('fileFormatVersion: 2\nguid: 28f94687f2a447b0a254e13f9fdb2ae0\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n  userData:\n  assetBundleName:\n  assetBundleVariant:\n')
 print('Authored and bound bark + four rock colour/relief paintings.')
if __name__=='__main__':main()

"""Authored curves, carved stone families, closed roofs and volumetric botany."""
import math,random
import numpy as np
from native import Mesh
TIMBER=(.43,.27,.14);DARK=(.23,.15,.10);PAPER=(.84,.77,.59);SLATE=(.20,.34,.37);STONE=(.40,.44,.41)

def rock(seed):
 r=random.Random(seed);m=Mesh();family=seed%4;n=[24,8,10,16][family];rows=13
 # Distinct low sandstone shelves, angular granite, split basalt, craggy river stone.
 profiles=[[.76,.90,1,.90,.91,.82,.86,.74,.78,.69,.66,.59,.48],
 [.76,.93,.98,1,.99,.97,.96,.92,.88,.85,.81,.74,.65],
 [.77,.87,.91,.94,.97,.94,.92,.88,.86,.81,.73,.65,.54],
 [.72,.88,.95,1,.93,.97,.91,.87,.78,.76,.69,.61,.44]][family]
 heights=np.linspace(0,1,rows)**(1.2 if family==0 else .85 if family==2 else 1)
 colors=[(.65,.55,.38),(.43,.48,.48),(.27,.33,.36),(.49,.46,.41)]
 rings=[]
 for j in range(rows):
  ring=[]
  for k in range(n):
   a=k*math.tau/n;groove=(abs(math.sin(a*3.5+seed))**18)*.10
   rr=profiles[j]*(1+.12*math.sin(a*3+seed)+.045*math.sin(a*7-j*.6)-groove)
   if family==0:rr*=1+.035*math.sin(j*2.7+a*2)
   yy=heights[j]+(.012*math.sin(a*5+j) if j else 0)
   if family in (1,2):yy+=.14*math.cos(a+seed)*(j/(rows-1))**3;rr/=max(abs(math.cos(a)),abs(math.sin(a)))**.65
   tone=1+.07*math.sin(j*2.6+a*2)
   ring.append(m.vertex((math.cos(a)*rr,yy,math.sin(a)*rr),np.array(colors[family])*tone,(k/n,j/rows)))
  rings.append(ring)
 for a,b in zip(rings,rings[1:]):
  for k in range(n):kk=(k+1)%n;m.tri.extend([(a[k],b[k],a[kk]),(a[kk],b[k],b[kk])])
 for ids,rev in [(rings[0],False),(rings[-1],True)]:
  center=m.vertex(np.mean(np.array(m.v)[ids],axis=0),colors[family])
  for k in range(n):m.tri.append((center,ids[(k+1)%n],ids[k]) if rev else (center,ids[k],ids[(k+1)%n]))
 v=np.array(m.v);lo=v.min(0);hi=v.max(0);v=(v-lo)/(hi-lo);v[:,0]-=.5;v[:,2]-=.5;m.v=v.tolist()
 if family in (1,2):
  sharp=Mesh()
  for t in m.tri:sharp.face([m.v[k] for k in t],m.c[t[0]])
  m=sharp
 return m

def tree(seed):
 r=random.Random(seed);wood=Mesh();leaf=Mesh();kind=seed%3
 trunk=[(0,0,0),(.12,.55,.03),(-.08,1.25,.06),(.14,2,.02),(.27,2.8,.05),(.17,3.4,.09),(.32,4.1,.13)]
 wood.tube(trunk,[.30,.25,.20,.17,.13,.09,.025],TIMBER,n=18,groove=.075)
 for i in range(6):
  a=i*math.tau/6;wood.tube([(math.cos(a)*.65,.015,math.sin(a)*.65),(math.cos(a)*.32,.10,math.sin(a)*.32),(.06,.48,0)],[.045,.12,.19],TIMBER,n=10,groove=.08)
 # Growth whorls and off-axis knots are geometry, not painted flat circles.
 for h in [1.0,2.15]:
  points=[(.11+math.cos(a)*.10,h+math.sin(a)*.14,.18) for a in np.linspace(0,math.tau,17)]
  wood.tube(points,[.016]*17,DARK,n=6)
 for i in range(11):
  a=i*2.39996+seed;yy=1.65+i*.17;length=1.65 if i<7 else 1.15
  end=np.array([math.cos(a)*length,yy+.65,math.sin(a)*length])
  start=np.array([.12,yy,.03]);mid=start+(end-start)*.55+np.array([0,-.13,0])
  wood.tube([start,mid,end],[.105,.055,.018],TIMBER,n=12,groove=.06)
  for j in range(3):
   aa=a+(j-1)*.8;tip=end+np.array([math.cos(aa)*.48,.25+j*.04,math.sin(aa)*.48]);wood.tube([end,tip],[.025,.006],TIMBER,n=7)
   for k in range(12 if kind==0 else 28):
    angle=r.uniform(0,math.tau);rad=math.sqrt(r.random());p=tip+np.array([math.cos(angle)*rad*.66,r.uniform(-.18,.28),math.sin(angle)*rad*.52])
    if kind==0:
     # Five cupped petals plus a raised flower centre, each oriented in space.
     pink=r.choice([(.87,.55,.60),(.98,.76,.73),(.98,.86,.78),(.81,.43,.53)])
     for petal in range(5):
      angle=petal*math.tau/5;axis=np.array([math.cos(angle),0,math.sin(angle)]);side=np.array([-math.sin(angle),0,math.cos(angle)])
      center=p+axis*.045+np.array([0,.006,0]);rim=[]
      for k in range(9):
       a=k*math.tau/8;rim.append(p+axis*(.045+math.cos(a)*.052)+side*(math.sin(a)*.033)+np.array([0,.019+.008*math.cos(a),0]))
      for k in range(8):leaf.face([center,rim[k],rim[k+1]],pink)

    else:
     color=r.choice([(.48,.57,.22),(.64,.44,.17),(.36,.50,.22)]) if kind==1 else r.choice([(.16,.36,.27),(.28,.44,.25),(.31,.48,.29)])
     leaf.leaf(p,.20 if kind==1 else .27,.09 if kind==1 else .045,angle,color,tip=.04)
 return wood,leaf

def vegetation(seed,kind='grass'):
 r=random.Random(seed);m=Mesh()
 if kind=='bamboo':
  for j in range(3):
   x=r.uniform(-.27,.27);z=r.uniform(-.22,.22);h=r.uniform(1.7,2.7)
   points=[(x+.02*math.sin(k),k*h/9,z+.015*k) for k in range(10)]
   m.tube(points,[.045-k*.0025 for k in range(10)],(.30,.43,.22),n=10,groove=.025)
   for k in range(1,9):
    y=k*h/9;m.loft([(x,y-.012,z+k*.015,.049,.049),(x,y+.012,z+k*.015,.049,.049)],(.43,.52,.27),n=10)
    if k>3:
     for a in [j*2+k,j*2+k+2.1]:
      p=(x,y,z+k*.015);tip=np.array(p)+np.array([math.cos(a)*.38,.13,math.sin(a)*.38]);m.tube([p,tip],[.014,.005],(.29,.40,.22),n=6)
      for i in range(3):m.leaf(tip,.23,.055,a+i*.45,(.28,.46,.24),tip=-.04)
 elif kind=='flower':
  for j in range(5):
   a=r.uniform(0,math.tau);x=math.cos(a)*r.uniform(.02,.25);z=math.sin(a)*r.uniform(.02,.25);h=r.uniform(.20,.48)
   m.tube([(x,0,z),(x+.03,h*.5,z),(x+.02,h,z+.02)],[.009,.007,.004],(.23,.40,.20),n=6)
   for k in range(3):m.leaf((x,h*(.2+k*.16),z),.16,.06,a+k*2,(.25,.43,.22),tip=.03)
   petal=(.88,.73,.49) if seed%3==0 else (.81,.40,.49) if seed%3==1 else (.83,.84,.73)
   for k in range(6):m.leaf((x+.02,h,z+.02),.074,.049,k*math.tau/6,petal,tip=.01)
   m.ellipsoid((x+.02,h+.014,z+.02),(.019,.018,.019),(.69,.43,.13),n=8,rows=4)
 else:
  for i in range(18):
   a=r.uniform(0,math.tau);rad=r.uniform(.01,.25);p=(math.cos(a)*rad,0,math.sin(a)*rad)
   m.leaf(p,r.uniform(.18,.46),r.uniform(.025,.06),a,r.choice([(.33,.47,.21),(.45,.53,.25),(.28,.42,.23)]),tip=r.uniform(.08,.20))
 return m

def roof(width,depth,eave=2.65):
 m=Mesh();w=width/2+.52;d=depth/2+.48;ridge=eave+1.20
 # Hip roof with thickness and connected fascia; four genuinely closed slopes.
 rows=[(w,d,eave),(w-.08,d-.08,eave+.12),(w*.76,d*.72,eave+.30),(w*.46,d*.34,eave+.72),(w*.30,.08,ridge)]
 rings=[]
 for ww,dd,yy in rows:
  lift=.10 if yy<eave+.2 else .04 if yy<eave+.8 else 0
  rings.append([(-ww,yy+lift,-dd),(0,yy,-dd),(ww,yy+lift,-dd),(ww,yy,0),(ww,yy+lift,dd),(0,yy,dd),(-ww,yy+lift,dd),(-ww,yy,0)])
 for i,(a,b) in enumerate(zip(rings,rings[1:])):
  for k in range(8):m.face([a[k],b[k],b[(k+1)%8],a[(k+1)%8]],np.array(SLATE)*(1+i*.025))
 m.face(rings[0],SLATE);m.face(list(reversed(rings[-1])),SLATE)
 # Individual raised kawara lips follow the same roof surface (no floating tiles).
 for side in (-1,1):
  for zz in np.arange(.12,d-.05,.36):
   def surface(z):
    for aa,bb in zip(rows,rows[1:]):
     if bb[1]<=z<=aa[1]:
      u=(aa[1]-z)/max(.001,aa[1]-bb[1]);return aa[2]+(bb[2]-aa[2])*u,aa[0]+(bb[0]-aa[0])*u
    return ridge,w*.30
   yy,span=surface(zz)
   for x in np.arange(-span+.22,span-.21,.40):
    arc=[(x+u,yy+.016+math.cos(u/.19*math.pi/2)*.028,side*zz) for u in [-.19,-.07,.07,.19]]
    for k in range(3):
     a,b=arc[k],arc[k+1];pts=[a,b,(b[0],b[1]-.018,b[2]+side*.045),(a[0],a[1]-.018,a[2]+side*.045)];m.face(list(reversed(pts)) if side>0 else pts,(.29,.42,.43))
 # Tiled ridge, scalloped eaves and real rafters beneath the roof.
 for x in np.arange(-w*.30,w*.30+.01,.20):m.tube([(x,ridge-.02,-.10),(x,ridge+.10,0),(x,ridge-.02,.10)],[.065,.075,.065],(.27,.40,.41),n=8)
 return m

def house(width,depth,seed,home=False):
 r=random.Random(seed);wood=Mesh();plaster=Mesh();stone=Mesh();roofmesh=roof(width,depth,3.60 if home else 2.65)
 w=width/2;d=depth/2;eave=3.60 if home else 2.65
 # Foundation courses and visible corner timber joinery.
 if not home:
  for x in np.arange(-w+.27,w,.54):
   for z in [-d,d]:stone.box((x,.15,z),(.52,.30,.25),STONE,bevel=.055)
  for z in np.arange(-d+.27,d,.54):
   for x in [-w,w]:stone.box((x,.15,z),(.25,.30,.52),STONE,bevel=.055)
  for x in [-w,w]:
   for z in [-d,d]:wood.box((x,(eave-.04)/2,z),(.16,eave-.04,.17),TIMBER,bevel=.025)
  # Wall panels stop at the beam; inset windows and entry are actual recesses.
  for side in (-1,1):
   z=side*d
   wood.box((0,.49,z),(width,.14,.16),DARK,bevel=.015)
   plaster.box((0,1.16,z),(width-.10,1.25,.12),PAPER,bevel=.025)
   wood.box((0,1.80,z),(width,.13,.17),TIMBER,bevel=.015)
   plaster.box((0,2.18,z),(width-.10,.65,.12),PAPER,bevel=.02)
   for x in np.arange(-w+.4,w-.2,.85):
    wood.box((x,1.17,z+side*.08),(.055,1.18,.10),TIMBER,bevel=.01)
   for x in [-w*.53,w*.53]:
    plaster.box((x,1.38,z+side*.09),(.90,.69,.045),(.70,.68,.50),bevel=.008)
    for k in range(-3,4):wood.box((x+k*.125,1.38,z+side*.135),(.022,.74,.035),DARK,bevel=.003)
    for y in [1.05,1.40,1.73]:wood.box((x,y,z+side*.14),(.96,.025,.04),DARK,bevel=.003)
  for side in (-1,1):
   plaster.box((side*w,1.45,0),(.12,2.2,depth),PAPER,bevel=.025)
   for z in np.arange(-d+.3,d,.85):wood.box((side*(w+.05),1.45,z),(.10,2.35,.065),TIMBER,bevel=.012)
  # Recessed front door and sheltered entry porch.
  front=d+.11;wood.box((0,1.04,front),(.93,1.75,.10),DARK,bevel=.025)
  for x in np.arange(-.4,.41,.10):wood.box((x,1.04,front+.065),(.045,1.69,.04),TIMBER,bevel=.008)
  wood.box((0,.24,d+.39),(1.8,.16,.78),TIMBER,bevel=.025)
  stone.box((0,.085,d+.77),(1.72,.17,.36),STONE,bevel=.04)
 if home:
  for z in [-d,d]:wood.box((0,3.32,z),(width,.35,.16),TIMBER,bevel=.02)
  for x in [-w,w]:wood.box((x,3.32,0),(.16,.35,depth),TIMBER,bevel=.02)
 if not home:
  # Street-facing cloth is folded geometry, with a raised sun crest and hanging rod.
  if seed%3!=2:
   wood.tube([(-.82,2.03,d+.22),(.82,2.03,d+.22)],[.025,.025],TIMBER,n=8)
   color=(.24,.32,.43) if seed%3==0 else (.57,.24,.18)
   for panel in range(3):
    left=-.73+panel*.50
    for row in range(4):
     top=2.0-row*.14;bottom=top-.14
     for col in range(4):
      x0=left+col*.12;x1=x0+.12
      z0=d+.23+.018*math.sin(col*math.pi/2);z1=d+.23+.018*math.sin((col+1)*math.pi/2)
      plaster.face([(x0,bottom,z0),(x1,bottom,z1),(x1,top,z1),(x0,top,z0)],color)
   for t in np.linspace(0,math.tau,24):
    wood.ellipsoid((math.cos(t)*.105,1.80+math.sin(t)*.105,d+.265),(.012,.012,.009),(.70,.48,.18),n=6,rows=3)
  else:
   for row in range(5):
    for side in (-1,1):wood.box((side*(w+.085),.66+row*.12,0),(.035,.10,depth-.2),TIMBER,bevel=.006)
 # Every eave now has continuous, connected beams, rafter ends and roof support.
 for z in [-d,d]:wood.box((0,eave-.10,z),(width+.16,.25,.20),TIMBER,bevel=.025)
 for x in [-w,w]:wood.box((x,eave-.10,0),(.20,.25,depth+.16),TIMBER,bevel=.025)
 for x in np.arange(-w,w+.01,.46):
  for side in (-1,1):wood.tube([(x,eave-.18,side*(d+.45)),(x,eave+.00,side*(d-.25)),(x,eave+.12,side*d*.70)],[.045,.05,.04],DARK,n=8)
 for x in [-w*.72,w*.72]:
  for z in [-d,d]:wood.tube([(x,eave-.50,z),(x,eave-.08,z+.27*(1 if z>0 else -1))],[.055,.055],TIMBER,n=8)
 return wood,plaster,stone,roofmesh

def gate():
 wood=Mesh();metal=Mesh();rope=Mesh()
 for x in [-.90,.90]:
  wood.box((x,1.45,0),(.20,2.90,.22),(.46,.22,.12),bevel=.035)
  wood.box((x,.15,0),(.31,.30,.34),STONE,bevel=.04)
 wood.tube([(-1.24,2.72,0),(0,2.62,0),(1.24,2.72,0)],[.11,.13,.11],TIMBER,n=12)
 wood.box((0,2.19,0),(2.13,.14,.18),TIMBER,bevel=.025)
 # Cast bronze bell: open mouth, visible thick rim, shoulder and attached clapper.
 metal.loft([(0,.99,0,.38,.38),(0,1.06,0,.40,.40),(0,1.16,0,.30,.30),(0,1.57,0,.24,.24),(0,1.72,0,.14,.14)],(.39,.37,.22),n=32,flute=.015)
 points=[(math.sin(a)*.065,1.79+math.cos(a)*.07,0) for a in np.linspace(0,math.tau,21)]
 metal.tube(points,[.015]*21,(.48,.39,.19),n=8)
 metal.loft([(0,.99,0,.35,.35),(0,1.03,0,.35,.35)],(.18,.21,.16),n=32)
 metal.tube([(0,1.03,0),(0,.86,0)],[.035,.055],(.34,.27,.12),n=12)
 for j in range(3):metal.loft([(0,1.28+j*.11,0,.278-j*.012,.278-j*.012),(0,1.30+j*.11,0,.278-j*.012,.278-j*.012)],(.56,.44,.22),n=32)
 rope.tube([(0,2.62,0),(0,1.80,0)],[.035,.035],(.68,.57,.34),n=10,groove=.09)
 rope.tube([(.2,1.0,.16),(.2,.38,.20)],[.025,.032],(.76,.62,.36),n=10,groove=.10)
 return wood,metal,rope

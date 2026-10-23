"""Offline, deterministic Windflower environment details. apply(scene) never saves scene.
Preserves red bridge rails and all existing physics. Native mesh+material assets only.
"""
from pathlib import Path
import importlib.util,sys,math,re,json,random,hashlib,struct,collections
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/village'))
import native
from native import Mesh,Scene,ASSETS,guid,vec,fmt
# build imports village/environment.py; load it before this module is imported as a short name.
from build import Sources
OUT=ASSETS/'Generated/LivingWorld/Environment'
INK=ASSETS/'Generated/InkWorld'
PREFIX='Living detail · '
_SHELL_CACHE={}


def folder(path):
 path.mkdir(parents=True,exist_ok=True)
 meta=Path(str(path)+'.meta')
 if not meta.exists():meta.write_text('fileFormatVersion: 2\nguid: '+hashlib.md5(str(path.relative_to(ROOT)).encode()).hexdigest()+'\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n  userData:\n  assetBundleName:\n  assetBundleVariant:\n')


def material(name,source,tint=None,wind=None,shader=None):
 raw=source.read_text();raw=re.sub(r'm_Name: .*','m_Name: '+name,raw,count=1)
 if tint is not None:raw=re.sub(r'- _BaseColor: .*','- _BaseColor: {r: %g, g: %g, b: %g, a: 1}'%tuple(tint),raw)
 if wind is not None:raw=re.sub(r'- _Wind: .*','- _Wind: '+str(wind),raw)
 if shader:raw=re.sub(r'm_Shader: .*','m_Shader: {fileID: 4800000, guid: '+guid(shader)+', type: 3}',raw,count=1)
 path=OUT/(name+'.mat');path.write_text(raw);return guid(path)


def outline_mesh(path):
 raw=path.read_text();cachekey=(str(path),hashlib.sha256(raw.encode()).hexdigest())
 if cachekey in _SHELL_CACHE:return _SHELL_CACHE[cachekey]
 n=int(re.search(r'm_VertexCount: (\d+)',raw)[1]);data=bytearray.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)',raw)[1]);stride=len(data)//n
 positions=np.array([struct.unpack_from('<3f',data,i*stride) for i in range(n)]);normals=np.array([struct.unpack_from('<3f',data,i*stride+12) for i in range(n)])
 sums=collections.defaultdict(lambda:np.zeros(3))
 for p,normal in zip(positions,normals):sums[tuple(np.round(p*10000).astype(int))]+=normal
 compact=bytearray()
 for p,normal in zip(positions,normals):
  nn=sums[tuple(np.round(p*10000).astype(int))];length=np.linalg.norm(nn)
  if length<1e-8:nn=normal;length=max(np.linalg.norm(normal),1e-8)
  compact.extend(struct.pack('<6f',*p,*(nn/length)))
 raw=re.sub(r'(?m)^    _typelessdata: .*','    _typelessdata: '+compact.hex(),raw);raw=re.sub(r'(?m)^    m_DataSize: .*','    m_DataSize: '+str(len(compact)),raw)
 channels=''.join(f'    - stream: 0\n      offset: {12 if i==1 else 0}\n      format: 0\n      dimension: {3 if i<2 else 0}\n' for i in range(14))
 raw=re.sub(r'    m_Channels:\n.*?(?=    m_DataSize:)', '    m_Channels:\n'+channels,raw,flags=re.S)
 raw=re.sub(r'm_Extent: \{[^}]+\}',lambda m:'m_Extent: '+fmt(vec(m[0],'m_Extent')+.45),raw)
 out=OUT/('Outline-'+path.stem+'.asset');out.write_text(raw);_SHELL_CACHE[cachekey]=guid(out);return _SHELL_CACHE[cachekey]


def add(scene,name,mesh,mat,parent=0,p=(0,0,0),scale=(1,1,1),outline=True,shadow=True):
 obj=scene.add(PREFIX+name,mesh,mat,parent=parent,p=p,scale=scale);r=scene.component(obj,23)
 scene.set(r,'m_CastShadows',1 if shadow else 0)
 if outline:
  path=next(p for p in OUT.glob('*.asset') if guid(p)==mesh)
  shell=scene.add(PREFIX+'ink · '+name,outline_mesh(path),guid(INK/'Ink-contour.mat'),parent=scene.transform(obj))
  renderer=scene.component(shell,23);scene.set(renderer,'m_CastShadows',0);scene.set(renderer,'m_ReceiveShadows',0)
 return obj


def deck():
 mesh=Mesh();rng=random.Random(21103)
 widths=np.array([rng.uniform(.88,1.12) for _ in range(54)]);widths*=9.6/widths.sum();edge=-4.8
 for j,width in enumerate(widths):
  x=edge+width/2;edge+=width;u=(x+4.8)/9.6;y=.10+.42*max(0,math.sin(math.pi*u))**1.5+rng.uniform(-.004,.004)
  start=len(mesh.v);tone=rng.uniform(.86,1.12);color=np.array((.62,.115,.065))*tone
  mesh.box((x,y-.045,0),(width-.006,.09,2.51+rng.uniform(-.025,.025)),color,bevel=.009)
  for line in range(3):
   xx=x+(line-1)*width*.23+rng.uniform(-.008,.008)
   path=[(xx+.004*math.sin(k*1.2+j),y+.001,-1.19+k*2.38/9) for k in range(10)]
   mesh.tube(path,[.0025]*10,(.22,.043,.026),n=3)
  for z in [-rng.uniform(1.02,1.14),rng.uniform(1.02,1.14)]:
   mesh.ellipsoid((x+rng.uniform(-width*.20,width*.20),y+.003,z),(.011,.004,.011),(.12,.09,.07),n=6,rows=3)
  if rng.random()<.24:
   kz=rng.uniform(-.88,.88)
   for radius in [.016,.027]:
    path=[(x+math.sin(a)*radius,y+.003,kz+math.cos(a)*radius*2.7) for a in np.linspace(0,math.tau,17)]
    mesh.tube(path,[.0025]*17,(.19,.04,.022),n=3)
  for k in range(start,len(mesh.v)):
   px,py,pz=mesh.v[k];mesh.v[k]=(px+.0025*math.sin(pz*2+j),py+.002*math.sin(pz*3+j*.7),pz)
 return mesh


def log(seed):
 m=Mesh();rng=random.Random(seed);rings=[]
 for j in range(8):
  y=-.5+j/7;rx=.97*(1+.018*math.sin(j*1.6+seed));rings.append((.013*math.sin(j*.8),y,.013*math.cos(j*.7),rx,rx))
 m.loft(rings,(.35,.21,.11),n=24,flute=.065)
 for k in range(16):
  a=k*math.tau/16+rng.uniform(-.03,.03)
  p=[]
  for j in range(9):
   y=-.49+j*.98/8;angle=a+.026*math.sin(j*.9+k)
   rr=.978*(1+.065*math.cos(angle*8))
   p.append((math.cos(angle)*rr,y,math.sin(angle)*rr))
  m.tube(p,[.012+rng.random()*.005]*9,(.12,.075,.042),n=3)
 # Cut end grain with a warm sapwood ring, heartwood and growth-ring grooves.
 for end in [-1,1]:
  y=end*.504
  ys=sorted([end*.5005,end*.503])
  m.loft([(0,yy,0,.94,.94) for yy in ys],(.65,.45,.23),n=24)
  for radius in [.18,.34,.52,.71,.90]:
   path=[(math.cos(a)*radius*(1+.025*math.sin(a*5+seed)),y,math.sin(a)*radius) for a in np.linspace(0,math.tau,25)]
   m.tube(path,[.009 if radius<.85 else .017]*25,(.19,.105,.047),n=3)
  # Distinctive radial checks at the sawn ends.
  for angle in [seed*.8,seed*.8+2.1,seed*.8+4.2]:
   m.tube([(math.cos(angle)*r,y+.002*end,math.sin(angle)*r) for r in [.52,.67,.92]],[.014,.012,.004],(.105,.065,.03),n=3)
 # Bark knot follows a flattened oval on the visible lateral face.
 for r in [.10,.17,.23]:
  p=[(math.sin(a)*r,.04+math.cos(a)*r*.29,.985+.013*math.sin(a*3)) for a in np.linspace(0,math.tau,19)]
  m.tube(p,[.012]*19,(.14,.085,.04),n=3)
 # Broken, asymmetric sawn lips rather than perfectly level cylinders.
 for i,(x,y,z) in enumerate(m.v):
  if y>.34:
   wave=.045*math.sin(math.atan2(z,x)*3+seed)+.024*math.sin(math.atan2(z,x)*7+seed*.3)
   m.v[i]=(x,y+wave*(y-.34)/.164,z)
 return m


def bamboo(seed):
 rng=random.Random(seed);stem=Mesh();leaves=Mesh();number=rng.randint(8,14)
 for i in range(number):
  a=i*2.399+rng.uniform(-.45,.45);rad=math.sqrt(rng.random())*1.1;x,z=math.cos(a)*rad,math.sin(a)*rad
  h=rng.uniform(2.0,6.4);width=rng.uniform(.028,.075);bend=rng.uniform(.15,.75)
  lean=np.array([math.cos(a+.4)*bend,0,math.sin(a+.4)*bend]);n=rng.randint(7,13)
  heights=np.linspace(0,1,n+1)**rng.uniform(.85,1.15)
  pts=[np.array([x,h*u,z])+lean*u*u+np.array([.025*math.sin(u*4+i),0,.025*math.cos(u*4+i)]) for u in heights]
  colors=[(.25,.39,.13),(.37,.48,.18),(.47,.53,.24),(.24,.36,.16)];color=colors[i%4]
  stem.tube(pts,[width*(1-.65*u) for u in heights],color,n=12,groove=.05)
  for j in range(1,n):
   p=pts[j];r=width*(1-.65*heights[j])*1.17
   stem.loft([(p[0],p[1]-.018,p[2],r,r),(p[0],p[1]+.018,p[2],r,r)],(.61,.64,.34),n=12)
   if j<3:continue
   angle=a+j*2.15+rng.uniform(-.7,.7);length=rng.uniform(.30,.85)*(heights[j]**.5)
   direction=np.array([math.cos(angle),.18,math.sin(angle)]);mid=p+direction*length*.6;tip=p+direction*length+np.array([0,-.10,0])
   stem.tube([p,mid,tip],[.013,.009,.0015],color,n=7)
   for fan in range(2):
    branchangle=angle+(-.7 if fan==0 else .65)
    origin=p+direction*length*(.45+fan*.20);end=origin+np.array([math.cos(branchangle)*.30,.04,math.sin(branchangle)*.30])
    stem.tube([origin,end],[.006,.001],color,n=5)
    for k in range(rng.randint(8,13)):
     u=(k+1)/13;root=origin+(end-origin)*u
     leaves.leaf(root,rng.uniform(.22,.44),rng.uniform(.045,.075),branchangle+(-1 if k%2 else 1)*rng.uniform(.5,1.1),(.24+rng.random()*.18,.38+rng.random()*.19,.10+rng.random()*.09),tip=rng.uniform(-.10,.04))
 # Basal young shoots give the clump a planted, layered silhouette.
 for j in range(5):
  a=rng.random()*math.tau;h=rng.uniform(.3,.9);x,z=math.cos(a)*.8,math.sin(a)*.8
  stem.tube([(x,0,z),(x+.08,h,z+.06)],[.027,.003],(.38,.42,.16),n=9)
 return stem,leaves


def waterfall():
 m=Mesh()
 # Undulating, layered sheet intersects the basin below and has no floating gap.
 for j in range(30):
  t=j/29;y=-.34+t*6.14;z=.12*math.sin(t*math.pi)-.17*t
  for k in range(12):
   u=k/11;x=(u-.5)*2.75*(1+.06*math.sin(t*6+u*2));m.vertex((x,y,z+.035*math.sin(u*29+t*4)),(.58,.81,.72),(u,t))
 for j in range(29):
  for k in range(11):
   a=j*12+k;b=a+12;m.tri.extend([(a,b,a+1),(a+1,b,b+1)])
 return m


def river_x(world_z):
 q=-world_z
 def raw(v):return 1.1*math.sin(v*.13)+.45*math.sin(v*.31)+2*math.exp(-((v+8)/4)**2)
 cross=math.exp(-(26/4)**2);a=(raw(12)-raw(-14)*cross)/(1-cross*cross);b=raw(-14)-a*cross
 return -23+raw(q)-a*math.exp(-((q-12)/4)**2)-b*math.exp(-((q+14)/4)**2)


def replace_material(scene,go,mat):
 r=scene.component(go,23)
 scene.blocks[r]=re.sub(r'  m_Materials:\n.*?(?=  m_StaticBatchInfo:)',f'  m_Materials:\n  - {{fileID: 2100000, guid: {mat}, type: 2}}\n',scene.blocks[r],flags=re.S)


def apply(scene):
 if any(scene.kind(i)==1 and scene.name(i).startswith(PREFIX) for i in scene.blocks):
  return {'alreadyApplied':True}
 for p in [OUT.parent,OUT]:folder(p)
 original_out=native.OUT;native.OUT=OUT
 src=Sources(scene)
 wood=material('Weathered-bridge-cedar',INK/'Ink-painted-timber.mat')
 bark=material('Carved-arena-timber',INK/'Ink-painted-timber.mat')
 leaf=material('Bamboo-varied-leaves',INK/'Ink-living-foliage.mat',wind=.22)
 green=material('Bamboo-golden-jade',INK/'Ink-painted-timber.mat',tint=(.83,.93,.55))
 cliff=material('Cascade-carved-ochre',INK/'Ink-ochre-cliff.mat')
 report={'redBridgeRailsModified':0,'bridgeDecks':0,'arenaLogs':0,'bambooClumps':0,'homeOutlines':0,'waterfallSource':True}
 # Replace only decks; original bridge collision and the praised vermilion rails stay intact.
 new_deck=deck().save('Bridge-sawn-planks')
 for n in [795,800]:src.hide(n)
 for go in list(scene.blocks):
  if scene.kind(go)==1 and scene.name(go)=='Second bridge · solid arched planks':scene.set(go,'m_IsActive',0)
 for z in [-8,14]:add(scene,'jointed bridge boards '+str(z),new_deck,wood,p=(-23,.008,z));report['bridgeDecks']+=1
 logs=[log(610+i).save('Arena-cedar-grain-'+str(i)) for i in range(3)]
 for go in list(scene.blocks):
  if scene.kind(go)!=1:continue
  name=scene.name(go)
  if name.startswith('Arena · full cedar log'):
   index=int(name.rsplit(' ',1)[1]);scene.set(scene.component(go,33),'m_Mesh',f'{{fileID: 4300000, guid: {logs[index%3]}, type: 2}}');replace_material(scene,go,bark)
   child=scene.add(PREFIX+'ink carved arena log '+str(index),outline_mesh(OUT/('Arena-cedar-grain-'+str(index%3)+'.asset')),guid(INK/'Ink-contour.mat'),parent=scene.transform(go))
   scene.set(scene.component(child,23),'m_CastShadows',0);scene.set(scene.component(child,23),'m_ReceiveShadows',0)
   report['arenaLogs']+=1
 # Each placed clump is unique; consistent seed keeps comparisons and positions stable.
 for go in list(scene.blocks):
  if scene.kind(go)!=1 or not scene.name(go).startswith('Living bamboo · '):continue
  index=int(scene.name(go).rsplit(' ',1)[1]);st,le=bamboo(4100+index)
  sg=st.save('Bamboo-'+str(index)+'-culms');lg=le.save('Bamboo-'+str(index)+'-leaf-fans')
  scene.set(scene.component(go,33),'m_Mesh',f'{{fileID: 4300000, guid: {sg}, type: 2}}');replace_material(scene,go,green)
  add(scene,'layered bamboo leaves '+str(index),lg,leaf,parent=scene.transform(go),outline=False,shadow=False)
  child=scene.add(PREFIX+'ink bamboo culms '+str(index),outline_mesh(OUT/('Bamboo-'+str(index)+'-culms.asset')),guid(INK/'Ink-contour.mat'),parent=scene.transform(go))
  scene.set(scene.component(child,23),'m_CastShadows',0);scene.set(scene.component(child,23),'m_ReceiveShadows',0)
  report['bambooClumps']+=1
 # House outlines participate in original home cutaway; no black ghost roof indoors.
 homecut=next(i for i,b in scene.blocks.items() if scene.kind(i)==114 and 'Assembly-CSharp::Sunward.HomeCutaway' in b)
 assetpaths={guid(p):p for p in ASSETS.glob('Generated/**/*.asset') if p.stat().st_size<15_000_000 and not p.name.startswith(('Outline-','Contour-'))}
 for go in list(scene.blocks):
  if scene.kind(go)!=1 or not scene.name(go).startswith('Home · '):continue
  mf=scene.component(go,33)
  if not mf:continue
  g=re.search(r'm_Mesh: .*guid: (\w+)',scene.blocks[mf])[1]
  if g not in assetpaths:continue
  shell=scene.add(PREFIX+'ink Ammy house '+scene.name(go),outline_mesh(assetpaths[g]),guid(INK/'Ink-contour.mat'),parent=scene.transform(go))
  r=scene.component(shell,23);scene.set(r,'m_CastShadows',0);scene.set(r,'m_ReceiveShadows',0)
  scene.blocks[homecut]=scene.blocks[homecut].rstrip()+'\n  - {fileID: '+str(r)+'}\n';report['homeOutlines']+=1
 # Remove the boulder intersecting the mill pillar; retain unrelated bank stones.
 for go in list(scene.blocks):
  if scene.kind(go)!=1 or not scene.name(go).startswith('Grounded stone 104 '):continue
  scene.set(go,'m_IsActive',0);report['millPillarRockRemoved']=scene.name(go)
 # Existing mill power train now also operates a visible rice-pounder and hopper.
 mill=next(i for i in scene.blocks if scene.kind(i)==1 and scene.name(i)=='River-driven rice mill · supported short transmission')
 mill_t=scene.transform(mill)
 mortar=Mesh();mortar.loft([(0,0,0,.34,.34),(0,.10,0,.39,.39),(0,.37,0,.37,.37),(0,.42,0,.30,.30)],(.38,.31,.21),n=18,flute=.04)
 mortar_g=mortar.save('Mill-rice-mortar');add(scene,'rice pounding mortar',mortar_g,cliff,parent=mill_t,p=(3.85,-.75,-.65))
 pestle=Mesh();pestle.tube([(0,-.24,0),(0,.31,0),(0,.76,0)],[.10,.075,.055],(.48,.29,.12),n=10,groove=.09)
 pestle_g=pestle.save('Mill-cam-pestle');pestle_go=add(scene,'wheel driven rice pestle',pestle_g,wood,parent=mill_t,p=(3.85,-.12,-.65))
 hopper=Mesh()
 for side in [-1,1]:
  hopper.box((side*.29,.17,0),(.07,.38,.58),(.48,.30,.14),bevel=.025)
  hopper.box((0,.17,side*.29),(.58,.38,.07),(.48,.30,.14),bevel=.025)
 hopper.box((0,-.01,0),(.62,.045,.62),(.33,.21,.11),bevel=.015)
 hopper_g=hopper.save('Mill-rice-hopper');add(scene,'rice hopper and open feed',hopper_g,wood,parent=mill_t,p=(2.9,.50,0))
 rice=Mesh();rice.ellipsoid((0,0,0),(.023,.042,.016),(.91,.81,.48),n=6,rows=4);rice_g=rice.save('Mill-paddy-grain')
 grain=[]
 for i in range(8):
  go=add(scene,'falling rice grain '+str(i),rice_g,wood,parent=mill_t,p=(2.9+(i%3-1)*.035,.43-(i/8)*.39,(i%2-.5)*.03),outline=False,shadow=False);grain.append(scene.transform(go))
 component=next(i for i,b in scene.blocks.items() if scene.kind(i)==114 and 'Assembly-CSharp::Sunward.WaterMillMotion' in b)
 scene.blocks[component]=scene.blocks[component].rstrip()+'\n  pestle: {fileID: '+str(scene.transform(pestle_go))+'}\n  grainDrops:\n'+''.join('  - {fileID: '+str(t)+'}\n' for t in grain)
 # Source rock physics is a separate original proxy. Clear exactly the intersecting stone.
 for go in list(scene.blocks):
  if scene.kind(go)!=1 or scene.name(go)!='Trunk / rock collider':continue
  p=vec(scene.blocks[scene.transform(go)],'m_LocalPosition')
  if abs(p[0]+20.175206)<.08 and abs(p[2]-6.7)<.08:
   for c in scene.refs(go):
    if scene.kind(c) in [65,136]:scene.disabled(c)
 report['ricePestleDrivenByWheel']=True;report['fallingGrains']=len(grain)
 # The old stationary waterfall cards were centred on the wrong river reach.
 for n in [785,786]:src.hide(n)
 x,z=river_x(43.4),43.4
 sheet=waterfall().save('Cascade-layered-sheet')
 water=material('Animated-cascade',INK/'Ink-living-foliage.mat',shader=ASSETS/'Shaders/LivingCascade.shader')
 add(scene,'riverhead flowing cascade',sheet,water,p=(x,0,z),outline=False,shadow=False)
 # Source cliff with a deliberate spillway notch. Lower tiers seat below water.
 rocks=Mesh();rng=random.Random(3316)
 for side in [-1,1]:
  rings=[]
  heights=[-.72,-.22,.08,.70,1.04,1.65,2.12,2.55,3.18,3.70,4.15,4.72,5.20,5.65,6.18,6.65]
  for level,cy in enumerate(heights):
   # Continuous eroded escarpment: re-entrant shelves, non-parallel facets and
   # a strong buried base, without repeated floating seam strips.
   radius=.73+.12*math.sin(level*1.79+side)
   cx=side*(1.91+.10*math.sin(level*.91));cz=1.20+.10*math.cos(level*1.13)
   rings.append((cx,cy,cz,radius,1.30+.12*math.sin(level*1.5)))
  rocks.loft(rings,(.55,.44,.24),n=11,flute=.10)
 rocks.box((0,5.65,1.35),(2.4,.36,2.5),(.53,.44,.28),bevel=.1)
 # Feeder emerges from a dark cleft in the headwall, not a floating ribbon.
 rocks.box((0,6.42,2.64),(4.4,.82,.72),(.50,.41,.26),bevel=.16)
 for side in [-1,1]:rocks.box((side*1.49,5.91,2.63),(.72,1.0,.76),(.49,.40,.25),bevel=.12)
 rocks.box((0,5.95,2.81),(2.15,.66,.10),(.095,.12,.10),bevel=.025)
 rockg=rocks.save('Cascade-sculpted-source-cliff');add(scene,'riverhead source cliff',rockg,cliff,p=(x,0,z))
 # A visible upstream feeder, immediately behind the spillway, explains the water.
 feed=Mesh();feed.face([(-1.27,5.84,.20),(-1.23,5.84,2.88),(1.23,5.84,2.88),(1.27,5.84,.20)],(.48,.75,.65))
 # Waterfall shader uses authored UV; feeder supplies its own stream UV.
 feedg=feed.save('Cascade-upper-feeder');add(scene,'upper spring channel',feedg,water,p=(x,0,z),outline=False,shadow=False)
 report['waterfallPosition']=[x,0,z];report['riverAtSourceX']=x
 (ROOT/'tools/living-world/environment-report.json').write_text(json.dumps(report,indent=2)+'\n')
 native.OUT=original_out
 return report

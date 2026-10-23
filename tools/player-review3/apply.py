"""Saved-scene corrections after Player Fixes 2. Never executed at runtime."""
from pathlib import Path
import sys,re,math,random,struct,hashlib,importlib.util,json
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools/player-review'))
from scene_tools import *
from build import Sources
import native
OUT=ASSETS/'Generated/PlayerReview3'

def load(name,path):
 spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def read_mesh(path):
 s=path.read_text();n=int(re.search(r'm_VertexCount: (\d+)',s)[1]);buf=bytes.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)',s)[1]);stride=len(buf)//n;m=Mesh()
 for i in range(n):
  p=struct.unpack_from('<3f',buf,i*stride);c=struct.unpack_from('<3f',buf,i*stride+24) if stride>=48 else (1,1,1);uv=struct.unpack_from('<2f',buf,i*stride+40) if stride>=48 else (0,0);m.vertex(p,c,uv)
 ix=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-fA-F]+)',s)[1]),dtype='<u4' if 'm_IndexFormat: 1' in s else '<u2');m.tri=[tuple(t) for t in ix.reshape(-1,3)]
 return m

def root_buttresses(seed,color):
 rng=random.Random(seed);m=Mesh();color=np.array(color)
 for j in range(rng.randint(5,8)):
  a=j*2.399+seed*.12;axis=np.array([math.cos(a),0,math.sin(a)]);side=np.array([-math.sin(a),0,math.cos(a)]);length=rng.uniform(.90,1.8)
  pts=[];radii=[]
  for k in range(14):
   u=k/13;r=.12+length*u;y=.54*(1-u)**2-.06*u
   pts.append(axis*r+side*(math.sin(u*math.pi)*rng.uniform(.03,.12))+np.array([-.10,y,.02]));radii.append(.19*(1-u)**1.15+.003)
  m.tube(pts,radii,color*rng.uniform(.92,1.08),n=14,groove=.14)
  # Thin longitudinal bark seams follow the curved growth, not flat fins.
  for off in [-.045,.045]:
   groove=[np.array(p)+side*off+np.array([0,r*.92,0]) for p,r in zip(pts,radii)]
   m.tube(groove,[max(.001,r*.04) for r in radii],color*.54,n=5)
  if j%2==0:
   fork=pts[7];direction=axis*.7+side*rng.uniform(-.8,.8)
   m.tube([fork,fork+direction*.35+np.array([0,-.08,0]),fork+direction*.68+np.array([0,-.15,0])],[.065,.035,.003],color*.95,n=10,groove=.12)
 return m

def replace_flat_root_components(m):
 # Tubes are disconnected mesh islands. Remove whole low root islands while
 # retaining the continuous main trunk, including its original grounded base.
 v=np.array(m.v);parents=list(range(len(v)))
 def find(a):
  while parents[a]!=a:parents[a]=parents[parents[a]];a=parents[a]
  return a
 for a,b,c in m.tri:
  for x,y in [(a,b),(b,c)]:
   x,y=find(x),find(y)
   if x!=y:parents[y]=x
 groups={}
 for i,p in enumerate(v):groups.setdefault(find(i),[]).append(i)
 remove=set()
 for key,ids in groups.items():
  vv=v[ids]
  if vv[:,1].max()<.95 and np.linalg.norm(vv[:,[0,2]],axis=1).max()>.42:remove.add(key)
 m.tri=[t for t in m.tri if find(t[0]) not in remove]
 return m

def apply(s):
 OUT.mkdir(exist_ok=True);native.OUT=OUT
 Path(str(OUT)+'.meta').write_text('fileFormatVersion: 2\nguid: '+hashlib.md5(str(OUT.relative_to(ROOT)).encode()).hexdigest()+'\nfolderAsset: yes\nDefaultImporter:\n  externalObjects: {}\n')
 src=Sources(s);index=asset_index();cache={};report={}
 # The source model has one combined black-ink mesh. Hiding a replacement
 # stone/stall never hid the corresponding old ink faces in that shared mesh.
 import build as source_tools
 source_tools.OUT=OUT
 def old_ink_region(v):
  market=(abs(v[:,:,0])<6.3)&(v[:,:,2]>-8)&(v[:,:,2]<7)&(v[:,:,1]>-.3)&(v[:,:,1]<3.4)
  mill=(v[:,:,0]>-31)&(v[:,:,0]<-17)&(v[:,:,2]>3)&(v[:,:,2]<12)&(v[:,:,1]>-2)&(v[:,:,1]<4)
  return market|mill
 report['orphanedLegacyInkTrianglesRemoved']=src.trim_region(349,old_ink_region,'Legacy-ink-cleared-market-mill')
 # The imported combined ink mesh had stale bounds; keep every retained vertex
 # inside both its mesh/submesh bounds after writing a standalone native asset.
 trimmed=OUT/'Legacy-ink-cleared-market-mill-349.asset';v=src.positions(349)
 raw=trimmed.read_text();raw=re.sub(r'm_Center: \{[^}]+\}','m_Center: '+fmt((v.min(0)+v.max(0))/2),raw);raw=re.sub(r'm_Extent: \{[^}]+\}','m_Extent: '+fmt((v.max(0)-v.min(0))/2),raw);trimmed.write_text('\n'.join(line.rstrip() for line in raw.splitlines())+'\n')
 for n in [374,375]:src.hide(n)
 if 349 in src.objects:src.patch(src.prefab.component(src.objects[349],23),'m_CastShadows',0)

 ink=load('review3_ink',ROOT/'tools/ink-world/apply.py');ink.OUT=OUT
 def save(m,name):p=OUT/(name+'.asset');m.write(p);return guid(p)
 def add(name,m,mat,p=(0,0,0),parent=0,outline=True):
  g=save(m,name);go=s.add('Review 3 · '+name,g,mat,p=p,parent=parent)
  if outline:
   child=s.add('Review 3 ink · '+name,ink.shell_mesh(OUT/(name+'.asset'),{}),guid(ASSETS/'Generated/InkWorld/Ink-contour.mat'),parent=s.transform(go));s.set(s.component(child,23),'m_CastShadows',0)
  return go
 wood=guid(ASSETS/'Generated/InkWorld/Ink-painted-timber.mat')
 # Replace tiny detached roots with buttresses joined into each real trunk mesh.
 for go in list(s.blocks):
  if s.kind(go)==1 and s.name(go).startswith(('Review 2 · rooted tree transition','Review 2 · leaf litter')):s.set(go,'m_IsActive',0)
 trees=0
 for go in list(s.blocks):
  if s.kind(go)!=1 or not s.name(go).startswith('Living tree ') or 'bark and branching' not in s.name(go):continue
  mf=s.component(go,33);g=re.search(r'guid: (\w+)',s.blocks[mf])[1];m=read_mesh(index[g]);v=np.array(m.v);c=np.array(m.c);low=v[:,1]<.75;palette=np.mean(c[low],axis=0) if low.any() else np.array([.26,.16,.08])
  # Retire the original flat fan roots before growing rounded, branching roots.
  replace_flat_root_components(m)
  base=len(m.v);m.merge(root_buttresses(1000+trees,palette))
  w=world(s,s.transform(go),{});sy=np.linalg.norm(w[:3,1]);p=w[:3,3]
  for k in range(base,len(m.v)):
   v=np.array(m.v[k]);q=(w@np.append(v,1))[:3];v[1]+=(src.ground(q[0],q[2])+.02-p[1])/sy;m.v[k]=tuple(v)
  mg=save(m,'Rooted-trunk-'+str(trees));s.set(mf,'m_Mesh','{fileID: 4300000, guid: '+mg+', type: 2}')
  for c in list(s.blocks):
   if s.kind(c)==4 and parent(s,c)==s.transform(go):
    child=s.owner(c);cm=s.component(child,33)
    if cm:s.set(cm,'m_Mesh','{fileID: 4300000, guid: '+ink.shell_mesh(OUT/('Rooted-trunk-'+str(trees)+'.asset'),{})+', type: 2}')
  litter=Mesh();rng=random.Random(400+trees)
  for k in range(30):
   a=rng.random()*math.tau;r=rng.uniform(.45,1.6);x,z=p[0]+math.cos(a)*r,p[2]+math.sin(a)*r
   litter.leaf((x,src.ground(x,z)+.028,z),rng.uniform(.11,.24),.07,a,(.44,.32,.13) if k%3 else (.31,.39,.13),tip=.015)
  add('root leaf scatter '+str(trees),litter,guid(ASSETS/'Generated/InkWorld/Ink-living-foliage.mat'),outline=False);trees+=1
 report['integratedRootedTrunks']=trees
 # Anchor fascia to the actual wall, not the roof's overhang. Add attached corbels.
 arches=0
 for go in list(s.blocks):
  if s.kind(go)!=1 or not s.name(go).startswith('Ink world · curved entrance fascia'):continue
  t=s.transform(go);roof=parent(s,t);owner=s.name(s.owner(roof));number=re.search(r'Village house (\d+)',owner)
  if not number:continue
  wall=next((i for i in s.blocks if s.kind(i)==1 and s.name(i).startswith('Village house '+number[1]+' · recessed')),None)
  if wall is None:continue
  g=re.search(r'guid: (\w+)',s.blocks[s.component(wall,33)])[1];raw=index[g].read_text();front=vec(raw,'m_Center')[2]+vec(raw,'m_Extent')[2]
  s.set(t,'m_LocalPosition',fmt((0,2.25,front+.025)));s.set(t,'m_LocalScale',fmt((1,.55,1)));arches+=1
  if 'Gable-timber' not in index[re.search(r'guid: (\w+)',s.blocks[s.component(go,33)])[1]].name:continue
  supports=Mesh()
  for x in [-.83,.83]:
   supports.box((x,2.10,0),(.13,.55,.20),(.36,.20,.095),bevel=.018)
   supports.tube([(x,1.94,-.08),(x,2.19,.10),(x,2.30,.12)],[.045,.055,.03],(.38,.22,.11),n=9)
  add('wall anchored doorway supports '+number[1],supports,wood,p=(0,0,front-.035),parent=roof)
 report['wallAnchoredFasciaParts']=arches
 # A complete coloured festival canopy, with supports in the clear inner lane.
 for go in list(s.blocks):
  if s.kind(go)!=1:continue
  if s.name(go).startswith(('Living places · market supported lantern posts','Living places · market sagging lantern rope')):s.set(go,'m_IsActive',0)
  if s.name(go).startswith('Living places · evening lantern '):
   n=s.name(go).rsplit(' ',1)[-1]
   if n.isdigit() and int(n)<4:
    root=s.transform(go)
    for child in list(s.blocks):
     if s.kind(child)!=1:continue
     t=s.transform(child)
     while t and t!=root:t=parent(s,t)
     if t==root:
      renderer=s.component(child,23)
      if renderer:s.set(renderer,'m_Enabled',0)
 paper=ASSETS/'Generated/LivingPlaces/Evening-glowing-paper.mat';raw=paper.read_text();raw=re.sub(r'- _BaseColor: .*','- _BaseColor: {r: 1, g: 1, b: 1, a: 1}',raw);paper.write_text(raw);pm=guid(paper)
 colors=[(.92,.18,.12),(.24,.56,.70),(.72,.30,.50),(.86,.62,.16),(.31,.62,.34),(.55,.37,.71)]
 for row,z in enumerate([-5.7,0,5.2]):
  posts=Mesh();rope=Mesh()
  for x in [-3.06,3.06]:
   posts.tube([(x,0,0),(x,3.8,0)],[.075,.055],(.40,.24,.11),n=12,groove=.1);posts.box((x,.10,0),(.24,.20,.24),(.13,.09,.06),bevel=.025)
   posts.loft([(x,3.76,0,.11,.11),(x,3.84,0,.07,.07)],(.66,.13,.07),n=12)
  pts=[(x,3.45+.32*(x/3.06)**2,0) for x in np.linspace(-3.06,3.06,40)];rope.tube(pts,[.015]*40,(.13,.09,.06),n=7)
  add('festival posts '+str(row),posts,wood,p=(0,0,z));add('festival rope '+str(row),rope,wood,p=(0,0,z),outline=False)
  for j,x in enumerate(np.linspace(-2.65,2.65,8)):
   c=colors[(j+row*2)%6];m=Mesh();radius=.15+(.025 if j%3==0 else 0);height=.38+(j%3)*.06
   m.loft([(0,-height/2,0,radius*.55,radius*.55),(0,-height*.37,0,radius*.90,radius*.90),(0,0,0,radius,radius),(0,height*.37,0,radius*.90,radius*.90),(0,height/2,0,radius*.55,radius*.55)],c,n=20,flute=.025)
   top=3.45+.32*(x/3.06)**2;y=top-.17-height/2
   lantern=add('coloured festival lantern '+str(row*8+j),m,pm,p=(x,y,z),outline=False)
   trim=Mesh();trim.tube([(0,height/2,0),(0,height/2+.17,0)],[.007,.007],(.15,.08,.045),n=5)
   for yy in [-height/2,height/2]:trim.loft([(0,yy-.012,0,radius*.60,radius*.60),(0,yy+.012,0,radius*.60,radius*.60)],(.43,.085,.045),n=20)
   # Fine curved ribs and small brush crest retain form by day, colour by night.
   for k in range(8):
    a=k*math.tau/8;trim.tube([(math.cos(a)*radius*r,yy,math.sin(a)*radius*r) for yy,r in [(-height/2,.55),(0,1),(height/2,.55)]],[.0025]*3,(.22,.12,.08),n=4)
   add('festival lantern ribs '+str(row*8+j),trim,wood,parent=s.transform(lantern),outline=False)
 report['colouredMarketLanterns']=24
 # Remove remaining stone shadows from the mill's immediate surroundings.
 nearby=0
 for go in list(s.blocks):
  if s.kind(go)!=1 or not active(s,go) or not s.name(go).startswith('Grounded stone '):continue
  t=s.transform(go);p=world(s,t,{})[:3,3]
  if abs(p[0]+27)<6 and abs(p[2]-8)<6:
   r=s.component(go,23)
   if r:s.set(r,'m_CastShadows',0);nearby+=1
 floor=Mesh()
 for j in range(13):floor.box(((j-6)*.43,.015,0),(.415,.035,4.35),(.40,.25,.12),bevel=.006)
 add('rice mill joined plank floor',floor,wood,p=(-27.16,.065,8),outline=False)
 report['nearMillStoneShadowCastersDisabled']=nearby
 # Authored ivory cloud fur for the temporary P-key visual form.
 mane=Mesh();rng=random.Random(333)
 for side in [-1,1]:
  for j in range(6):
   z=.38-j*.14;h=1.38-j*.035;x=side*(.20+j*.012)
   controls=np.array([(x,h,z),(side*(.39+j*.012),h+.18,z-.18),(side*(.46+j*.012),h+.21,z-.42),(side*(.35+j*.012),h+.20,z-.70)])
   pts=[];radii=[]
   for k in range(18):
    u=k/17;pts.append((1-u)**3*controls[0]+3*(1-u)**2*u*controls[1]+3*(1-u)*u*u*controls[2]+u**3*controls[3]);radii.append(.075*(1-u)**.85+.001)
   mane.tube(pts,radii,(.97,.94,.83),n=14,groove=.035)
 mg=save(mane,'Shiranui-ivory-cloud-mane');mp=OUT/'Shiranui-ivory.mat';raw=(ASSETS/'Generated/LivingCombat/Spirit-painted.mat').read_text();raw=re.sub(r'm_Name: .*','m_Name: Shiranui-ivory',raw,count=1);raw=re.sub(r'- _BaseColor: .*','- _BaseColor: {r: 1, g: 1, b: 1, a: 1}',raw);mp.write_text(raw)
 growth=next(i for i,b in s.blocks.items() if s.kind(i)==114 and 'Assembly-CSharp::Sunward.DivineGrowth\n' in b)
 s.blocks[growth]=s.blocks[growth].rstrip()+'\n  shiranuiMane: {fileID: 4300000, guid: '+mg+', type: 2}\n  shiranuiMaterial: {fileID: 2100000, guid: '+guid(mp)+', type: 2}\n'
 # Generated objects have no thin mesh shadows; no runtime rebuild is required.
 for r,b in list(s.blocks.items()):
  if s.kind(r)==23 and s.name(s.owner(r)).startswith(('Review 3 · coloured','Review 3 · festival')):s.set(r,'m_CastShadows',0)
 report['temporaryShiranuiManeBound']=True
 return report

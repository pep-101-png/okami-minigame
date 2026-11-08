"""Thirty-second edit: native poses, source scene, directed cinematic cameras."""
from native_renderer import *
class Director:
 cuts=[0,2.5,4.5,6.5,8,10,12.8,14.2,16.2,18.8,21,23.5,25.5,28.5,30]
 names=['intro','village','farm','festival','race','tundra','instrument','heaven','shiranui','boss-armour','boss-storm','victory','moon-howl','outro']
 def __init__(self,r,out):
  self.r=r;self.out=out;self.world=json.loads((A/'Sunward/Data/Valley.json').read_text())['world'];self.actors=[];self.npcs=[];self.particles=[]
  self.hero=self.actor('NativePlayer/pl00');self.spirit=self.actor('Okami/pl0d');self.beads=self.actor('Okami/wp2e');self.sword=self.actor('Okami/wp29');self.imps=[self.actor('Okami/em00',.8612828629880562*.76,(-.00849,.07094,-.27517)) for _ in range(2)];self.boss=self.actor('Okami/em11',.2114521888*2.75,(-.01578,.00157,.06323));self.armour=self.actor('Okami/crimson-armour',.2114521888*2.75,(-.01578,.00157,.06323));self.boss.groups={0,2};self.armour.groups=set(g for g,_ in self.armour.parts);self.load_npcs();self.build_farm();self.build_festival();self.build_garden();self.stand=r.place('vt0a',(35, self.h(35,-3),-3),(1,.5,1));print('Ready native actors',len(r.actors),'scene parts',len(r.static),flush=True)
 def actor(self,resource,scale=1,offset=(0,0,0)):
  n=Native(self.r,resource,scale,offset);self.r.actors.append(n);return n
 def h(self,x,z):
  t=self.world['terrain'];fx=np.clip((x-t['minX'])/t['step'],0,t['nx']-1.001);fz=np.clip((-z-t['minZ'])/t['step'],0,t['nz']-1.001);ix,iz=int(fx),int(fz);u,v=fx-ix,fz-iz;a=np.asarray(t['heights']).reshape(t['nz'],t['nx']);return float(a[iz,ix]*(1-u)*(1-v)+a[iz,ix+1]*u*(1-v)+a[iz+1,ix]*(1-u)*v+a[iz+1,ix+1]*u*v)
 def pos(self,x,z,lift=0):return [x,self.h(x,z)+lift,z]
 def load_npcs(self):
  w=self.r.w;s=w.scene
  for instance,source in [(0,s),*w.prefabs.items()]:
   for cid,b in source.blocks.items():
    if 'Assembly-CSharp::Sunward.Remaster.OriginalActor\n' not in b or '  m_Enabled: 0\n' in b:continue
    go=source.owner(cid)
    if not w.active(instance,go):continue
    root=w.matrix(instance,source.transform(go))
    if root[1,3]<-5:continue
    resource=re.search(r'  resource: (.+)',b)[1];idle=re.search(r'  idle: (.+)',b)[1]
    try:actor=self.actor(resource,float(re.search(r'  modelScale: (.+)',b)[1]),vec(b,'modelOffset'))
    except StopIteration:continue
    self.npcs.append((actor,idle,root))
 def prop(self,res,p,size,yaw=0,realm='village'):
  return self.r.place(res,self.pos(p[0],p[1]),size,yaw,realm)
 def rail(self,x,z,width,yaw,height=.85):
  count=math.ceil(width/2.2);span=width/count;angle=math.radians(yaw)
  for i in range(count):
   a=-width/2+span*(i+.5);self.prop('farm-rail',(x+a*math.cos(angle),z-a*math.sin(angle)),(span,height,.18),yaw)
 def build_farm(self):
  for x0,x1,z0,z1,opening in [(15.5,23,27.8,36.5,2.1),(24,35,27.8,40,2.4),(37,43,28,40,1.5),(45,50,29,40,1.5),(51,57,28.5,34,1.2)]:
   mid=(x0+x1)/2;w=x1-x0;d=z1-z0;self.rail(mid,z1,w,0);self.rail(x0,(z0+z1)/2,d,90);self.rail(x1,(z0+z1)/2,d,90);half=(w-opening)/2;self.rail(x0+half/2,z0,half,0);self.rail(x1-half/2,z0,half,0)
  for x,z,width,depth,head in [(29.5,36,7.4,7.3,3.15),(47.5,37.3,2.8,2.76,.57),(54,32.4,2.4,2.36,.35),(54,38.5,4.8,4.74,1.7)]:
   self.r.place('farm-pitched-roof',self.pos(x,z,head),(width,width*.315,depth))
   for a in [-1,1]:
    for b in [-1,1]:self.prop('farm-post',(x+a*width*.35,z+b*depth*.35),(.22,head,.22))
  for x,z in [(25.4,29),(38.3,30),(46,30.8),(52,30)]:self.prop('vt49',(x,z),(.8,.4,.8));self.prop('et2b',(x,z+1.1),(.65,.58,.65));self.prop('vt5e',(x+1.1,z),(.8,.32,.65))
 def build_festival(self):
  self.lanterns=[]
  for row in range(6):
   z=-11+row*4.2;y=self.h(0,z)
   for side in [-1,1]:self.lanterns+=self.r.place('vt00',(side*3.8,y,z),(.16,4.8,.16))
   self.lanterns+=self.r.place('et03',(0,y+4.6,z),(7.6,.025,.025))
   for i in range(5):
    x=-2.6+i*1.3;self.lanterns+=self.r.place(['vt33','vt34','vt32'][(row+i)%3],(x,y+3.822,z),(.42,.56,.42))
  for ob in self.lanterns:ob.visible=False
 def garden_height(self,x,z):
  a,b,c,det=self.surface;valid=abs(det)>1e-8;dx=x-a[:,0];dz=z-a[:,2];u=np.divide(dx*c[:,2]-dz*c[:,0],det,out=np.full(len(a),-1.),where=valid);v=np.divide(b[:,0]*dz-b[:,2]*dx,det,out=np.full(len(a),-1.),where=valid);hit=valid&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1.000001);return float(np.max((a[:,1]+u*b[:,1]+v*c[:,1])[hit])) if hit.any() else -.2
 def build_garden(self):
  # Bake the runtime's native-paint blend; no new illustration or source asset.
  source=(ROOT/'tools/heaven-palace/render.py').read_text();sample=source[source.index('def sample('):source.index('def floor_material(')];fun=source[source.index('def floor_material('):source.index('terrain_material=floor_material')];fun=fun[:fun.index(' mat=texture_material')]+ ' return target\n';layout=json.loads((D/'CelestialGarden.json').read_text());scope=dict(np=np,Image=Image,D=D,OUT=self.out,layout=layout);exec(sample+'\n'+fun,scope);paint=scope['floor_material'](1,90,1024);triangles=[]
  def place(item):
   p=np.array(list(item['position'].values()),float);size=list(item['size'].values());kind=item['kind'];res=item['resource'];terrain=kind=='ground' and res.split('/')[-1] in ['celestial-meadow','celestial-terrace','celestial-grounded','heaven-basin-terrain']
   if kind not in ['ground','cloud','cloudsea'] and not item.get('absoluteHeight'):p[1]+=self.garden_height(p[0],p[2])+.005
   mode=3 if terrain else 7 if kind in ['cloud','cloudsea'] else 0;obs=self.r.place(res,p,size,item.get('yaw',0),'garden',mode,paint if terrain else None)
   if terrain:
    for ob in obs:triangles.extend((ob.vertices@ob.root[:3,:3].T+ob.root[:3,3])[ob.indices])
   if kind in ['cloud','cloudsea']:
    for ob in obs:ob.twosided=True;ob.tint=(1.08,1.04,1.12)
   return obs
  for it in layout['items']:
   if it['kind']=='ground':place(it)
  t=np.asarray(triangles);a=t[:,0];b=t[:,1]-a;c=t[:,2]-a;self.surface=(a,b,c,b[:,0]*c[:,2]-b[:,2]*c[:,0])
  for it in layout['items']:
   if it['kind']!='ground':place(it)
  self.garden_people=[]
  for res,clip,p,yaw in [('garden-hm50','hm05_000',(0,17),180),('garden-hm40','hm95_000',(12,-22),240),('garden-hm06','hm05_000',(-15,26),90)]:
   n=self.actor('Okami/'+res,1.25);self.garden_people.append((n,clip,matrix((p[0],self.garden_height(*p)+.025,p[1]),yaw)))
 def billboard(self,name,p,size,alpha=1,tint=(1,1,1)):
  self.r.sprite(name,p,size,size,self.r.right,self.r.up,tint,alpha)
 def effects(self,t,shot,local):
  r=self.r;H=lambda z:self.h(0,z)
  if shot in ['intro','village','outro']:
   for i in range(16):
    x=(i*3.17)%12-6;z=(i*2.71+t*.4)%24-12;y=1.5+(i*.13+t*.11)%3;self.billboard('Blossom',(x,y,z),.10,.65,(1,.83,.91))
  if shot in ['festival','race']:
   for i in range(4):
    z=(2 if shot=='festival' else 4)+i*3.0
    if shot=='race' and z<local*6.8:continue
    for k in range(5):a=k*1.8+t*3;self.billboard('SpiritGlow',(.16*math.cos(a),H(z)+1.15+.18*math.sin(a),z+.16*math.sin(a)),.24,.8,(1,.8,.35))
   for row in range(6):
    z=-11+row*4.2
    for i in range(5):self.billboard('SpiritGlow',(-2.6+i*1.3,H(z)+4.05,z),.48,.25,(1,.62,.24))
  if shot=='tundra':
   for hit,position in [(.55,(35,self.h(35,2)+1,2)),(1.55,(36.2,self.h(36.2,2.7)+1,2.7)),(2.25,(34,self.h(34,2)+1,2))]:
    age=local-hit
    if 0<=age<.35:
     for k in range(7):a=k*2.399;self.billboard('Spark',(position[0]+math.sin(a)*age*3,position[1]+math.cos(a)*age*2,position[2]),.10*(1-age/.4),.9,(.4,.85,1))
  if shot=='heaven':
   for i in range(40):
    p=[(i*3.13)%48-24,2+math.sin(t*.5+i),(i*7.47)%48-24];self.billboard('SpiritGlow',p,.11,.65,(1,.93,.7))
  if shot=='shiranui':
   p=self.hero_pos;burst=local>1.18
   for k in range(46):
    a=k*2.399+local*2.8;u=(local+k*.031)%1.1/1.1;rad=(1-u)*2.4 if not burst else .45+(local-1.18)*3;self.billboard('SpiritGlow',(p[0]+math.cos(a)*rad,p[1]+.4+u*2.1,p[2]+math.sin(a)*rad),.12+.16*(1-u),.7,(1,.91,.61))
   if 1.18<local<1.55:self.billboard('OriginalWhiteRing',(p[0],p[1]+1,p[2]),2+(local-1.18)*10,.45,(1,.94,.67))
   for k in range(6):a=k*math.pi/3+local;self.billboard('Spirit',(p[0]+math.cos(a)*1.2,p[1]+1.4+.6*math.sin(local*2+k),p[2]+math.sin(a)*1.2),1.1,.5,(1,.87,.52))
  if shot.startswith('boss') or shot=='victory':
   for k in range(15):
    a=k*2.399;u=(t*.8+k*.13)%1.3;rad=2 if shot=='boss-armour' else 4;self.billboard('Flame',(35+math.cos(a)*rad,-109+u*3,4+math.sin(a)*rad),.9+u,.6,(1,.65,.27))
   if shot in ['boss-storm','victory']:
    age=(local-1.4) if shot=='boss-storm' else local
    if 0<=age<.55:
     p=(35,-109,4);r.sprite('OriginalThunderSheet',(35,-104,4),2.1,10,r.right,[0,1,0],(1,.96,.6),1,tile=1)
     for k in range(14):a=k*2.399;self.billboard('OriginalElectricity',(35+math.sin(a)*age*8,-108+math.cos(a)*age*3,4+math.cos(a)*age*8),.5+age,.75,(1,.9,.35))
  if shot=='moon-howl':
   p=self.hero_pos;direction=normalize([-.45,.5,.72]);moon=p+direction*46;r.sprite('OriginalMoon',moon,10,10,r.right,r.up,(.84,.92,1),.98)
   for i in range(12):a=i*2.399+t*.4;self.billboard('SpiritGlow',(p[0]+math.sin(a)*2,p[1]+.5+(i*.31+t*.1)%2,p[2]+math.cos(a)*2),.09,.7,(1,.86,.51))
 def frame(self,t,read=True):
  shot_id=min(len(self.names)-1,np.searchsorted(self.cuts,t,side='right')-1);shot=self.names[shot_id];start=self.cuts[shot_id];local=t-start;length=self.cuts[shot_id+1]-start;u=local/length;r=self.r;night=1 if shot in ['festival','race','moon-howl','outro'] else 0;realm='garden' if shot=='heaven' else 'cave' if shot in ['boss-armour','boss-storm','victory'] else 'village';fov=50
  for n in r.actors:n.visible=False
  for ob in self.lanterns:ob.visible=bool(night)
  for ob in self.stand:ob.visible=shot=='instrument'
  if realm=='village':
   for i,(n,idle,root) in enumerate(self.npcs):n.visible=True;n.update(idle,t+i*.17,root)
  self.hero.visible=shot not in ['heaven','outro'];h=self.hero;clip='pl00_000';ct=local;loop=True;pos=self.pos(0,-5);yaw=0;effect=None
  if shot=='intro':
   eye=np.array([-23+u*4,15-u*2,-27+u*2]);target=[0,1.5,3];pos=self.pos(0,-7);fov=54
  elif shot=='village':
   z=-7+u*6;pos=self.pos(0,z);clip='pl00_011';ct=local;eye=[-5.8,3.0,z-5.8];target=[.2,1,z+1];fov=48
  elif shot=='farm':
   x=42+min(local,1.1)*3;pos=self.pos(x,24);yaw=90;clip='pl00_011' if local<1.1 else 'pl00_092';ct=local if local<1.1 else local-1.1;loop=local<1.1;eye=[x+5,3.6,17.3];target=[x,.9,26];fov=53
  elif shot=='festival':
   z=-10+local*6.8;pos=self.pos(0,z);clip='pl00_012';eye=[5,3,z-6];target=[0,1.3,z+3];fov=56
  elif shot=='race':
   z=local*6.8;pos=self.pos(0,z);clip='pl00_012';eye=[-5.2,2.7,z-5];target=[.1,1.3,z+2];fov=54
  elif shot=='tundra':
   pos=self.pos(35,0);yaw=0;phase=min(2,int(local/.94));ct=local-phase*.94;clip=['pl00_544','pl00_545','pl00_54b'][phase];loop=False;eye=[42.3,3.4,-5.9];target=[35,.95,2.1];fov=47
   for i,n in enumerate(self.imps):
    death=local-(1.5 if i==0 else 2.35);at=self.pos(35+(-.7 if i==0 else 1.3),2.5+i*.65);n.visible=death<1.2;n.update('em00_040' if death>=0 else 'em00_082',max(0,death) if death>=0 else max(0,local-i*.35),matrix(at,180),False)
   self.beads.visible=True;self.bead_clip=['wp2e_001','wp2e_002','wp2e_008'][phase];self.bead_time=ct
  elif shot=='instrument':
   self.hero.visible=False;eye=[37.5,2.5,-6.3];target=[35,1.6,-3];fov=40;self.sword.visible=True;self.sword.groups={1,4};root=matrix([35,self.h(35,-3)+1.6,-3],-20+u*70);rx=matrix();a=math.radians(-65);rx[:3,:3]=[[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]];root=root@rx;self.sword.update('wp29_001',local,root)
  elif shot=='heaven':
   self.hero.visible=False;eye=[-18+u*5,10+u*2,-25];target=[0,2,11];fov=55
   for n,c,root in self.garden_people:n.visible=True;n.update(c,local,root)
  elif shot=='shiranui':
   pos=self.pos(35,0);yaw=155;clip='pl00_04e';loop=False;angle=math.radians(-70+u*75);eye=[35+math.sin(angle)*6.7,2.5,-math.cos(angle)*6.7];target=[35,1,0];fov=45
   if local>=1.18:self.hero.visible=False;self.spirit.visible=True
  elif shot=='boss-armour':
   pos=[35-(min(1,max(0,(local-.45)/.65)))*1.8,-109.92,-1.8];yaw=0;clip='pl00_011' if local<.45 else 'pl00_019' if local<1.1 else 'pl00_520';ct=local if local<.45 else local-.45 if local<1.1 else local-1.1;loop=False;eye=[42,-106.4,-7];target=[35,-108,1];fov=50;self.hero.visible=False;self.spirit.visible=True;self.sword.visible=True;self.sword.groups={1,4};self.boss.visible=self.armour.visible=True;self.boss.groups={0,2};bp=self.boss.update('em65_022',local,matrix([35,-109.92,2.5],180),False);ap=self.armour.pose('wp19_000',local);ap[:33]=bp[:33];self.armour.update('wp19_000',local,matrix([35,-109.92,2.5],180),pose=ap)
  elif shot=='boss-storm':
   pos=[35,-109.92,-3];yaw=0;clip='pl00_523' if local<1.4 else 'pl00_524';ct=2*(.05+.21*(1-math.cos(local*math.pi/2))*.5) if local<1.4 else min(local-1.4,.667);loop=False;eye=[48,-102.5,-10];target=[35,-105.5,2];fov=55;self.hero.visible=False;self.spirit.visible=True;self.boss.visible=True;self.boss.groups={0,2,3} if local<.45 else {1};self.boss.scale=.2114521888*2.75*(2+2*min(1,max(0,(local-.45)/.65)));self.boss.update('em65_024' if local>1.4 else 'em65_032',min(local-1.4,.36) if local>1.4 else local,matrix([35,-109.92,5],180),False);self.sword.visible=True;self.sword.groups={1,3 if local<1.4 else 4}
  elif shot=='victory':
   pos=[35,-109.92,-3];clip='pl00_000';yaw=160;eye=[47,-102.5,-10];target=[35,-106,2];fov=50;self.hero.visible=False;self.spirit.visible=True;self.boss.visible=local<1.4;self.boss.groups={1};self.boss.scale=.2114521888*2.75*4;self.boss.update('em65_030',local,matrix([35,-109.92,5],180),False)
  elif shot=='moon-howl':
   pos=self.pos(35,0);yaw=-32;clip='pl00_04e';ct=min(local,1.92);loop=False;eye=[pos[0]+5.5-u*1.2,pos[1]+1.7,pos[2]-6];target=[pos[0]-.5,pos[1]+2.5,pos[2]+1];fov=51;self.hero.visible=False;self.spirit.visible=True
  else:
   self.hero.visible=False;eye=[-21+u*2,17,-27];target=[0,2,7];fov=54
  root=matrix(pos,yaw);self.hero_pos=pos;pose=h.pose(clip,ct,loop)
  if shot=='boss-storm' and local>1.4:
   amount=np.clip(((local-1.4)/.667-.78)/.22,0,1);rest=h.pose('pl00_000',0);q=rest[:,3:7].copy();q[np.sum(pose[:,3:7]*q,axis=1)<0]*=-1;pose=pose*(1-amount)+rest*amount;pose[:,3:7]=pose[:,3:7]*(1-amount)+q*amount;pose[:,3:7]/=np.maximum(np.linalg.norm(pose[:,3:7],axis=1,keepdims=True),1e-9)
  h.update(clip,ct,root,loop,pose=pose)
  if self.spirit.visible:
   # PL0D shares the original PL00 rig, so use the current original wolf pose.
   self.spirit.update('pl00_000',ct,root,pose=pose)
  if shot=='tundra':self.beads.update(self.bead_clip,self.bead_time,h.dorsal(),False)
  if shot in ['boss-storm','boss-armour']:
   socket=h.anatomical_dorsal() if shot=='boss-storm' and local<1.4 else h.dorsal()
   if shot=='boss-storm' and local<1.4:socket[:3,3]+=np.array([0,.45,-.5])
   self.sword.update('wp29_001',local,socket)
  r.begin(np.asarray(eye),target,t,night,realm,fov);r.geometry(night)
  if self.hero.visible or self.spirit.visible:
   # Reuse the original soft core sprite as the same painted contact shadow.
   r.sprite('SpiritGlow',np.asarray(pos)+[0,.028,0],1.6,.65,np.array([1,0,0]),np.array([0,0,1]),(0,0,0),.23)
  self.effects(t,shot,local);return (r.end() if read else None),shot

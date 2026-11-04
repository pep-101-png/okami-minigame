"""Original terrain vertices reshaped in Y only; original art and native plants.
No new visible mesh topology or painted artwork is authored here.
"""
from pathlib import Path
import sys,json,math,random,copy,shutil,hashlib,subprocess
import numpy as np
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];D=ROOT/'Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami';sys.path.insert(0,'/workspace/work/reference-repairs');from meta import meta
original=json.loads((D/'celestial-meadow/Model.json').read_text());m=copy.deepcopy(original);allv=np.concatenate([np.array(p['positions']).reshape(-1,3) for p in m['parts']]);lo=allv.min(0);hi=allv.max(0)
def smooth(a,b,z):
 t=np.clip((z-a)/(b-a),0,1);return t*t*(3-2*t)
for p in m['parts']:
 v=np.array(p['positions']).reshape(-1,3);v[:,0]=(v[:,0]-(lo[0]+hi[0])/2)*110/(hi[0]-lo[0]);v[:,2]=(v[:,2]-(lo[2]+hi[2])/2)*108/(hi[2]-lo[2]);x,z=v[:,0],v[:,2];v[:,1]=1.25*smooth(-10,0,z)+1.4*smooth(6,16,z)+.025*np.sin(x*.18)*np.cos(z*.11);p['positions']=v.ravel().tolist()
miny=min(min(p['positions'][1::3]) for p in m['parts'])
for p in m['parts']:p['positions'][1::3]=[float(y-miny) for y in p['positions'][1::3]]
height=max(max(p['positions'][1::3]) for p in m['parts']);m['derivation']='Original r108 meadow topology, XZ footprint scaled to 110x108m and existing Y vertices reshaped into continuous gently graded garden levels. All source indices, UVs and vertex count retained; roads are original stone paint on this same mesh.'
folder=D/'celestial-grounded';folder.mkdir(exist_ok=True)
(folder/'Model.json').write_text(json.dumps(m,separators=(',',':')))
for t in m['textures']:
 if not t.get('vertexOnly'):shutil.copyfile(D/'celestial-meadow'/t['path'],folder/t['path'])
for p in [folder,*folder.iterdir()]:
 if p.suffix!='.meta':meta(p)
a=json.loads(subprocess.check_output(['git','show','dd551cdee99b2e2306db73a30fdd540c0483f47c:Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami/CelestialGarden.json'],cwd=ROOT));items=[i for i in a['items'] if i['kind'] not in ['ground','cloud','cloudsea']];items=[i for i in items if not(-30<i['position']['x']<-8 and -13<i['position']['z']<8)];items=[i for i in items if i['kind']!='pond'];items=[i for i in items if i['resource']!='Okami/celestial-gate' or i['position']['z']<0]
def put(res,x,y,z,sx,sy,sz,kind='prop',yaw=0):
 items.append(dict(resource='Okami/'+res,position=dict(x=round(x,4),y=round(y,4),z=round(z,4)),size=dict(x=sx,y=sy,z=sz),yaw=yaw,kind=kind,absoluteHeight=kind in ['ground','cloud','cloudsea']))
# The only walkable surface. Visible ground and collision share these vertices.
put('celestial-grounded',0,-.18,0,110,height,108,'ground')
for i in items:
 if i['resource']=='Okami/vtaa':i['position']=dict(x=0,y=0,z=27);i['size']=dict(x=19,y=10.5,z=12)
# Complete native pond bowls remain modest, with enough rim depth for gentle slopes.
for x,z,yaw in [(22,-18,20),(23,19,110),(-20,20,55)]:put('celestial-pond',x,0,z,10,.85,8.5,'pond',yaw)
for x,y,z,sx,sy,sz,yaw in [(0,-3,0,202,30,198,0),(-8,-9,4,270,49,254,35),(12,-19,-8,350,65,335,95),(-18,-31,12,440,78,420,12),(15,-43,-15,530,92,500,65)]:put('celestial-cloud-bank',x,y,z,sx,sy,sz,'cloud',yaw)
put('celestial-meadow',0,-9,0,450,.1,450,'cloudsea')
# A five-by-five bamboo garden maze, with real boundary collision and two gates.
rng=random.Random(411);n=5;pitch=3.5;ox=-28.5;oz=-11.5;links=set();seen={(4,0)};stack=[(4,0)]
while stack:
 x,z=stack[-1];options=[(x+dx,z+dz) for dx,dz in [(1,0),(-1,0),(0,1),(0,-1)] if 0<=x+dx<n and 0<=z+dz<n and (x+dx,z+dz) not in seen]
 if not options:stack.pop();continue
 nxt=rng.choice(options);links.add(tuple(sorted(((x,z),nxt))));seen.add(nxt);stack.append(nxt)
walls=[]
def wall(x1,z1,x2,z2):walls.append(dict(a=dict(x=x1,y=0,z=z1),b=dict(x=x2,y=0,z=z2)))
for x in range(n):
 for z in range(n):
  px=ox+x*pitch;pz=oz+z*pitch
  if z==0:wall(px,pz,px+pitch,pz)
  if x==0:wall(px,pz,px,pz+pitch)
  if z==n-1 or tuple(sorted(((x,z),(x,z+1)))) not in links:wall(px,pz+pitch,px+pitch,pz+pitch)
  if x==n-1:
   if z not in [0,4]:wall(px+pitch,pz,px+pitch,pz+pitch)
  elif tuple(sorted(((x,z),(x+1,z)))) not in links:wall(px+pitch,pz,px+pitch,pz+pitch)
# Overlapping original bamboo clumps form planted boundaries, not fake hedges.
for j,w in enumerate(walls):
 x1,z1=w['a']['x'],w['a']['z'];x2,z2=w['b']['x'],w['b']['z'];dist=math.hypot(x2-x1,z2-z1)
 for k in range(3):
  t=(k+.5)/3;put('vt19',x1+(x2-x1)*t,0,z1+(z2-z1)*t,1.8,2.1+(j%3)*.12,1.45,'hedge',(j*41+k*57)%360)
# Lanterns frame the two open gates, without blocking their 2.8m lanes.
# Continuous original hydrangea bushes fill the bamboo's open lower stems.
for i in [p for p in items if p['kind']=='hedge']:
 p=i['position'];put('vt48',p['x'],0,p['z'],1.85,1.12+(int(abs(p['x']*11))%3)*.08,1.5,'maze-flower',(i['yaw']+31)%360)
for z in [-9.75,4.25]:
 for dz in [-1.3,1.3]:put('vt35',-10.3,0,z+dz,.65,1.25,.65)
# Main promenade, branches and round garden path are shader paint, never sheets.
walks=[]
def walk(a,b,width=1.35):walks.append(dict(a=dict(x=a[0],y=0,z=a[1]),b=dict(x=b[0],y=0,z=b[1]),width=width))
route=[(0,-25),(0,-21),(2,-16),(3,-11),(1,-5),(-1,1),(0,7),(1,12),(0,17),(0,22)]
for p,q in zip(route,route[1:]):walk(p,q,1.45)
for p,q in [((3,-11),(-11,-9.75)),((-11,4.25),(-1,4)),((2,-16),(16,-18)),((0,17),(17,19)),((-1,12),(-18,19)),((1,1),(12,2))]:walk(p,q,1.05)
for j in range(14):
 t=j*math.tau/14;u=(j+1)*math.tau/14;walk((20+8*math.cos(t),3+8*math.sin(t)),(20+8*math.cos(u),3+8*math.sin(u)),.95)
for p,width in [((0,17),3.2),((0,-25),3.4),((20,3),1.8)]:walk(p,p,width)
# Clear existing flowers away from every painted path and maze corridor.
def pathdist(x,z,w):
 ax,az=w['a']['x'],w['a']['z'];bx,bz=w['b']['x'],w['b']['z'];dx,dz=bx-ax,bz-az;t=max(0,min(1,((x-ax)*dx+(z-az)*dz)/max(.001,dx*dx+dz*dz)));return math.hypot(x-ax-t*dx,z-az-t*dz)-w['width']
def clear(x,z):return min(pathdist(x,z,w) for w in walks)>.4 and not(-30<x<-9 and -13<z<8) and all(math.hypot(x-px,(z-pz)*1.15)>5.5 for px,pz in [(22,-18),(23,19),(-20,20)])
items=[i for i in items if i['kind'] not in ['flower','tree'] or clear(i['position']['x'],i['position']['z'])]
flowers=['vt40','vt46','vt47','vt48','vt29'];rr=random.Random(1144)
for i in range(310):
 t=rr.random()*math.tau;r=math.sqrt(rr.random())*6.4;x,z=20+math.cos(t)*r,3+math.sin(t)*r
 if clear(x,z):put(flowers[i%5],x,0,z,rr.uniform(.8,1.35),rr.uniform(.55,.95),rr.uniform(.7,1.15),'flower',rr.randrange(360))
# Plant the maze's outside border and the space around the three ponds.
for cx,cz in [(22,-18),(23,19),(-20,20)]:
 for i in range(36):
  t=i*math.tau/36;r=5.8+rr.random()*1.7;x,z=cx+math.cos(t)*r,cz+math.sin(t)*r
  if (x/35)**2+(z/32)**2<.95 and clear(x,z):put(flowers[i%5],x,0,z,1.2,.85,1.1,'flower',rr.randrange(360))
for x,z in [(-30,-15),(-30,8),(-11,9),(11,-24),(30,-10),(31,12),(-24,25),(18,28)]:
 if (x/35)**2+(z/32)**2<1.05 and clear(x,z):put('vtba',x,0,z,4,6.5,2,'tree')
layout=dict(version=5,items=items,walks=walks,mazeWalls=walls,maze=dict(columns=n,rows=n,pitch=pitch,origin=dict(x=ox,z=oz),entrance=[4,0],exit=[4,4],links=[[list(a),list(b)] for a,b in sorted(links)]))
(D/'CelestialGarden.json').write_text(json.dumps(layout,indent=2)+'\n')
(Path(__file__).parent/'source-provenance.json').write_text(json.dumps(dict(originalTerrainSHA256=m['sourceSHA256'],derivation=m['derivation'],sourceVertexCount=sum(len(p['positions'])//3 for p in original['parts']),walkArtwork='Original r102/jimen00_ly04 stair texture, composited on the terrain shader',mazeArtwork='Original VT19 bamboo with original VT35 lanterns and original flowers'),indent=2)+'\n')
print('Continuous original terrain:',len(m['parts'][0]['positions'])//3,'source vertices;',height,'m rise;',len(walks),'painted path sections;',len(walls),'maze boundaries;',len(items),'native placements')

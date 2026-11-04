"""Native topology, continuous ground and actual maze boundary checks. Not Unity."""
from pathlib import Path
import sys,json,math,hashlib,re,subprocess,collections
import numpy as np
sys.dont_write_bytecode=True
import geometry as g
R=g.ROOT;D=g.D;raw=json.loads((D/'CelestialGarden.json').read_text());checks=0
def check(ok,msg):
 global checks;checks+=1;assert ok,msg
check(sum(i['kind']=='ground' for i in g.layout)==1,'Separate tier/path meshes remain')
check(not any(i['kind']=='ground' and i['resource'] in ['Okami/celestial-stair','Okami/vt0a'] for i in g.layout),'Unsupported stone sheets/giant blocks remain')
a=json.loads((D/'celestial-meadow/Model.json').read_text());b=json.loads((D/'celestial-grounded/Model.json').read_text());check(a['sourceSHA256']==b['sourceSHA256'],'Lost source identity')
for p,q in zip(a['parts'],b['parts']):
 check(p['indices']==q['indices'] and p['uv']==q['uv'] and len(p['positions'])==len(q['positions']),'Changed original terrain topology/UVs')
check(len(g.surfaces)==1,'Ground collision overlaps several tier surfaces')
tri=g.surfaces[0];norm=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);valid=abs(norm[:,1])>1e-8;slopes=np.linalg.norm(norm[valid][:,[0,2]],axis=1)/abs(norm[valid][:,1]);check(slopes.max()<math.tan(math.radians(45 if raw.get("version",0)>=6 else 25)),'Terrain exceeds a safe walking slope')
for x in np.linspace(-35,35,49):
 for z in np.linspace(-32,32,45):
  if (x/35)**2+(z/32)**2<=1:check(g.height(x,z) is not None,'Hole inside guarded realm')
for w in raw['walks']:
 a=np.array([w['a']['x'],w['a']['z']]);b=np.array([w['b']['x'],w['b']['z']])
 for t in np.linspace(0,1,17):
  x,z=a+(b-a)*t;check(g.height(x,z) is not None,'Path has no supporting native terrain')
  check(((x/35)**2+(z/32)**2)<.96,'Path leads into world guard')
check(len(raw['walks'])<=(96 if raw.get('version',0)>=6 else 48),'Shader path data truncates')
# Solve both the logical maze and the actual collider layout using the wolf's radius.
m=raw['maze'];n=m['columns'];pitch=m['pitch'];ox=m['origin']['x'];oz=m['origin']['z'];links={tuple(sorted((tuple(a),tuple(b)))) for a,b in m['links']}
def world(c):return np.array([ox+(c[0]+.5)*pitch,oz+(c[1]+.5)*pitch])
def wall_distance(p,w):
 a=np.array([w['a']['x'],w['a']['z']]);b=np.array([w['b']['x'],w['b']['z']]);low=np.minimum(a,b)-.325;high=np.maximum(a,b)+.325;return float(np.linalg.norm(np.maximum(np.maximum(low-p,p-high),0)))
start=tuple(m['entrance']);finish=tuple(m['exit']);seen={start};todo=[start]
while todo:
 c=todo.pop()
 for d in [(1,0),(-1,0),(0,1),(0,-1)]:
  q=(c[0]+d[0],c[1]+d[1])
  if not(0<=q[0]<n and 0<=q[1]<n) or tuple(sorted((c,q))) not in links:continue
  for t in np.linspace(0,1,11):
   p=world(c)+(world(q)-world(c))*t;check(min(wall_distance(p,w) for w in raw['mazeWalls'])>.35,'Logical passage blocked by actual hedge collision')
  if q not in seen:seen.add(q);todo.append(q)
check(finish in seen and len(seen)==n*n,'Maze lacks a route/all cells reachable')
for c in [start,finish]:
 p=world(c)
 for x in np.linspace(p[0],ox+n*pitch+1,12):check(min(wall_distance([x,p[1]],w) for w in raw['mazeWalls'])>.35,'Maze gate is blocked')
# Everything is traceable original geometry/art. Protect approved bark/shop work.
for item in g.layout:
 model=json.loads((D/item['resource'].split('/')[-1]/'Model.json').read_text());check(bool(model.get('sourceSHA256')),'Untraceable model')
check(sum(i['kind']=='flower' for i in g.layout)>500,'Flower garden missing');check(sum(i['kind']=='cloud' for i in g.layout)==5,'Layered clouds missing');check(sum(i['kind']=='hedge' for i in g.layout)==len(raw['mazeWalls'])*3,'Maze vegetation gaps')
for subtree in ['Original/Resources/Okami/WeaponPortraits','Original/Resources/Okami/NativeAudio']:
 diff=subprocess.check_output(['git','diff','dd551cd','--name-only','--diff-filter=M','--','Sunward-Unity/Assets/OkamiRemaster/'+subtree],cwd=R);check(not diff.strip(),'Approved shop/bark changed')
script=(R/'Sunward-Unity/Assets/OkamiRemaster/Original/Scripts/HeavenlyGarden.cs').read_text();shader=(R/'Sunward-Unity/Assets/OkamiRemaster/Original/Shaders/OriginalCelestialGround.shader').read_text()
check('Shader.SetGlobalVectorArray("_SunwardHeavenWalks",walks)' in script and 'Shader.SetGlobalVectorArray("_SunwardHeavenWalkStyle",styles)' in script,'Runtime does not upload painted path data')
check('sampler_WalkPaint,p*float2(.18,.42)' in shader and 'return half4(c,1)' in shader,'Path is not opaque original paint on the floor')
check(sum(i['kind']=='maze-flower' for i in g.layout)==len(raw['mazeWalls'])*3,'Open bamboo stalks leave visually empty solid walls')
# Wide pond bases use the lowest supporting corner, without unsupported downhill rims.
for item in [i for i in g.layout if i['kind']=='pond']:
 x,z=item['position']['x'],item['position']['z'];sx,sz=item['size']['x'],item['size']['z'];sample=[g.height(x,z)]+[g.height(x+dx,z+dz) for dx,dz in [(-.4*sx,-.4*sz),(.4*sx,-.4*sz),(-.4*sx,.4*sz),(.4*sx,.4*sz)]];base=min(sample)+.005
 check(all(base<=h+.006 for h in sample),'Pond floats above its supporting corner')
check('PondMaterial(prop,item)' in script if raw.get('version',0)>=6 else 'rimFloor-Centre.y+.005f' in script,'Runtime lost the pond adapter')
print('PASS',checks,'native topology, continuous floor, slope, painted route support, actual maze clearances/solvability and protected art/audio checks; NOT Unity gameplay')

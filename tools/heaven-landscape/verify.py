"""Actual mesh support, stair continuity and cloud clearance. Does not run Unity."""
import sys,json,math,numpy as np,hashlib,subprocess,re
from pathlib import Path
sys.dont_write_bytecode=True
import geometry as g
R=g.ROOT;D=g.D;checks=0
def check(ok,why):
 global checks;checks+=1;assert ok,why
for j in range(192):
 a=j*math.tau/192;check(g.height(35*math.cos(a),32*math.sin(a)) is not None,'Missing walkable perimeter floor')
check(-.5<g.height(0,-25)<.4,'Arrival/return not on the lower garden')
check(2.8<g.height(0,3)<3.2,'Middle landing has no supporting terrace')
check(5.8<g.height(0,17)<6.3 and 5.8<g.height(0,22)<6.3,'Keeper or altar not on supported upper sanctuary')
# Trace each actual curved stair through transverse triangle intersections.
for item in [i for i in g.layout if i['resource']=='Okami/celestial-stair']:
 tri=g.triangles(item);last=None
 for z in np.linspace(tri[:,:,2].min()+.2,tri[:,:,2].max()-.2,90):
  points=[]
  for t in tri:
   for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:
    if (a[2]<=z<=b[2] or b[2]<=z<=a[2]) and abs(a[2]-b[2])>1e-7:points.append(a+(b-a)*(z-a[2])/(b[2]-a[2]))
  check(bool(points),'Gap across actual original stair triangles')
  p=np.array(points);x=(p[:,0].min()+p[:,0].max())*.5;y=g.height(x,z)
  check(y is not None,'Curved ascent lacks real floor')
  # .35m maximum per .15m step catches retaining wall intersections and raised lips.
  if last is not None:check(abs(y-last)<.35,'Ascent intersects a wall or has a discontinuous landing')
  last=y
# Dense cloud banks surround, rather than cover, the guarded walking ellipse.
old=g.surfaces
for item in [i for i in g.layout if i['kind']=='cloud']:
 g.surfaces=[g.triangles(item)]
 for a in np.linspace(0,math.tau,96,endpoint=False):check(g.height(35*math.cos(a),32*math.sin(a)) is None,'Cloud bank crosses the playable boundary')
g.surfaces=old
check(sum(i['kind']=='flower' for i in g.layout)>400,'Planting beds too sparse')
for item in g.layout:
 m=json.loads((D/item['resource'].split('/')[-1]/'Model.json').read_text());check(bool(m.get('sourceSHA256')),'Untraceable original model')
for p in (D/'WeaponPortraits').glob('*.png'):
 raw=subprocess.check_output(['git','show','2a553e9:'+str(p.relative_to(R))],cwd=R)
 expected=re.search(rb'oid sha256:(\w+)',raw)
 check(hashlib.sha256(p.read_bytes()).hexdigest()==expected[1].decode() if expected else p.read_bytes()==raw,'Approved weapon art changed')
check(not subprocess.check_output(['git','diff','2a553e9','--name-only','--','Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami/NativeAudio*'],cwd=R).strip(),'Approved bark/audio changed')
cloud=json.loads((D/'celestial-cloud-bank/Model.json').read_text())['parts'][0];v=np.array(cloud['positions']).reshape(-1,3);alpha=np.array(cloud['colors']).reshape(-1,4)[:,3]
check(np.all(alpha[v[:,1]==v[:,1].min()]==0) and np.all(alpha[v[:,1]==v[:,1].max()]==0),'Original cloud bank rim fade is absent')
shader=(R/'Sunward-Unity/Assets/OkamiRemaster/Original/Shaders/OriginalHeavenCloud.shader').read_text();check('saturate(i.color.a*4)' in shader and 'ZWrite Off Blend SrcAlpha OneMinusSrcAlpha' in shader,'Cloud rim becomes an opaque wall')
print('PASS',checks,'original-mesh floor, two curved ascents, landings, cloud clearance, planting and protected art/audio checks; not Unity playback')

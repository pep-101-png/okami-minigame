"""Native model/layout audits. These do not replace Unity physics or screenshots."""
from pathlib import Path
import sys,json,subprocess,hashlib,re,math
import numpy as np
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools/heaven-qol'));import geometry as g
D=g.D;A=ROOT/'Sunward-Unity/Assets';l=json.loads((D/'CelestialGarden.json').read_text());checks=0;results={}
def check(v,why):
 global checks
 checks+=1
 assert v,why
def height_at(tri,x,z):
 a=tri[:,0];b=tri[:,1]-a;c=tri[:,2]-a;det=b[:,0]*c[:,2]-b[:,2]*c[:,0];ok=abs(det)>1e-8;u=np.divide((x-a[:,0])*c[:,2]-(z-a[:,2])*c[:,0],det,out=np.full(len(a),-1.),where=ok);v=np.divide(b[:,0]*(z-a[:,2])-b[:,2]*(x-a[:,0]),det,out=np.full(len(a),-1.),where=ok);hit=ok&(u>=-1e-6)&(v>=-1e-6)&(u+v<=1.000001);return (a[:,1]+u*b[:,1]+v*c[:,1])[hit]
tri=np.concatenate(g.surfaces);normal=np.cross(tri[:,1]-tri[:,0],tri[:,2]-tri[:,0]);check(np.all(normal[:,1]>0),'Terrain raycast faces point down');check(np.isfinite(tri).all(),'Invalid terrain coordinates');results['terrainTriangles']=len(tri);slope=np.linalg.norm(normal[:,[0,2]],axis=1)/normal[:,1];check(slope.max()<1,'Native terrain exceeds 45 degree walking slope');results['maximumSlopeDegrees']=float(np.degrees(np.arctan(slope.max())))
for p in l['ponds']:
 x,z=p['position']['x'],p['position']['z'];level=p['position']['y'];floor=g.height(x,z);check(abs(level-floor-.18)<1e-5,'Pond has no actual basin');item=next(i for i in l['items'] if i['kind']=='pond' and i['position']['x']==x and i['position']['z']==z);t=g.triangles(item)[2:];check(len(height_at(t,x,z))==0,'Rock model has solid center over basin');check(item['absoluteHeight'],'Basin rim snapped to depression');
 # Entry slopes should be walkable, not a vertical invisible lip.
 for ang in np.linspace(0,math.pi*2,12,endpoint=False):
  r=np.linspace(.7,1.8,45);xx=x+np.cos(ang)*r*p['radius']['x'];zz=z+np.sin(ang)*r*p['radius']['y'];ys=np.array([g.height(a,b) for a,b in zip(xx,zz)]);slope=abs(np.diff(ys))/np.sqrt(np.diff(xx)**2+np.diff(zz)**2);check(slope.max()<1.35,'Unwalkable basin edge')
results['pondDepthMetres']=.18
shrine=next(i for i in l['items'] if i['resource']=='Okami/vtaa');q=json.loads(json.dumps(shrine));q['kind']='prop';q['position']['y']+=g.height(q['position']['x'],q['position']['z'])+.005;t=g.triangles(q);n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);walk=(n[:,1]/np.maximum(.00001,np.linalg.norm(n,axis=1))>.55)&(t[:,:,1].max(1)<=q['position']['y']+3.1);t=t[walk];check(len(t)>100,'Shrine stairs/landing omitted from collision');ys=[]
for z in np.linspace(21.05,25.4,35):
 hit=height_at(t,0,z);check(len(hit)>0,'Hole through shrine staircase');ys.append(max(hit))
check(np.diff(ys).min()>-.1 and max(np.diff(ys))<.36,'Stairs have a gap or unwalkable riser');results['nativeShrineWalkFaces']=len(t)
check(len(l['walks'])<=96,'Path shader silently truncates routes');check(len(l['mazeWalls'])>30,'Maze boundary missing');check('Centre.y+7f' in (A/'OkamiRemaster/Original/Scripts/HeavenlyGarden.cs').read_text(),'Maze jump barrier too low')
bar=(D/'Effects/HeavenBarrier.mat').read_text();check('a3c019b9b65642148b202ae78df8d741' in bar,'Maze veil uses leaves instead of spirit glow');check('velocityOverLifetime' in (A/'OkamiRemaster/Original/Scripts/HeavenlyGarden.Features.cs').read_text(),'Maze upward motion missing')
base=json.loads(subprocess.check_output(['git','show','4a462f1:Sunward-Unity/Assets/OkamiRemaster/Original/Resources/Okami/NativeAudio.json'],cwd=ROOT));now=json.loads((D/'NativeAudio.json').read_text());check(now['cues'][:len(base['cues'])]==base['cues'],'Existing sound changed unintentionally');check(sum(c['cue']=='heaven-gong' for c in now['cues'])==1,'Duplicate gong cue')
# Every newly introduced project file must have a valid unique Unity metadata GUID.
paths=set(subprocess.check_output(['git','ls-files','--others','--exclude-standard','-z','Sunward-Unity/Assets'],cwd=ROOT).decode().split('\0'))|set(subprocess.check_output(['git','diff','4a462f1','--name-only','-z','--','Sunward-Unity/Assets'],cwd=ROOT).decode().split('\0'));guids={}
for p in A.rglob('*.meta'):
 m=re.search(r'^guid: ([0-9a-f]{32})$',p.read_text(),re.M)
 if m:guids.setdefault(m[1],[]).append(p)
for path in filter(None,paths):
 p=ROOT/path
 if p.suffix=='.meta':
  m=re.search(r'^guid: ([0-9a-f]{32})$',p.read_text(),re.M);check(m is not None and len(guids[m[1]])==1,'New meta has duplicate/invalid GUID: '+path)
 else:check(Path(str(p)+'.meta').exists(),'Missing Unity meta: '+path)
for res in ['heaven-basin-terrain','heaven-gate','heaven-pond-basin','heaven-tea-cup','heaven-tea-tray','heaven-lookout-roof']:
 m=json.loads((D/res/'Model.json').read_text());check(bool(m.get('derivation')),'Missing original source derivation');check(bool(m.get('sourceSHA256')),'Missing original source identity')
results.update(checks=checks,scope='Native geometry, metadata and source contracts; not Unity runtime');(Path('/workspace/work/heaven-complete')/'geometry-audit.json').write_text(json.dumps(results,indent=2));print('PASS',checks,'native terrain/basin/stair/maze/resource contracts',results)

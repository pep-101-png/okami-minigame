"""Geometry and targeted scene regression checks; does not claim Unity rendering."""
from pathlib import Path
import importlib.util,re,json,hashlib,struct,subprocess
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('sunward_environment_details',Path(__file__).with_name('environment.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
base=subprocess.check_output(['git','show','7046ef0:Sunward-Unity/Assets/Sunward/Scenes/Windflower.unity'],cwd=ROOT,text=True)
scene=m.Scene(m.ASSETS/'Scenes/Windflower.unity',text=base)
red={i:b for i,b in scene.blocks.items() if scene.kind(i)==1 and scene.name(i).startswith('Ink world · vermilion bridge')}
original_colliders={i:b for i,b in scene.blocks.items() if scene.kind(i) in [64,65,136,154]}
report=m.apply(scene)
for i,b in red.items():assert scene.blocks[i]==b,'Praised bridge rail object changed'
# No collider geometry can change. The lone targeted mill-rock proxy may be disabled.
for i,b in original_colliders.items():
 assert re.sub(r'm_Enabled: [01]','m_Enabled: X',scene.blocks[i])==re.sub(r'm_Enabled: [01]','m_Enabled: X',b),'Collider geometry changed'
assert report.get('alreadyApplied') or (report['bridgeDecks']==2 and report['bambooClumps']==7 and report['arenaLogs']==28 and report['homeOutlines']==2)
old=dict(scene.blocks);assert m.apply(scene)=={'alreadyApplied':True};assert old==scene.blocks
hashes=set();vertices=triangles=0
for path in m.OUT.glob('*.asset'):
 raw=path.read_text();n=int(re.search(r'm_VertexCount: (\d+)',raw)[1]);data=bytes.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)',raw)[1]);assert len(data)%n==0
 stride=len(data)//n;assert stride in [24,48]
 v=np.array([struct.unpack_from('<3f',data,i*stride) for i in range(n)])
 nn=np.array([struct.unpack_from('<3f',data,i*stride+12) for i in range(n)])
 ix=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-fA-F]+)',raw)[1]),dtype='<u4')
 assert np.isfinite(v).all() and np.isfinite(nn).all(),path
 assert np.allclose(np.linalg.norm(nn,axis=1),1,atol=1e-4),path
 assert ix.min()>=0 and ix.max()<n and len(ix)%3==0,path
 if re.fullmatch('Bamboo-[0-6]-culms',path.stem):hashes.add(hashlib.sha256(data).hexdigest())
 vertices+=n;triangles+=len(ix)//3
assert len(hashes)==7,'Bamboo clumps must not repeat geometry'
assert abs(m.river_x(43.4)+22.691049535874367)<1e-6
shader=(m.ASSETS/'Shaders/LivingCascade.shader').read_text();assert '_Time.y*_FlowSpeed' in shader
result={'result':'passed','checkedAssets':len(list(m.OUT.glob('*.asset'))),'vertices':vertices,'sharedMeshTriangles':triangles,'uniqueBambooClumps':len(hashes),'redBridgeObjectsUntouched':len(red),'unityRendered':False,'sceneSaved':False}
(Path(__file__).parent/'environment-check.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))

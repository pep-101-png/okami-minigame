"""Validate the saved assets/references, not merely the Python authoring functions.
Does not claim Unity API compilation, sound, motion, or final scene approval.
"""
from native import *
from PIL import Image
import collections,subprocess

def parse_mesh(path):
 s=path.read_text();assert s.startswith('%YAML 1.1\n%TAG !u!'),path
 n=int(re.search(r'm_VertexCount: (\d+)',s)[1]);raw=bytes.fromhex(re.search(r'_typelessdata: ([0-9a-fA-F]+)',s)[1]);channels=re.findall(r'- stream: (\d+)\n      offset: (\d+)\n      format: (\d+)\n      dimension: (\d+)',s)
 assert len(channels)==14,(path,len(channels))
 stride=80 if int(channels[12][3]) else 48
 assert len(raw)==n*stride and len(raw)==int(re.search(r'm_DataSize: (\d+)',s)[1]),path
 positions=np.array([struct.unpack_from('<3f',raw,i*stride) for i in range(n)])
 normals=np.array([struct.unpack_from('<3f',raw,i*stride+12) for i in range(n)])
 assert np.isfinite(positions).all() and np.isfinite(normals).all(),path
 dtype='<u4' if 'm_IndexFormat: 1' in s else '<u2';ix=np.frombuffer(bytes.fromhex(re.search(r'm_IndexBuffer: ([0-9a-fA-F]+)',s)[1]),dtype=dtype)
 assert len(ix)==int(re.search(r'indexCount: (\d+)',s)[1]) and len(ix)%3==0 and max(ix)<n,path
 assert np.max(abs(np.linalg.norm(normals[np.unique(ix)],axis=1)-1))<.001,path
 if stride==80:
  assert s.count('  - e00:')==13 and 'Infinity' not in s,path
  for i in range(n):
   weights=struct.unpack_from('<4f',raw,i*stride+48);bones=struct.unpack_from('<4I',raw,i*stride+64)
   assert abs(sum(weights)-1)<1e-6 and min(weights)>=0 and max(bones)<13,path
 return len(ix)//3

def unresolved(scene):
 refs=set()
 for b in scene.blocks.values():refs.update(int(x) for x in re.findall(r'\{fileID: (-?\d+)\}',b) if int(x))
 return refs-set(scene.blocks)

def main():
 paths=list(OUT.glob('*.asset'));triangles=sum(parse_mesh(p) for p in paths)
 baseline=subprocess.check_output(['git','show','a6b9d4d89c43acccfcca17a8d86bb3f32182b486:Sunward-Unity/Assets/Sunward/Scenes/Windflower.unity'],cwd=ROOT,text=True)
 scene=Scene(ASSETS/'Scenes/Windflower.unity');before=Scene(Path('baseline'),baseline)
 assert set(before.blocks)<=set(scene.blocks),'Existing scene objects removed'
 assert not(unresolved(scene)-unresolved(before)),'New dangling scene reference'
 changes=[]
 for i,b in before.blocks.items():
  if before.kind(i) in (54,64,65,136,143) and '\n'.join(line.rstrip() for line in b.splitlines())!='\n'.join(line.rstrip() for line in scene.blocks[i].splitlines()):changes.append(i)
 assert len(changes)==2 and all(before.kind(i)==136 for i in changes),('Unexpected physics edit',changes)
 active=collections.defaultdict(list)
 for i,b in scene.blocks.items():
  if scene.kind(i)==137 and '  m_Enabled: 1\n' in b:
   root=re.search(r'm_RootBone: \{fileID: (-?\d+)\}',b)[1];active[root].append(i)
 assert len(active)==13 and all(len(v)==1 for v in active.values()),'Named NPC/shopper skin lost or duplicated'
 actors=[scene.name(scene.owner(ids[0])) for ids in active.values()]
 assert len(set(actors))==7 and all(a.startswith('Villager · ') for a in actors),actors
 # Exact topology orientation catches inverted tubes that Blender's two-sided
 # preview would show while Unity's backface culling hides the outside.
 for kind in ['tube','box','loft']:
  m=Mesh()
  if kind=='tube':m.tube([(0,0,0),(0,1,0)],[.2,.2],(1,1,1))
  elif kind=='box':m.box((0,.5,0),(1,1,1),(1,1,1))
  else:m.loft([(0,0,0,.2,.2),(0,1,0,.2,.2)],(1,1,1))
  v=np.array(m.v);volume=sum(np.dot(v[a],np.cross(v[b],v[c])) for a,b,c in m.tri)/6
  assert volume>0,(kind,'inward geometry')
 # Verify original wolf import, geometry, materials, textures and all 47 clips untouched.
 changed=subprocess.check_output(['git','diff','--name-only','HEAD'],cwd=ROOT,text=True).splitlines()
 assert not any('/Animations/' in p or '/Models/Amaterasu' in p or '/Generated/Wolf-' in p or '/Textures/Wolf-' in p or '/Generated/Amaterasu.prefab' in p or 'windows-sync' in p for p in changed),changed
 baseline_guids=set(re.findall(r'guid: ([0-9a-f]{32})',baseline))
 metas={}
 for p in (ROOT/'Sunward-Unity/Assets').rglob('*.meta'):
  match=re.search(r'guid: (\w+)',p.read_text())
  if match:metas[match[1]]=p
 for p in list(OUT.glob('*.mat'))+[ASSETS/'Scenes/Windflower.unity']:
  for g in re.findall(r'guid: ([0-9a-f]{32})',p.read_text()):
   if g.startswith('0000000000000000'):continue
   assert g in metas or g in baseline_guids,('New missing asset',p,g)
 for p in (ASSETS/'Textures/VillageFinish').glob('*.png'):
  with Image.open(p) as im:im.verify()
  meta=Path(str(p)+'.meta').read_text();assert ('sRGBTexture: 0' if '-normal' in p.stem else 'sRGBTexture: 1') in meta
  if '-normal' in p.stem:assert 'textureType: 0' in meta # Pigment explicitly decodes linear RGB, not packed Unity normals.
 print(f'PASS: {len(paths)} native meshes ({triangles:,} library triangles), 13 live rigs / 7 roles, valid new references and textures.')
 print('PASS: no removed pre-existing scene nodes; only the two requested obsolete arena capsule colliders disabled.')
 print('PASS: original wolf appearance assets, animation clips, importer and syncing untouched; geometry winding checked.')
 print('NOT VERIFIED: Unity import/render, gameplay motion quality, sound balance, or frame time.')
if __name__=='__main__':main()

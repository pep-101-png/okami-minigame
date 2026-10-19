"""Portable integrity checks. Does not substitute for Unity import/render/play tests."""
from pathlib import Path
import json,struct,math,hashlib,re
ROOT=Path(__file__).resolve().parents[1]
data=json.loads((ROOT/'Assets/Sunward/Data/Valley.json').read_text());raw=(ROOT/'Assets/Sunward/Data/Valley.bytes').read_bytes();vcount=triangles=meshes=0
for group in data['assets']:
 for mesh in group['meshes']:
  offset=mesh['offset'];nv,ni=struct.unpack_from('<ii',raw,offset);assert(nv,ni)==(mesh['vertices'],mesh['indices']);assert offset+8+48*nv+4*ni<=len(raw);assert ni%3==0
  values=struct.unpack_from('<'+'f'*(nv*12),raw,offset+8);assert all(math.isfinite(x)for x in values)
  ix=struct.unpack_from('<'+'I'*ni,raw,offset+8+48*nv);assert max(ix,default=0)<nv
  vcount+=nv;triangles+=ni//3;meshes+=1
for m in data['materials']:
 if m['texture']>=0:assert(ROOT/'Assets/Sunward/Textures'/('map-'+str(m['texture'])+'.png')).exists()
required={'TownV3','Spear','Sundial'}|{'NPC-'+str(i)for i in range(7)}|{'Enemy-'+k for k in ['wisp','reed','heavy','ranged','elite','boss']};assert required<={a['name']for a in data['assets']}
assert any(m['name']=='HomeRoof'for a in data['assets']for m in a['meshes'])
for id in ['garden','mill','shrine']:assert any(m['name']=='QuestFlower-'+id for a in data['assets']for m in a['meshes'])
assert len(data['world']['terrain']['heights'])==data['world']['terrain']['nx']*data['world']['terrain']['nz']
report=json.loads((ROOT/'Review/wolf-export.json').read_text());assert len(report['clips'])==44
for m in report['materials']:
 for image in m['images']:assert(ROOT/'Assets/Sunward/Textures'/('Wolf-'+image.split('.')[0]+'.png')).exists()
bindings=report['meshMaterials'];assert len(bindings)==11
assert len({b['name']for b in bindings})==len(bindings)
material_names={m['name']for m in report['materials']}
for binding in bindings:assert set(binding['materials'])<=material_names
from PIL import Image
for image in (ROOT/'Assets/Sunward/Textures').glob('*.png'):
 with Image.open(image)as png:png.verify()
# Validate the new, connected artwork rather than only the original map folder.
art=json.loads((ROOT/'Review/windflower-art.json').read_text())
for image in (ROOT/'Assets/Sunward/Textures/Art').glob('*.png'):
 with Image.open(image)as png:
  assert png.size==(1024,1024),('Artwork resolution',image)
  png.verify()
 assert image.with_suffix('.png.meta').exists(),('Missing artwork GUID',image)
assert len(list((ROOT/'Assets/Sunward/Textures/Art').glob('*.png')))==15
for file in (ROOT/'Assets/Sunward/Scripts').glob('*.cs'):
 for name in re.findall(r'class\s+(\w+)\s*:\s*MonoBehaviour',file.read_text()):assert name==file.stem,(name,file)
for file in ROOT.rglob('*'):
 if file.is_file()and'bin'not in file.parts and'obj'not in file.parts:assert file.stat().st_size<100*1024*1024,('GitHub individual-file size limit',file)
result={'converted_meshes':meshes,'vertices':vcount,'triangles':triangles,'materials':len(data['materials']),'map_textures':len(list((ROOT/'Assets/Sunward/Textures').glob('map-*.png'))),'wolf_textures':len(list((ROOT/'Assets/Sunward/Textures').glob('Wolf-*.png'))),'animation_actions':len(report['clips'])+len(report.get('unity_only_actions',[])),'source_actions':44,'sleep_rollback_actions':len(report.get('unity_only_actions',[])),'source_model_sha256':report['source_sha256'],'home_roof_cutaway_meshes':True,'three_collectible_flower_visual_groups':True,'mono_behaviour_filenames_match':True,'new_artwork_maps':15,'new_artwork_resolution':'1024x1024','unity_editor_compilation':'NOT RUN','unity_shader_compilation':'NOT RUN','unity_playmode':'NOT RUN','windows_build':'NOT RUN'}
(ROOT/'Review/asset-validation.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

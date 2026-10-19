"""Read the actual exported FBX back through Blender, including material order."""
from pathlib import Path
import bpy,json,math,hashlib,sys
R=Path(__file__).resolve().parents[1]
manifest=json.loads((R/'Review/remake-library.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(R/'Assets/Sunward/Models/Remake/WindflowerRemake.fbx'))
rows=[]
for part in manifest['assets']:
 mesh=bpy.data.objects.get(part['mesh']);root=bpy.data.objects.get(part['name']);front=bpy.data.objects.get(part['front'])
 assert mesh and root and front,part['name']
 assert mesh.type=='MESH' and len(mesh.data.polygons)>20
 assert not mesh.modifiers and not mesh.animation_data
 assert all(math.isfinite(v)for vertex in mesh.data.vertices for v in vertex.co)
 actual=[m.name for m in mesh.data.materials]
 if '--write-bindings' in sys.argv:
  assert set(actual)==set(part['materials']),(part['name'],actual,part['materials'])
  part.setdefault('source_materials',part['materials']);part['materials']=actual
 assert actual==part['materials'],(part['name'],actual,part['materials'])
 assert mesh.data.uv_layers,part['name']
 used={p.material_index for p in mesh.data.polygons};assert max(used)<len(part['materials'])
 bounds=[min(v.co[i] for v in mesh.data.vertices)for i in range(3)]+[max(v.co[i]for v in mesh.data.vertices)for i in range(3)]
 rows.append({'asset':part['name'],'vertices':len(mesh.data.vertices),'faces':len(mesh.data.polygons),'bounds':bounds,'material_order_matches':True})
if '--write-bindings' in sys.argv:(R/'Review/remake-library.json').write_text(json.dumps(manifest,indent=2))
assert len(rows)==19
assert not bpy.data.armatures and not bpy.data.actions
(R/'Review/remake-fbx-validation.json').write_text(json.dumps({'assets':rows,'sha256':hashlib.sha256((R/'Assets/Sunward/Models/Remake/WindflowerRemake.fbx').read_bytes()).hexdigest(),'check':'Actual static FBX import through Blender; no claim of Unity import, material or shader validation'},indent=2))
print('Verified',len(rows),'static FBX assets, material order, finite geometry, UVs and zero animations/armatures')

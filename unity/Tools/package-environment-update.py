"""Explicit overlay: preserve the existing Unity project, wolf and animations."""
from pathlib import Path
import hashlib,json,zipfile
r=Path(__file__).resolve().parents[1]
new=[
'Assets/Editor/EnvironmentFinishBuilder.cs','Assets/Editor/MarketTreeCleanup.cs','Assets/Sunward/Scripts/MarketTreeRules.cs',
'Assets/Sunward/Scripts/EnvironmentLayout.cs',
'Assets/Sunward/Scripts/EnvironmentReviewState.cs',
'Assets/Sunward/Scripts/MarketWalker.cs',
'Assets/Sunward/Shaders/SurfaceDetail.shader',
]
# Include the narrowly scoped dependency repair for installations missing that overlay.
existing=[
'Assets/Editor/WatersideRepair.cs','Assets/Editor/RockSeating.cs','Assets/Editor/VisualRemakeBuilder.cs',
'Assets/Sunward/Scripts/Valley.cs','Assets/Sunward/Scripts/WorldData.cs',
'Assets/Sunward/Scripts/SeatedStoneGeometry.cs','Assets/Sunward/Scripts/GardenPond.cs',
'Assets/Sunward/Scripts/SurfaceRepairState.cs','Assets/Sunward/Shaders/GardenPond.shader']
assets=new+existing
files=assets+[p+'.meta'for p in assets]+['Assets/Sunward/Textures/SurfaceDetail.meta']
files+=sorted(str(p.relative_to(r))for p in (r/'Assets/Sunward/Textures/SurfaceDetail').iterdir()if p.is_file())
files+=['Review/ENVIRONMENT-REVIEW-2.md','Review/environment-validation.json','Review/environment-assets-validation.json','Review/environment-portable-tests.txt','Review/environment-world-tests.txt','Review/waterside-validation.json','Review/bridge-clearance-geometry-diagnostic.png','Review/surface-material-contact-sheet.jpg']
files=sorted(set(files));out=r/'Releases/Sunward-Unity-Environment-Update.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in files:z.write(r/p,p)
 z.writestr('START-HERE.txt',(r/'Review/ENVIRONMENT-REVIEW-2.md').read_text())
with zipfile.ZipFile(out)as z:
 assert z.testzip()is None
 assert set(z.namelist())==set(files+['START-HERE.txt'])
 for p in files:assert z.read(p)==(r/p).read_bytes()
 assert not any(p.endswith(('.fbx','.anim','.controller','.blend','.unity'))for p in z.namelist())
 assert not any(p.startswith(('Packages/','ProjectSettings/','Library/'))for p in z.namelist())
report={'file':out.name,'requires_existing_visual_remake':'b0a2113 or newer','bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'files':files,'automatic_scene_migration':True,'unity_editor_verified':False,'wolf_animation_assets_included':False}
(r/'Releases/environment-update.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items()if k!='files'},indent=2))

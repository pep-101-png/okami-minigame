"""Focused patch against b0a2113: explicitly listed repair files only."""
from pathlib import Path
import zipfile,json,hashlib
r=Path(__file__).resolve().parents[1]
code=[
 'Assets/Editor/WatersideRepair.cs',
 'Assets/Editor/RockSeating.cs',
 'Assets/Editor/VisualRemakeBuilder.cs',
 'Assets/Sunward/Scripts/Valley.cs',
 'Assets/Sunward/Scripts/WorldData.cs',
 'Assets/Sunward/Scripts/GardenPond.cs',
 'Assets/Sunward/Scripts/SeatedStoneGeometry.cs',
 'Assets/Sunward/Scripts/SurfaceRepairState.cs',
 'Assets/Sunward/Shaders/GardenPond.shader',
]
names=code+[name+'.meta'for name in code]+[
 'README.md','Review/WATERSIDE-REPAIR.md','Review/waterside-validation.json',
 'Review/waterside-portable-tests.txt','Review/waterside-world-tests.txt']
files=[r/name for name in names];out=r/'Releases/Sunward-Unity-Waterside-Fix.zip'
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in files:z.write(p,p.relative_to(r).as_posix())
with zipfile.ZipFile(out)as z:
 assert z.testzip()is None
 assert set(z.namelist())==set(names)
 for p in files:assert z.read(p.relative_to(r).as_posix())==p.read_bytes()
 assert not any(n.endswith(('.fbx','.png','.anim','.controller'))for n in z.namelist())
report={'file':out.name,'base':'b0a2113','bytes':out.stat().st_size,'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'files':names,'applies_automatically_on_Windflower_open':True,'no_model_or_animation_assets':True,'unity_editor_verified':False}
(r/'Releases/waterside-fix.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='files'},indent=2))

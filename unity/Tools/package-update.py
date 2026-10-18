"""Package an integrated overlay, keeping the old import-patch URL compatible."""
from pathlib import Path
import json,hashlib,zipfile,shutil
root=Path(__file__).resolve().parents[1];out=root/'Releases';out.mkdir(exist_ok=True)
files=set()
for directory in ['Assets/Editor','Assets/Sunward/Scripts','Assets/Sunward/Shaders','Review']:
 for p in (root/directory).rglob('*'):
  if p.is_file():files.add(p.relative_to(root).as_posix())
files.update(['Assets/Sunward/Models/Amaterasu.fbx','Assets/Sunward/Models/Amaterasu.fbx.meta','Packages/manifest.json','README.md'])
target=out/'Sunward-Unity-Restoration-Update.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as archive:
 for name in sorted(files):archive.write(root/name,name)
with zipfile.ZipFile(target)as archive:
 assert archive.testzip()is None
 for name in ['Assets/Editor/EnvironmentGrounding.cs','Assets/Sunward/Scripts/VillageResident.cs','Assets/Sunward/Scripts/HomeWeaponRack.cs','Assets/Sunward/Models/Amaterasu.fbx','Review/RESTORATION.md']:assert name in archive.namelist()
shutil.copyfile(target,out/'Sunward-Unity-Import-Repair.zip')
report={'type':'integrated-restoration-overlay','target_editor':'6000.6.6f1','files':sorted(files),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,'unity_editor_verified':False,'note':'Includes corrected sleep FBX and all required scripts/shaders. Copy contents into existing Unity project, then run Sunward > Create or Rebuild V3 Scene.'}
(out/'restoration-update.json').write_text(json.dumps(report,indent=2)+'\n');(out/'import-repair.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='files'},indent=2))

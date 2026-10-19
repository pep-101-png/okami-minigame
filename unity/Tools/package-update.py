"""Package an integrated overlay, keeping the old import-patch URL compatible."""
from pathlib import Path
import json,hashlib,zipfile,shutil
root=Path(__file__).resolve().parents[1];out=root/'Releases';out.mkdir(exist_ok=True)
files=set()
for directory in ['Assets/Editor','Assets/Sunward/Scripts','Assets/Sunward/Shaders','Assets/Sunward/Textures/Art','Assets/Sunward/Textures/Remake','Assets/Sunward/Models/Remake','Assets/Sunward/Audio','Review']:
 for p in (root/directory).rglob('*'):
  if p.is_file():files.add(p.relative_to(root).as_posix())
files.update(['Assets/Sunward/Textures/Remake.meta','Assets/Sunward/Models/Remake.meta','Assets/Sunward/Textures/Art.meta','Packages/manifest.json','README.md'])
target=out/'Sunward-Unity-Restoration-Update.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED,compresslevel=6)as archive:
 for name in sorted(files):archive.write(root/name,name)
with zipfile.ZipFile(target)as archive:
 assert archive.testzip()is None
 for name in ['Assets/Editor/EnvironmentGrounding.cs','Assets/Sunward/Scripts/VillageResident.cs','Assets/Sunward/Scripts/HomeWeaponRack.cs','Assets/Editor/WolfClipProcessor.cs','Review/RESTORATION.md']:assert name in archive.namelist()
shutil.copyfile(target,out/'Sunward-Unity-Import-Repair.zip')
report={'type':'integrated-restoration-overlay','target_editor':'6000.6.6f1','files':sorted(files),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,'unity_editor_verified':False,'note':'Preserves existing FBX and its importer metadata. Includes native-clip repair code and connected Windflower artwork. Open Windflower and run Sunward > Apply Visual Remake to Windflower. This visual-only menu does not reprocess wolf animations.'}
(out/'restoration-update.json').write_text(json.dumps(report,indent=2)+'\n');(out/'import-repair.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items()if k!='files'},indent=2))

# Small repair overlay for users who already applied the full environment update.
hotfix=out/'Sunward-Unity-Scale-Hotfix.zip'
with zipfile.ZipFile(hotfix,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as archive:
 for name in ['Assets/Editor/WolfClipProcessor.cs','Assets/Editor/WolfClipProcessor.cs.meta','Assets/Editor/SleepClipAuthoring.cs','Assets/Editor/SleepClipAuthoring.cs.meta','Assets/Sunward/Scripts/LimbArc.cs','Assets/Sunward/Scripts/LimbArc.cs.meta','Review/SCALE-HOTFIX.md']:
  archive.write(root/name,name)
with zipfile.ZipFile(hotfix) as archive:
 assert archive.testzip() is None
(out/'scale-hotfix.json').write_text(json.dumps({'sha256':hashlib.sha256(hotfix.read_bytes()).hexdigest(),'bytes':hotfix.stat().st_size,'unity_editor_verified':False,'install':'Extract into existing project root, reopen Unity, run Sunward > Repair Amaterasu Animation Scale (not just Validate).'},indent=2)+'\n')
print('Scale hotfix:',hotfix.stat().st_size,'bytes')

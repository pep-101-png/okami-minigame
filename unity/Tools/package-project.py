"""A standalone Unity project ZIP, not a Windows executable or a Unity test result."""
from pathlib import Path
import zipfile,json,hashlib
root=Path(__file__).resolve().parents[1];release=root/'Releases';release.mkdir(exist_ok=True)
files=[]
for p in root.rglob('*'):
 if not p.is_file():continue
 rel=p.relative_to(root)
 if any(part in {'Releases','Library','Temp','Obj','Builds','Logs','UserSettings','bin','obj','__pycache__'}for part in rel.parts):continue
 if p.suffix in {'.csproj.user','.sln','.log'}:continue
 files.append(p)
with zipfile.ZipFile(release/'Sunward-Unity.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for p in sorted(files):z.write(p,'Sunward-Unity/'+p.relative_to(root).as_posix())
with zipfile.ZipFile(release/'Sunward-Unity.zip')as z:
 assert z.testzip()is None
 names=set(z.namelist())
 for f in ['Packages/manifest.json','ProjectSettings/ProjectVersion.txt','Assets/Editor/SunwardProjectBuilder.cs','Assets/Sunward/Models/Amaterasu.fbx','Assets/Sunward/Data/Valley.bytes','README.md']:assert'Sunward-Unity/'+f in names
meta={'project':'Sunward-Unity','target_editor':'6000.6.6f1','source_game_commit':'b55b1bd2283738fcdc2a5cd711d2adb91aba4418','files':len(files),'zip_sha256':hashlib.sha256((release/'Sunward-Unity.zip').read_bytes()).hexdigest(),'bytes':(release/'Sunward-Unity.zip').stat().st_size,'unity_compilation_verified':False,'unity_playmode_verified':False,'windows_executable_included':False}
(release/'manifest.json').write_text(json.dumps(meta,indent=2));print(json.dumps(meta,indent=2))

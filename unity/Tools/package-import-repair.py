"""Create a small overlay patch for existing Unity projects; no model binaries."""
from pathlib import Path
import zipfile, json, hashlib
root=Path(__file__).resolve().parents[1]
files=['Assets/Editor/SunwardProjectBuilder.cs','Assets/Editor/SunwardProjectBuilder.cs.meta','Assets/Editor/SunwardImportPolicy.cs','Assets/Editor/SunwardImportPolicy.cs.meta','Assets/Sunward/Scripts/GameFlow.cs','Assets/Sunward/Scripts/GameFlow.cs.meta','Review/wolf-export.json','Review/IMPORT-REPAIR.md','Packages/manifest.json']
target=root/'Releases/Sunward-Unity-Import-Repair.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED)as archive:
 for name in files:archive.write(root/name,name)
with zipfile.ZipFile(target)as archive:assert archive.testzip()is None
report={'files':files,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,'unity_editor_verified':False}
(root/'Releases/import-repair.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))

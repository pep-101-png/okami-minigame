"""Package only changed Unity files for dragging into an existing project."""
from pathlib import Path,PurePosixPath
import json,hashlib,zipfile
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).parent
OUTPUT=ROOT/'download-output/Sunward-Player-Fixes-3-UPDATE-ONLY.zip'

def sha(path):
 with path.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def main():
 manifest=json.loads((HERE/'update-manifest.json').read_text())
 assert manifest['deletedFiles']==[], 'This drop-in update must not require manual removals'
 OUTPUT.parent.mkdir(exist_ok=True)
 with zipfile.ZipFile(OUTPUT,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
  for item in manifest['files']:
   name=item['path'];parts=PurePosixPath(name).parts
   assert parts[0] in ('Assets','Packages','ProjectSettings') and '..' not in parts and not name.startswith('/')
   source=ROOT/'Sunward-Unity'/name
   assert source.stat().st_size==item['bytes'] and sha(source)==item['sha256'],name
   if source.stat().st_size<1024:assert not source.read_bytes().startswith(b'version https://git-lfs.github.com/spec/v1'),name
   info=zipfile.ZipInfo(name);info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
   z.writestr(info,source.read_bytes())
  docs={'START-HERE.txt':HERE/'START-HERE.txt','UPDATE-REPORT.md':HERE/'REPORT.md','ST0-INSPECTION.md':HERE/'ST0-INSPECTION.md','UPDATE-CONTENTS.json':HERE/'update-manifest.json','CHECK-RESULTS.json':HERE/'checks.json'}
  for name,path in docs.items():
   info=zipfile.ZipInfo(name);info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,path.read_bytes())
 with zipfile.ZipFile(OUTPUT) as z:
  assert z.testzip() is None
  assert not any(p.startswith(('Sunward-Unity/','Library/','Temp/')) for p in z.namelist())
  for item in manifest['files']:
   b=z.read(item['path']);assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256'],item['path']
  assert 'Assets/Sunward/Scenes/Windflower.unity' in z.namelist()
  assert b'Player fixes 3' in z.read('Assets/Sunward/Scripts/ScrollUI.cs')
  assert not any(p.endswith('Idle_Natural.anim') for p in z.namelist()),'Unchanged full animation should not be resent'
 OUTPUT.with_suffix('.zip.sha256').write_text(sha(OUTPUT)+'  '+OUTPUT.name+'\n')
 print('PASS:',len(manifest['files']),'changed/new project files;',OUTPUT.stat().st_size,'ZIP bytes; SHA256',sha(OUTPUT))
if __name__=='__main__':main()

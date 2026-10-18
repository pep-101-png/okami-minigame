from pathlib import Path
import zipfile,hashlib,json,shutil
R=Path(__file__).resolve().parents[2];release=R/'releases';release.mkdir(exist_ok=True)
files={}
for p in (R/'dist').rglob('*'):
 if p.is_file():files['Sunward-RPG/dist/'+str(p.relative_to(R/'dist'))]=p
files['Sunward-RPG/START-GAME.cmd']=R/'tools/expansion/START-PLAY.cmd';files['Sunward-RPG/server.mjs']=R/'tools/expansion/serve-game.mjs';files['Sunward-RPG/README.md']=R/'README.md';files['Sunward-RPG/LICENSE-THREE.txt']=R/'node_modules/three/LICENSE';files['Sunward-RPG/THIRD_PARTY.md']=R/'THIRD_PARTY.md'
with zipfile.ZipFile(release/'Sunward-RPG.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for name,p in files.items():z.write(p,name)
with zipfile.ZipFile(release/'Sunward-RPG.zip')as z:assert z.testzip()is None
manifest={'zip_sha256':hashlib.sha256((release/'Sunward-RPG.zip').read_bytes()).hexdigest(),'files':len(files),'model_sha256':hashlib.sha256((R/'public/models/amaterasu-original.glb').read_bytes()).hexdigest(),'node_required':True,'npm_install_required':False}
(release/'Sunward-RPG.json').write_text(json.dumps(manifest,indent=2));print(json.dumps(manifest,indent=2))

from pathlib import Path
import zipfile,hashlib,json
ROOT=Path(__file__).resolve().parent
names=['Amaterasu-Movement.blend','OPEN-IN-BLENDER.txt','README.md','LICENSE-SOURCE.txt']
archive=ROOT/'Amaterasu-Movement.zip'
with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=8)as z:
 for name in names:z.write(ROOT/name,'Amaterasu-Movement/'+name)
with zipfile.ZipFile(archive)as z:
 assert z.testzip()is None
 assert z.read('Amaterasu-Movement/Amaterasu-Movement.blend')==(ROOT/'Amaterasu-Movement.blend').read_bytes()
hashes={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest()for n in ['Amaterasu-Movement.blend',archive.name]}
(ROOT/'SHA256SUMS.txt').write_text('\n'.join(h+'  '+n for n,h in hashes.items())+'\n')
(ROOT/'review/package.json').write_text(json.dumps({'hashes':hashes,'zip_crc_passed':True,'blend_matches_zip':True,'bytes':{n:(ROOT/n).stat().st_size for n in hashes}},indent=2))
print('PACKAGE_VERIFIED',hashes)

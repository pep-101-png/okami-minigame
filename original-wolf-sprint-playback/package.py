from pathlib import Path
import hashlib,zipfile,json
R=Path(__file__).resolve().parent
files=['Amaterasu-Movement.blend','OPEN-IN-BLENDER.txt','README.md','LICENSE-SOURCE.txt']
with zipfile.ZipFile(R/'Amaterasu-Movement.zip','w',zipfile.ZIP_DEFLATED,compresslevel=9)as z:
 for name in files:z.write(R/name,name)
with zipfile.ZipFile(R/'Amaterasu-Movement.zip')as z:
 assert z.testzip()is None
 for name in files:assert z.read(name)==(R/name).read_bytes()
(R/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256((R/n).read_bytes()).hexdigest()+'  '+n+'\n'for n in ['Amaterasu-Movement.blend','Amaterasu-Movement.zip']))
print((R/'SHA256SUMS.txt').read_text())

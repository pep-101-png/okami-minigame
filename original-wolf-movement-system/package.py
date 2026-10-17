from pathlib import Path
import hashlib,json,zipfile,datetime
R=Path(__file__).resolve().parent
checks=json.loads((R/'review/validation.json').read_text());saved=json.loads((R/'review/saved-file.json').read_text());blend=R/'Amaterasu-Movement.blend'
assert checks['frames_tested']==3069 and checks['demo_max_ik_error']<.01
assert saved['saved_project_sha256']==hashlib.sha256(blend.read_bytes()).hexdigest()
review={'inspected_by':'Rendered images inspected visually by the assistant; user approval pending','current_views':86,'coverage':['idle gaze','left and right standing pivots','Walk left/right','Jog left/right','Sprint left/right','six gait transitions','showcase arc headings'],'source_sha256':'bcf79d66cd522bbca442982ff71d88a11fecb0391d727f3319496c78721d86e4','delivered_sha256':saved['saved_project_sha256'],'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'limits':['No independent eye rig','Actual viewport GPU FPS depends on hardware','Showcase contact correction must be rebaked if timing changes']}
(R/'review/visual-review.json').write_text(json.dumps(review,indent=2))
with zipfile.ZipFile(R/'Amaterasu-Movement.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for name in ['Amaterasu-Movement.blend','OPEN-IN-BLENDER.txt','README.md','LICENSE-SOURCE.txt']:z.write(R/name,name)
with zipfile.ZipFile(R/'Amaterasu-Movement.zip')as z:
 assert z.testzip()is None
 assert hashlib.sha256(z.read(blend.name)).hexdigest()==saved['saved_project_sha256']
(R/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256((R/n).read_bytes()).hexdigest()+'  '+n+'\n'for n in ['Amaterasu-Movement.blend','Amaterasu-Movement.zip']))
print((R/'SHA256SUMS.txt').read_text())

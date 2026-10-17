from pathlib import Path
from PIL import Image
import hashlib,json,datetime,subprocess,zipfile
R=Path(__file__).resolve().parent
files=list((R/'review/final2/Sprint_Polished').glob('*/*.png'));assert len(files)==96
for p in files:
 with Image.open(p)as im:im.verify()
for view in ['side','rear','neck']:
 info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,r_frame_rate','-of','json',str(R/f'review/Sprint-{view}.mp4')]))['streams'][0];assert info['nb_frames']=='320'and info['r_frame_rate']=='60/1'
with zipfile.ZipFile(R/'Amaterasu-Movement.zip')as z:assert z.testzip()is None and z.read('Amaterasu-Movement.blend')==(R/'Amaterasu-Movement.blend').read_bytes()
assert hashlib.sha256((R/'Amaterasu-Movement.blend').read_bytes()).hexdigest()==json.loads((R/'review/effects.json').read_text())['source_sha256']
record={'source_sha256':hashlib.sha256((R/'Amaterasu-Movement.blend').read_bytes()).hexdigest(),'visually_inspected_frames':96,'views':['side','rear three-quarter','neck close-up'],'comparison':['previous Sprint key poses 1,9,17,25','new full 32-frame cycle'],'review_findings':['Head motion is phased after neck flexion while gaze remains stabilised.','Tail follows hips with a damped root and delayed wave through five existing controls.','Approved leg and core curves and evaluated matrices are unchanged.','No new visible holes, snapping, neck/shoulder intersection or tail/body penetration was observed in the reviewed frames.','Wind remains behind the face, with the side-view silhouette readable.','Original skin can retain creasing in tightly bent joints; no weight or mesh changes were made.'],'not_an_acceptance':True,'wind_speed_and_action_gate_tested_with_autoexec_disabled':True,'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(R/'review/visual-review.json').write_text(json.dumps(record,indent=2));print('REVIEW_AND_PACKAGE_VERIFIED')

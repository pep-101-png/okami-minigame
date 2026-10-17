from pathlib import Path
from PIL import Image
import json,hashlib,subprocess,zipfile,datetime
R=Path(__file__).resolve().parent;files=list((R/'review/renders').glob('*/*/*.png'));assert len(files)==96
for p in files:
 with Image.open(p)as im:im.verify()
for view in ['side','neck']:
 info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,r_frame_rate','-of','json',str(R/f'review/Sprint-{view}.mp4')]))['streams'][0];assert info['nb_frames']=='320'and info['r_frame_rate']=='60/1'
with zipfile.ZipFile(R/'Amaterasu-Movement.zip')as z:assert z.testzip()is None and z.read('Amaterasu-Movement.blend')==(R/'Amaterasu-Movement.blend').read_bytes()
assert hashlib.sha256((R/'Amaterasu-Movement.blend').read_bytes()).hexdigest()==json.loads((R/'review/layers.json').read_text())['source_sha256']
(R/'review/visual-review.json').write_text(json.dumps({'new_cycle_frames_inspected':72,'prior_comparison_keyframes':24,'views':['32 side frames','32 neck close-ups','8 front poses'],'findings':['More changing neck curvature with partial gaze stabilisation.','No new visible neck holes, joint collapse or snapping in the reviewed frames.','Body, legs, tail and timing tracks match the previous clip.','Cached subdivision preserves evaluated surface vertices and normals exactly in retained poses.','Finished wind is unchanged; FAST uses a deliberately simplified viewport preview.'],'cpu_bottleneck_removed':True,'windows_60fps_not_verified':True,'software_display_remains_gpu_limited':True,'not_accepted_until_user_review':True,'sha256':hashlib.sha256((R/'Amaterasu-Movement.blend').read_bytes()).hexdigest(),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat()},indent=2));print('REVIEW_PACKAGE_AND_FINAL_FILE_HASH_VERIFIED')

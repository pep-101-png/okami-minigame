from pathlib import Path
import json,hashlib,zipfile,datetime
R=Path(__file__).resolve().parent;v=json.load(open(R/'review/validation.json'));saved=json.load(open(R/'review/saved-file.json'))
assert not v['action_problems'] and v['demo']['maximum_ik_error']<.015 and v['demo']['maximum_frame_upper_leg_rotation_deg']<65
assert v['original_geometry_rig_weights_materials_textures_exact']and v['all_previous_actions_exact']
assert saved['sha256']==hashlib.sha256((R/'Amaterasu-Movement.blend').read_bytes()).hexdigest()
images=list((R/'review/final-renders').glob('*/*.png'));assert len(images)>=210
review={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'delivered_sha256':saved['sha256'],'rendered_views':len(images),'new_actions':15,'showcase_cases':14,'frames_checked':2539,'visual_review':'Side/rear contact sheets for all 15 Actions and showcase images inspected by assistant; user artistic approval pending. Corrected sprint takeoff handoff, safe IK reach and sparse subframe paw clearance.','limits':['Fixed trajectory animations need runtime terrain/root-motion handling later','Showcase contact layer must be rebaked if timing changes','Actual GPU viewport FPS is hardware dependent']}
(R/'review/visual-review.json').write_text(json.dumps(review,indent=2))
with zipfile.ZipFile(R/'Amaterasu-Movement.zip','w',zipfile.ZIP_DEFLATED,compresslevel=6)as z:
 for name in ['Amaterasu-Movement.blend','OPEN-IN-BLENDER.txt','README.md','LICENSE-SOURCE.txt']:z.write(R/name,name)
with zipfile.ZipFile(R/'Amaterasu-Movement.zip')as z:assert z.testzip()is None;assert hashlib.sha256(z.read('Amaterasu-Movement.blend')).hexdigest()==saved['sha256']
(R/'SHA256SUMS.txt').write_text(''.join(hashlib.sha256((R/n).read_bytes()).hexdigest()+'  '+n+'\n'for n in ['Amaterasu-Movement.blend','Amaterasu-Movement.zip']))
print((R/'SHA256SUMS.txt').read_text())

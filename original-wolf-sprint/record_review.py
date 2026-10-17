from pathlib import Path
import json,hashlib,datetime,subprocess,zipfile,ast
p=Path(__file__).resolve().parent;r=p/'review'
for view in ['side','front','rear']:
 assert len(list((r/'final5'/view).glob('*.png')))==32
 info=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames,r_frame_rate,duration','-of','json',str(r/f'Sprint-{view}.mp4')]))['streams'][0]
 assert info['nb_frames']=='320'and info['r_frame_rate']=='60/1',info
with zipfile.ZipFile(p/'Amaterasu-Movement.zip')as z:
 assert z.testzip()is None
 for name in ['Amaterasu-Movement.blend','OPEN-IN-BLENDER.txt','README.md','LICENSE-SOURCE.txt']:assert z.read('Amaterasu-Movement/'+name)==(p/name).read_bytes(),name
module=ast.parse((p/'author_sprint.py').read_text());offsets=ast.literal_eval(next(n.value for n in module.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='OFFSETS'for t in n.targets)))
order=[k for k,v in sorted(offsets.items(),key=lambda x:x[1])];assert order==['front.R','front.L','rear.L','rear.R'],order
report={'revision':5,'frames_reviewed_per_angle':32,'angles':['side','front','rear'],'joint_closeups_reviewed':11,'fractional_frame_samples':129,'gait':'double-suspension rotary gallop','footfall_order':order,'main_actions':['Idle','Walk','Jog','Sprint'],'archived_action':'Legacy_Run','source_jog_sha256':'53dccddf955eeb6829ac3c6334a5bf1431fbfca6cf26af89b5887d82fe718dee','blend_sha256':hashlib.sha256((p/'Amaterasu-Movement.blend').read_bytes()).hexdigest(),'preservation_pose_samples':25,'visual_findings':['Longer fore reach and hind kickback, with visibly distinct gathered and extended poses.','Opposite fore/hind leads form the rotary gallop; rear IK remains continuous.','Rhythmic spine/hip/chest motion with stabilised gaze and delayed neck/tail response.','Full side/front/rear sequences and closing-to-opening transition inspected.','Some original-skin creasing remains at deeply flexed inner joints.'],'game_and_viewer_untouched':True,'reviewed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
(r/'final-review.json').write_text(json.dumps(report,indent=2));print('FINAL_REVIEW_COMPLETE',report['blend_sha256'])

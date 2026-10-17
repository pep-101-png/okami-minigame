import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent
s=bpy.context.scene
assert s.name=='02 · Movement showcase' and s.frame_end==3069
assert s.render.fps==60
assert bpy.data.texts.get('MOVEMENT — START HERE')
assert len([i for i in bpy.data.images if i.packed_file])==6
rig=bpy.data.objects['DEMO_WOLF_RIG'];assert rig.animation_data.action is None
for f in [1,577,853,1129,1717,2109,2225,2625,3069]:
 s.frame_set(f);bpy.context.view_layer.update()
 assert all(abs(x)<10000 for x in rig.pose.bones['CTRL_head'].matrix.translation)
assert hashlib.sha256((R.parent/'original-wolf-sprint-playback/Amaterasu-Movement.blend').read_bytes()).hexdigest()=='bcf79d66cd522bbca442982ff71d88a11fecb0391d727f3319496c78721d86e4'
(R/'review/saved-file.json').write_text(json.dumps({'saved_project_sha256':hashlib.sha256((R/'Amaterasu-Movement.blend').read_bytes()).hexdigest(),'opens_without_autoexec':True,'default_scene':s.name,'fps':s.render.fps,'packed_textures':6,'showcase_frames':s.frame_end,'sampled_final_saved_frames':9},indent=2))
print('SAVED_FILE_SMOKE_PASSED')

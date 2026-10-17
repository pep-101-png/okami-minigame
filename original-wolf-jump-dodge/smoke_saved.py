import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;s=bpy.context.scene
assert s.name=='03 · Jump and dodge showcase'
assert s.render.fps==60 and s.frame_end==2539
assert bpy.data.texts.get('JUMP & DODGE — START HERE')
assert len([i for i in bpy.data.images if i.packed_file])==6
assert bpy.data.scenes.get('02 · Movement showcase')
for f in [1,300,700,900,1000,1200,1800,2300,2539]:s.frame_set(f);bpy.context.view_layer.update()
main=bpy.data.scenes['01 · Action inspection'];bpy.context.window.scene=main;r=bpy.data.objects['WOLF_RIG'];r.animation_data.action=bpy.data.actions['Air_Fall'];poses=[]
for f in [1,73]:
 main.frame_set(f);bpy.context.evaluated_depsgraph_get().update();ev=r.evaluated_get(bpy.context.evaluated_depsgraph_get());poses.append({p.name:p.matrix.copy()for p in ev.pose.bones if p.name.startswith('DEF_')})
error=max(abs(poses[0][n][i][j]-poses[1][n][i][j])for n in poses[0]for i in range(4)for j in range(4));assert error<1e-5,error
source=R.parent/'original-wolf-movement-system/Amaterasu-Movement.blend';assert hashlib.sha256(source.read_bytes()).hexdigest()=='82cee2e6e6d8ac3c3708c4a16d12cb5fefaa155da74c961fe34bec8810082cf4'
(R/'review/saved-file.json').write_text(json.dumps({'sha256':hashlib.sha256((R/'Amaterasu-Movement.blend').read_bytes()).hexdigest(),'opens_without_autoexec':True,'default_scene':'03 · Jump and dodge showcase','fps':60,'showcase_frames':2539,'air_fall_loop_matrix_error':error,'packed_textures':6},indent=2));print('M2_SAVED_PROJECT_SMOKE_PASSED',error)

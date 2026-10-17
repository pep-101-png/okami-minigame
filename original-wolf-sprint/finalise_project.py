import bpy,ast,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
node=next(n for n in ast.parse((ROOT.parent/'original-wolf-run-refinement/refine_run.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='action_hash');exec(compile(ast.Module(body=[node],type_ignores=[]),'<fingerprint>','exec'))
r=bpy.data.objects['WOLF_RIG'];s=bpy.context.scene;before={a.name:action_hash(a)for a in bpy.data.actions}
t=bpy.data.texts.get('MOVEMENT — START HERE')or bpy.data.texts.new('MOVEMENT — START HERE');t.clear();t.write((ROOT/'OPEN-IN-BLENDER.txt').read_text())
r.animation_data.action=bpy.data.actions['Sprint'];r.animation_data.action['export_note']='In-place. Bake/sample existing IK constraints on deform bones at 60 fps for game export.'
s.frame_set(1);s.frame_start=1;s.frame_end=1440;s.use_preview_range=False;s.sync_mode='FRAME_DROP'
assert before=={a.name:action_hash(a)for a in bpy.data.actions}
assert all(1440%n==0 for n in [240,72,40,32])
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Amaterasu-Movement.blend'))
print('FINAL_DEFAULT',r.animation_data.action.name,'ACTIONS',list(before),'PACKED_TEXTURES',len([i for i in bpy.data.images if i.packed_file]),flush=True)

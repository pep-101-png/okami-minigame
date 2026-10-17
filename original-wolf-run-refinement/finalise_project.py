"""Save playback instructions without changing animation curves or model data."""
import bpy,hashlib,json,ast
from pathlib import Path
ROOT=Path(__file__).resolve().parent
node=next(n for n in ast.parse((ROOT/'refine_run.py').read_text()).body if isinstance(n,ast.FunctionDef)and n.name=='action_hash');exec(compile(ast.Module(body=[node],type_ignores=[]),'<fingerprint>','exec'))
r=bpy.data.objects['WOLF_RIG'];s=bpy.context.scene
before={a.name:action_hash(a)for a in bpy.data.actions}
name='RUN REFINEMENT — START HERE';text=bpy.data.texts.get(name)or bpy.data.texts.new(name);text.clear();text.write((ROOT/'OPEN-IN-BLENDER.txt').read_text())
r.animation_data.action=bpy.data.actions['RUN_REFINED'];s.frame_set(1);s.frame_start=1;s.frame_end=720;s.use_preview_range=False;s.sync_mode='FRAME_DROP'
assert before=={a.name:action_hash(a)for a in bpy.data.actions}
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Amaterasu-Run-Refined.blend'))
print('DELIVERY_DEFAULT',r.animation_data.action.name,'ACTIONS',list(before),'TEXTURES',len([i for i in bpy.data.images if i.packed_file]),flush=True)

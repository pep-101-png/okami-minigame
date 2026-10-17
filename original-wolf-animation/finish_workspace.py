"""Save an immediately accessible Action dropdown; no animation/model changes."""
import bpy,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent;rig=bpy.data.objects['WOLF_RIG']
def actions_hash():
    return hashlib.sha256(json.dumps({a.name:[(f.data_path,f.array_index,[(list(k.co),k.interpolation)for k in f.keyframe_points])for f in a.fcurves]for a in bpy.data.actions},sort_keys=True).encode()).hexdigest()
before=actions_hash()
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='DOPESHEET_EDITOR' and (screen.name.startswith('Layout') or area.ui_type!='TIMELINE'):
            area.ui_type='DOPESHEET';area.spaces.active.mode='ACTION'
            area.spaces.active.show_region_ui=False
if bpy.context.window:bpy.context.window.workspace=bpy.data.workspaces['Layout']
rig.animation_data.action=bpy.data.actions['WALK'];bpy.context.scene.frame_set(1)
bpy.context.scene.frame_start=1;bpy.context.scene.frame_end=720
assert actions_hash()==before
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'Amaterasu-Idle-Walk-Run.blend'))
(ROOT/'review/workspace-validation.json').write_text(json.dumps({'action_curves_sha256':before,'actions_unchanged':True,'default_action':'WALK','common_review_range':720,'layout_action_editor':True},indent=2))

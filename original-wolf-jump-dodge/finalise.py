import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent;s=bpy.data.scenes['03 · Jump and dodge showcase'];bpy.context.window.scene=s
text=bpy.data.texts.get('JUMP & DODGE — START HERE')or bpy.data.texts.new('JUMP & DODGE — START HERE');text.clear();text.write((R/'OPEN-IN-BLENDER.txt').read_text())
info=json.load(open(R/'review/authoring.json'))['actions']
for name in info:
 a=bpy.data.actions[name]
 if not a.asset_data:a.asset_mark()
 if not a.asset_data.tags.get('Milestone 2'):a.asset_data.tags.new('Milestone 2')
cam=s.camera
# Pull back only for the high double-jump/drop sections. Native camera keys.
cam.data.ortho_scale=15;cam.data.keyframe_insert('ortho_scale',frame=1)
for row in json.load(open(R/'review/demo.json'))['cases']:
 if row['name']not in ['Double jump + soft landing','Large fall + heavy landing']:continue
 for f,v in [(row['start']-12,15),(row['start']+12,20),(row['end']-12,20),(row['end']+12,15)]:cam.data.ortho_scale=v;cam.data.keyframe_insert('ortho_scale',frame=f)
if cam.data.animation_data:
 for fc in cam.data.animation_data.action.fcurves:
  for k in fc.keyframe_points:k.interpolation='BEZIER';k.handle_left_type='AUTO_CLAMPED';k.handle_right_type='AUTO_CLAMPED'
s.frame_set(1);s.use_preview_range=False
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Amaterasu-Movement.blend'));print('M2_FINAL_SAVED')

import bpy,json
from pathlib import Path
R=Path(__file__).resolve().parent;main=bpy.data.scenes['01 · Action inspection'];demo=bpy.data.scenes['02 · Movement showcase']
main.frame_start=1;main.frame_end=1440;main.use_preview_range=False;original=bpy.data.objects['WOLF_RIG'];original.animation_data.action=bpy.data.actions['Idle_Natural']
public=['Idle_Natural','Walk_Natural','Jog_Natural','Sprint_Fluid','Walk_Turn_L','Walk_Turn_R','Jog_Turn_L','Jog_Turn_R','Sprint_Turn_L','Sprint_Turn_R','Idle_Turn_L90','Idle_Turn_R90','ADD_LookAround']
for a in bpy.data.actions:
 if a.name.startswith('.DEMO_'):a.asset_clear()
 if a.name in public:
  if not a.asset_data:a.asset_mark()
  if not a.asset_data.tags.get('Natural movement'):a.asset_data.tags.new('Natural movement')
  if a.name!='Sprint_Fluid':a.asset_data.description=a.name.replace('_',' ')+' · original wolf, existing control rig; see movement guide.'
text=bpy.data.texts.get('MOVEMENT — START HERE')or bpy.data.texts.new('MOVEMENT — START HERE');text.clear();text.write((R/'OPEN-IN-BLENDER.txt').read_text())
bpy.context.window.scene=demo;demo.frame_set(1);demo.use_preview_range=False
for a in bpy.context.screen.areas:
 if a.type=='VIEW_3D':a.spaces.active.region_3d.view_perspective='CAMERA';a.spaces.active.overlay.show_overlays=False
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Amaterasu-Movement.blend'));print('FINAL_MOVEMENT_PROJECT_SAVED')

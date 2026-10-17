import bpy
from pathlib import Path
R=Path(__file__).resolve().parent;s=bpy.context.scene;s.view_layers['FAST · Lightweight wind'].use=False
bpy.context.window.view_layer=s.view_layers['FULL · Painted wind'];r=bpy.data.objects['WOLF_RIG'];r.animation_data.action=bpy.data.actions['Sprint_Fluid'];s.frame_set(1)
t=bpy.data.texts['SPRINT FLUID — START HERE'];t.clear();t.write((R/'OPEN-IN-BLENDER.txt').read_text())
bpy.ops.wm.save_as_mainfile(filepath=str(R/'Amaterasu-Movement.blend'));print('FINALISED')

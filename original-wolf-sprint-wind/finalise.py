import bpy
from pathlib import Path
R=Path(__file__).resolve().parent
for seq in [bpy.data.objects,bpy.data.shape_keys]:
 for o in seq:
  if o.animation_data:
   for fc in o.animation_data.drivers:
    fc.driver.expression=fc.driver.expression.replace('min(1,max(0,speed/14.625))**2','min(1,max(0,speed/14.625))*min(1,max(0,speed/14.625))')
    assert fc.driver.is_simple_expression,(o.name,fc.driver.expression)
t=bpy.data.texts.get('SPRINT WIND — START HERE');t.clear();t.write((R/'OPEN-IN-BLENDER.txt').read_text())
bpy.context.scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(R/'Amaterasu-Movement.blend'));print('ALL_DRIVERS_NATIVE_SIMPLE',flush=True)

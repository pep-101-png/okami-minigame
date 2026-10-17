import bpy,json,math
from pathlib import Path
R=Path(__file__).resolve().parent;s=bpy.context.scene;r=bpy.data.objects['WOLF_RIG'];ctrl=bpy.data.objects['SPRINT_WIND · speed control'];wind=bpy.data.objects['Wind ribbon 01'];r.animation_data.action=bpy.data.actions['Sprint_Polished'];results={}
for name in ['Idle','Walk','Jog','Sprint','Sprint_Polished']:
 r.animation_data.action=bpy.data.actions[name];s.frame_set(1);bpy.context.view_layer.update();e=wind.evaluated_get(bpy.context.evaluated_depsgraph_get());results[name]={'scale':list(e.scale),'opacity':e.color[3]}
 assert(e.scale.x>.99 and e.color[3]>.99 if name=='Sprint_Polished'else max(e.scale)<1e-6 and e.color[3]<1e-6)
r.animation_data.action=bpy.data.actions['Sprint_Polished'];ctrl.animation_data.action=bpy.data.actions['Wind_Speed_Demo'];demo={}
for f in [1,9,17,65,97,113,129]:
 s.frame_set(f);e=wind.evaluated_get(bpy.context.evaluated_depsgraph_get());demo[f]={'speed':ctrl['speed'],'opacity':e.color[3],'length_factor':e.scale.y}
assert demo[1]['opacity']==0 and demo[129]['opacity']==0 and demo[65]['opacity']>.99
assert 0<demo[9]['opacity']<1 and 0<demo[113]['opacity']<1
ctrl.animation_data.action=None;ctrl['speed']=14.625;ctrl.update_tag()
def coords(f):
 s.frame_set(f);dep=bpy.context.evaluated_depsgraph_get();row={}
 for o in bpy.data.collections['05 · Sprint wind — separate effect'].objects:
  if o.type=='MESH':
   e=o.evaluated_get(dep);me=e.to_mesh();row[o.name]=[e.matrix_world@v.co for v in me.vertices];e.to_mesh_clear()
 return row
x=coords(1);y=coords(33);error=max((a-b).length for n in x for a,b in zip(x[n],y[n]));assert error<1e-5,error
all_drivers=[fc for seq in [bpy.data.objects,bpy.data.shape_keys]for o in seq if o.animation_data for fc in o.animation_data.drivers]
print('DRIVER_DIAG',[(fc.data_path,fc.driver.expression,fc.driver.is_valid,fc.driver.is_simple_expression)for fc in all_drivers if not(fc.driver.is_valid and fc.driver.is_simple_expression)],flush=True)
assert all(fc.driver.is_valid and fc.driver.is_simple_expression for fc in all_drivers)
(R/'review/effects.json').write_text(json.dumps({'gates':results,'speed_fade_demo':demo,'wind_loop_error':error,'simple_native_drivers':len(all_drivers),'source_sha256':__import__('hashlib').sha256((R/'Amaterasu-Movement.blend').read_bytes()).hexdigest()},indent=2));print('EFFECT_GATING_OPACITY_FADE_AND_LOOP_PASS',flush=True)

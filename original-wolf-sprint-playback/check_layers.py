import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent;s=bpy.context.scene;r=bpy.data.objects['WOLF_RIG'];rows={}
for layer in s.view_layers:
 bpy.context.window.view_layer=layer;rows[layer.name]={}
 target='PREVIEW · Wind ribbon 01'if layer.name.startswith('FAST')else'Wind ribbon 01'
 for name in ['Idle','Walk','Jog','Sprint','Sprint_Polished','Sprint_Fluid']:
  r.animation_data.action=bpy.data.actions[name];s.frame_set(4);bpy.context.view_layer.update();e=bpy.data.objects[target].evaluated_get(bpy.context.evaluated_depsgraph_get());rows[layer.name][name]=list(e.scale)
  assert(e.scale.x>.99 if name in ['Sprint_Polished','Sprint_Fluid']else max(e.scale)<1e-6),(layer.name,name,list(e.scale))
 assert(layer.use if layer.name.startswith('FULL')else not layer.use)
assert all(o.hide_render for o in bpy.data.collections['06 · Lightweight wind preview (viewport only)'].objects)
assert s.render.fps==60 and s.render.fps_base==1 and s.sync_mode=='FRAME_DROP'
(R/'review/layers.json').write_text(json.dumps({'gates':rows,'render_uses_full_effect_only':True,'fps':60,'fps_base':1,'sync':'FRAME_DROP','source_sha256':hashlib.sha256((R/'Amaterasu-Movement.blend').read_bytes()).hexdigest()},indent=2));print('LAYER_GATING_AND_RENDER_ISOLATION_PASS',flush=True)

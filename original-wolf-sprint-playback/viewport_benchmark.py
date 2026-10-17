import bpy,time,json,os
from pathlib import Path
R=Path(__file__).resolve().parent
state={'phase':-1,'start':0,'sample_start':None,'draws':[],'results':{}}
modes=[('FULL · Painted wind','MATERIAL'),('FAST · Lightweight wind','MATERIAL'),('FAST · Lightweight wind','SOLID')]
def draw():
 if state['sample_start']is not None and bpy.context.screen.is_animation_playing:
  row=(time.perf_counter(),bpy.context.scene.frame_current)
  if not state['draws']or row[1]!=state['draws'][-1][1]:state['draws'].append(row)
bpy.types.SpaceView3D.draw_handler_add(draw,(),'WINDOW','POST_PIXEL')
def tick():
 now=time.perf_counter();w=bpy.context.window;screen=w.screen;area=max((a for a in screen.areas if a.type=='VIEW_3D'),key=lambda a:a.width*a.height)
 if state['phase']<0:
  state['phase']=0;state['start']=now;w.view_layer=bpy.context.scene.view_layers[modes[0][0]];area.spaces.active.shading.type='MATERIAL'
  with bpy.context.temp_override(area=area):bpy.ops.screen.animation_play()
 elif state['sample_start']is None and now-state['start']>=8:
  state['sample_start']=now;state['draws']=[]
 elif state['sample_start']is not None and now-state['sample_start']>=8:
  samples=state['draws'];elapsed=now-state['sample_start'];name=' / '.join(modes[state['phase']]);deltas=[b[0]-a[0]for a,b in zip(samples,samples[1:])];state['results'][name]={'drawn_fps':len(samples)/elapsed,'drawn_frames':len(samples),'elapsed':elapsed,'frame_values':[x[1]for x in samples],'viewport_size':[area.width,area.height],'mode':'software-rendered local display; not Windows GPU hardware'};print('VIEWPORT_BENCH',name,len(samples)/elapsed,flush=True)
  if screen.is_animation_playing:
   with bpy.context.temp_override(area=area):bpy.ops.screen.animation_cancel(restore_frame=False)
  state['phase']+=1
  if state['phase']==len(modes):
   (R/'review/viewport.json').write_text(json.dumps(state['results'],indent=2));bpy.ops.wm.quit_blender();return None
  layer,shading=modes[state['phase']];w.view_layer=bpy.context.scene.view_layers[layer];area.spaces.active.shading.type=shading;state['start']=now;state['sample_start']=None
  with bpy.context.temp_override(area=area):bpy.ops.screen.animation_play()
 return .1
bpy.app.timers.register(tick,first_interval=3)

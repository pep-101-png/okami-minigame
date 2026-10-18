"""Three new original-rig actions; source mesh, weights and existing actions are untouched."""
import bpy,math,json
from mathutils import Vector
reset();s.frame_set(2);bpy.context.view_layer.update();s.frame_set(1);REF=soles();REST={n:r.pose.bones[n].matrix.copy()for n in CTRL};report={}
for name,N in [('Sleep_Down',100),('Sleep_Loop',240),('Sleep_Up',100)]:
 a=bpy.data.actions.new(name);a.use_fake_user=True;a['duration_frames']=N;a.use_frame_range=True;a.frame_start=1;a.frame_end=N+1;errors=[];body_floor=[]
 for f in sorted(set(range(0,N+1,3))|{N}):
  t=f/N;w=smooth(t)if name=='Sleep_Down'else 1-smooth(t)if name=='Sleep_Up'else 1;breath=math.sin(t*math.tau)*.035 if name=='Sleep_Loop'else 0;reset();body(f,N,-2.40*w+breath,-3*w,8*w,energy=.08)
  rotate('CTRL_neck_base',x=26*w);rotate('CTRL_neck_upper',x=24*w);rotate('CTRL_head',x=-15*w,y=3*w);rotate('CTRL_ear.L',x=-15*w,y=4*w);rotate('CTRL_ear.R',x=-8*w,y=-4*w)
  # Overlapping tail sections curl around the flank instead of rotating the whole wolf.
  for i in range(1,6):rotate(f'CTRL_tail_{i:02}',x=(-7-i*2)*w,y=(4+i*2)*w,z=(12+i*4)*w)
  goals={}
  for key,d in feet.items():
   v=REF[key]['center'].copy();front=key.startswith('front');v.y+=(-1.25 if front else -.72)*w;v.x+=d['sign']*(.08 if front else .70)*w;goals[key]={'center':v,'z':.035};rotate('CTRL_toes_'+key,x=-4*w)
  solve(goals);errors.append(max(ikerrors().values()));capture(a,f+1)
 finish(a,name=='Sleep_Loop');report[name]={'frames':N,'maximum_sampled_ik_error':max(errors)};assert max(errors)<.02,(name,max(errors))
(R/'notes/organic/sleep-authoring.json').write_text(json.dumps(report,indent=2));print('SLEEP_ACTIONS_AUTHORED',flush=True)

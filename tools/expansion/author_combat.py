"""Original-rig combat poses for the game export only. No source .blend is saved."""
import bpy,math,json
from pathlib import Path
from mathutils import Vector,Quaternion,Matrix
R=Path(__file__).resolve().parents[2];s=bpy.data.scenes['01 · Action inspection'];bpy.context.window.scene=s;r=bpy.data.objects['WOLF_RIG'];CTRL=[p.name for p in r.pose.bones if p.name.startswith('CTRL_')]
# Reuse the milestone's tested paw solver and coordinated torso/neck/tail controls.
exec(compile((R/'tools/expansion/rig_helpers.py').read_text(),'<existing animation helpers>','exec'))
reset();s.frame_set(2);bpy.context.view_layer.update();s.frame_set(1);foot=bpy.data.objects['Object_11'];M=foot.evaluated_get(bpy.context.evaluated_depsgraph_get()).matrix_world.copy();feet={}
for kind in ['front','rear']:
 for side,sign in [('L',1),('R',-1)]:feet[kind+'.'+side]={'ids':[v.index for v in foot.data.vertices if(p:=M@v.co).z<.17 and sign*p.x>.25 and(p.y<-.9 if kind=='front'else p.y>1)],'ctrl':'CTRL_paw_'+kind+'.'+side,'sign':sign}
REF=soles();REST={n:r.pose.bones[n].matrix.copy()for n in CTRL}
configs={'Thrust':(24,0,0),'Sweep':(29,32,0),'Finish':(40,-14,.26),'HeavyArc':(36,18,.30),'HeavyReturn':(42,-28,.23),'ChargedThrust':(39,5,.17),'ChargedHeavy':(52,-12,.48),'AirStrike':(44,0,0),'ChargeLight':(45,0,0),'ChargeHeavy':(45,0,0),'Bark':(33,0,0),'Disc1':(22,25,.06),'Disc2':(29,-38,.18),'Disc3':(40,44,.28),'DiscHeavy':(40,-34,.32),'DiscCharged':(51,48,.4)}
report={}
for name,(N,twist,lift)in configs.items():
 a=bpy.data.actions.new(name);a.use_fake_user=True;a.use_frame_range=True;a.frame_start=1;a.frame_end=N+1;a['duration_frames']=N;errors=[];floor=[]
 for f in sorted(set(range(0,N+1,2))|{N}):
  t=f/N;w=smooth(t)if name.startswith('Charge')and name in['ChargeLight','ChargeHeavy']else math.sin(math.pi*t)**2;reset()
  crouch=-(.35 if name in['Bark','ChargeHeavy','ChargedHeavy']else .17)*w;pitch=(8 if name in['AirStrike','HeavyArc']else-4 if name in['Finish','ChargedHeavy']else 3)*w
  body(f,N,crouch,pitch,12*w,lean=math.sin(t*math.tau)*.8,twist=twist*math.sin(math.pi*t)*(.3+.7*smooth((t-.1)/.4)),energy=.8)
  r.pose.bones['CTRL_body'].location.y+=(.32 if name in['Thrust','ChargedThrust','Finish']else .10)*math.sin(math.pi*t)*w
  if name=='Bark':rotate('CTRL_jaw',x=8*math.sin(math.pi*t)**2)
  goals={}
  for key,d in feet.items():
   front=key.startswith('front');v=REF[key]['center'].copy();h=lift*math.sin(math.pi*t)**2 if front else lift*.2*math.sin(math.pi*t)**2
   if name=='AirStrike':h=.15 if front else .55;v.y+=(-.15 if front else .25)*w
   if name=='Bark':v.x+=d['sign']*.14*w;v.y-=.12*w if front else 0
   goals[key]={'center':v,'z':.035+h};rotate('CTRL_toes_'+key,x=5*w)
  obs=solve(goals);errors.append(max(ikerrors().values()));floor.append(min(v['z']for v in obs.values()));capture(a,f+1)
 finish(a,False);report[name]={'frames':N,'maximum_sampled_ik_error':max(errors),'minimum_paw_z':min(floor)}
 assert max(errors)<.01,(name,max(errors))
 print('COMBAT_POSE',name,report[name],flush=True)
(R/'notes/expansion/combat-export.json').write_text(json.dumps(report,indent=2))

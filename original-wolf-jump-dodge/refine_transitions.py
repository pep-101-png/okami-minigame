"""Align NLA entry/exit phases at the overlap, then rebake only demo paw support."""
import bpy,json,ast,math
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parent;s=bpy.data.scenes['03 · Jump and dodge showcase'];bpy.context.window.scene=s;r=bpy.data.objects['JUMP_DEMO_WOLF_RIG'];foot=bpy.data.objects['M2 · Object_11'];CTRL=[p.name for p in r.pose.bones if p.name.startswith('CTRL_')];data=json.load(open(R/'review/demo.json'));segments=data['segments'];END=s.frame_end;feet={};M=foot.matrix_basis
for kind in ['front','rear']:
 for side,sign in [('L',1),('R',-1)]:feet[kind+'.'+side]={'ids':[v.index for v in foot.data.vertices if(p:=M@v.co).z<.17 and sign*p.x>.25 and(p.y<-.9 if kind=='front'else p.y>1)],'ctrl':'CTRL_paw_'+kind+'.'+side}
for k,v in feet.items():assert len(v['ids'])>100,k
speednames=['Idle','Idle_Natural','Walk_Natural','Jog_Natural','Sprint_Fluid'];changed=[]
for i,seg in enumerate(segments):
 if seg['action']not in speednames:continue
 phase=seg['phase']
 if i+1<len(segments)and segments[i+1]['case']==seg['case']and segments[i+1]['action']not in speednames:
  following=segments[i+1];a=bpy.data.actions[following['action']];phase=float(a.get('entry_phase',0))-(following['start']-seg['start'])/seg['N']
 elif i and segments[i-1]['case']==seg['case']and segments[i-1]['action']not in speednames:
  previous=segments[i-1];a=bpy.data.actions[previous['action']];phase=float(a.get('exit_phase',0))-(previous['end']-seg['start'])/seg['N']
 if abs(phase-seg['phase'])<1e-8:continue
 changed.append({'action':seg['action'],'start':seg['start'],'old_phase':seg['phase'],'phase':phase});seg['phase']=phase
 strip=r.animation_data.nla_tracks[i].strips[0]
 fc=next(fc for fc in strip.fcurves if fc.data_path=='strip_time');fc.keyframe_points[0].co.y=1+phase*seg['N'];fc.keyframe_points[-1].co.y=1+phase*seg['N']+seg['duration'];fc.update()
track=next(t for t in r.animation_data.nla_tracks if t.name.startswith('CONTACT'));track.mute=True;existing=track.strips[0].action
source=(R/'demo.py').read_text()
for node in ast.parse(source).body:
 if isinstance(node,ast.FunctionDef)and node.name in ['smooth','reduce','soles']:exec(compile(ast.Module(body=[node],type_ignores=[]),'<existing contact solver>','exec'))
block=source[source.index('bpy.context.window.scene=s;r.animation_data.action=None;states='):source.index('for fc in path.fcurves:\n values=')]
block=block.replace("cor=bpy.data.actions.new('M2_CONTACT · Blended paw support');cor.use_fake_user=True","cor=existing\nfor fc in list(cor.fcurves):cor.fcurves.remove(fc)")
start=block.index("r.animation_data.use_nla=True;track=r.animation_data.nla_tracks.new();track.name='CONTACT")
block=block[:start]+"r.animation_data.use_nla=True;track.mute=False\n"
exec(compile(block,'<rebake corrected phase transitions>','exec'))
data['segments']=segments;data['phase_alignment']=changed;data['contact_samples']=checks;data['contact_keys']=sum(len(fc.keyframe_points)for fc in existing.fcurves);(R/'review/demo.json').write_text(json.dumps(data,indent=2));s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(R/'Amaterasu-Movement.blend'));print('M2_PHASE_ALIGNED_AND_CONTACTS_REBAKED',len(changed),flush=True)

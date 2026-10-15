"""Let the actual loose shoulder tips respond, while leaving the shoulder curl anchored."""
import bpy
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(root/'review/drafts/run-candidate.blend'));coat=bpy.data.objects['Wolf ivory coat'];rig=bpy.data.objects['DivineWolfRig']
def smooth(t):t=max(0,min(1,t));return t*t*(3-2*t)
count=0
for v in coat.data.vertices:
 old={coat.vertex_groups[g.group].name:g.weight for g in v.groups};side='L' if v.co.x>=0 else 'R';base='shoulderFur'+side;names=[base,base+'Flow',base+'Tip'];amount=sum(old.get(n,0) for n in names)
 if amount<.00001:continue
 x,y,z=v.co;loose=smooth((y+1.25)/.80)*smooth((z-3.55)/.25)*smooth((abs(x)-.72)/.25);target=max(amount,.94*loose)
 if target<=amount+.0001:continue
 bone=rig.data.bones[base];d=bone.tail_local-bone.head_local;t=max(0,min(1,(v.co-bone.head_local).dot(d)/d.length_squared));q=min(1.999,t*2);i=int(q);u=smooth(q-i)
 new={n:w*(1-target)/max(1e-7,1-amount) for n,w in old.items() if n not in names};new[names[i]]=target*(1-u);new[names[i+1]]=target*u;top=sorted(new.items(),key=lambda p:-p[1])[:4];total=sum(w for n,w in top)
 for index in [g.group for g in v.groups]:coat.vertex_groups[index].remove([v.index])
 for n,w in top:coat.vertex_groups[n].add([v.index],w/total,'REPLACE')
 count+=1
bpy.ops.wm.save_as_mainfile(filepath=str(root/'review/drafts/run-candidate.blend'));print('LOOSE_TIP_REWEIGHTED',count)

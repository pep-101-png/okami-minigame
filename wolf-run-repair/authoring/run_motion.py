import bpy,math,json,numpy as np,os
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];stage=10
bpy.ops.wm.open_mainfile(filepath=str(root/'authoring/wolf.blend'))
rig=bpy.data.objects['DivineWolfRig'];coat=bpy.data.objects['Wolf ivory coat'];scene=bpy.context.scene
rig.animation_data.action=None
for b in rig.pose.bones:b.location=(0,0,0);b.rotation_euler=(0,0,0)
fur_names=['ruffL','ruffR','shoulderFurL','shoulderFurR','foreFurL','foreFurR','hindFurL','hindFurR'];extra_fur=[n+s for n in fur_names for s in ['Flow','Tip']];extra_tail=[n+s for n in ['tail','tailMid','tailTip','tailEnd'] for s in ['Flow','Silk']];spine_names=['chestBackA','chestBackB','hipsBackA','hipsBackB']
source=(root.parent/'wolf-motion-refinement/authoring/revise.py').read_text();a=source.index('leg_specs={}');b=source.index('# Pose functions',a);code=source[a:b].replace("[('Walk',36,.64,2.0),('Run',24,.40,2.20)]","[('Run',24,.40,2.20)]")
# Fewer visual folds: allow the hock to recover below the belly rather than
# lifting the entire massive thigh nearly horizontally into the torso.
code=code.replace("lift=(.58 if running and stage>=2", "lift=((.22 if leg=='hind' else .36) if running and stage>=2")
exec(code)
for bone in rig.pose.bones:
 for c in list(bone.constraints):bone.constraints.remove(c)
rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'review/drafts/run-candidate.blend'))

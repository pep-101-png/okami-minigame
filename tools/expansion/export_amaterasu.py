"""Export the approved original wolf and movement library; never save the Blender source."""
import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];source=R/'original-wolf-jump-dodge/Amaterasu-Movement.blend';before=hashlib.sha256(source.read_bytes()).hexdigest();bpy.ops.wm.open_mainfile(filepath=str(source));s=bpy.data.scenes['01 · Action inspection'];bpy.context.window.scene=s;r=bpy.data.objects['WOLF_RIG'];bpy.context.view_layer.objects.active=r
if r.mode!='OBJECT':bpy.ops.object.mode_set(mode='OBJECT')
exec(compile((R/'tools/expansion/author_combat.py').read_text(),str(R/'tools/expansion/author_combat.py'),'exec'))
exec(compile((R/'tools/organic/author_sleep.py').read_text(),str(R/'tools/organic/author_sleep.py'),'exec'))
keep=['Sleep_Down','Sleep_Loop','Sleep_Up','Idle_Natural','Walk_Natural','Jog_Natural','Sprint_Fluid','Walk_Turn_L','Walk_Turn_R','Jog_Turn_L','Jog_Turn_R','Sprint_Turn_L','Sprint_Turn_R','Jump_Standing','Jump_Walk','Jump_Jog','Jump_Sprint','Jump_Double','Air_Fall','Land_Soft','Land_Heavy','Dodge_Left','Dodge_Right','Dodge_Back','Dodge_Forward','Dodge_Walk','Dodge_Jog','Dodge_Sprint','Thrust','Sweep','Finish','HeavyArc','HeavyReturn','ChargedThrust','ChargedHeavy','AirStrike','ChargeLight','ChargeHeavy','Bark','Disc1','Disc2','Disc3','DiscHeavy','DiscCharged']
# Export only original character objects. Studio, wind and demonstrations stay in Blender.
for o in bpy.context.view_layer.objects:o.select_set(False)
for o in s.objects:
 if o==r or(o.type=='MESH'and o.parent==r):o.select_set(True)
r.animation_data.action=None
for track in list(r.animation_data.nla_tracks):r.animation_data.nla_tracks.remove(track)
for a in list(bpy.data.actions):
 if a.name not in keep:bpy.data.actions.remove(a)
 else:a.use_frame_range=True;a.frame_start=1;a.frame_end=int(a.get('duration_frames',a.get('cycle_frames',240)))+1
for p in r.pose.bones:p.matrix_basis.identity()
s.frame_set(1);s.frame_start=1;s.frame_end=481
bpy.ops.export_scene.gltf(filepath=str(R/'public/models/amaterasu-original.glb'),export_format='GLB',use_selection=True,use_active_scene=True,export_animations=True,export_animation_mode='ACTIONS',export_anim_single_armature=True,export_force_sampling=True,export_bake_animation=True,export_def_bones=False,export_reset_pose_bones=True,export_optimize_animation_size=True,export_materials='EXPORT',export_cameras=False,export_lights=False)
assert hashlib.sha256(source.read_bytes()).hexdigest()==before
(R/'notes/expansion/animation-export.json').write_text(json.dumps({'source_sha256':before,'original_source_unchanged':True,'requested_actions':keep},indent=2));print('ORIGINAL_AMATERASU_EXPORTED')

"""Convert a COPY of the verified game GLB. Never open/save original Blender sources."""
import bpy,json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[2];source=R/'public/models/amaterasu-original.glb';digest=hashlib.sha256(source.read_bytes()).hexdigest();bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=60;bpy.ops.import_scene.gltf(filepath=str(source));s=bpy.context.scene
for image in bpy.data.images:
 if image.type=='IMAGE' and image.size[0]:
  image.filepath_raw=str(R/'unity/Assets/Sunward/Textures'/('Wolf-'+image.name.split('.')[0]+'.png'));image.file_format='PNG';image.save()
arm=next(o for o in s.objects if o.type=='ARMATURE');clips=[]
for a in bpy.data.actions:
 a.use_fake_user=True;a.use_frame_range=True;a.frame_start=a.frame_range[0];a.frame_end=a.frame_range[1];clips.append({'name':a.name,'start':a.frame_start,'end':a.frame_end})
materials=[]
for m in bpy.data.materials:
 maps=[]
 if m.use_nodes:
  maps=[n.image.name for n in m.node_tree.nodes if n.type=='TEX_IMAGE'and n.image]
 bs=next((n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if m.use_nodes else None
 materials.append({'name':m.name,'images':maps,'color':list(bs.inputs['Base Color'].default_value)if bs else list(m.diffuse_color),'metallic':bs.inputs['Metallic'].default_value if bs else 0,'roughness':bs.inputs['Roughness'].default_value if bs else .8})
arm.animation_data.action=None
for t in list(arm.animation_data.nla_tracks):arm.animation_data.nla_tracks.remove(t)
for p in arm.pose.bones:p.matrix_basis.identity()
s.frame_set(0);bpy.context.view_layer.update()
mesh_report=[{'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons)}for o in s.objects if o.type=='MESH']
bpy.ops.export_scene.fbx(filepath=str(R/'unity/Assets/Sunward/Models/Amaterasu.fbx'),use_selection=False,object_types={'ARMATURE','MESH'},global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_UNITS',axis_forward='-Z',axis_up='Y',use_mesh_modifiers=False,mesh_smooth_type='OFF',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,bake_anim_use_all_bones=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=True,bake_anim_force_startend_keying=True,bake_anim_step=1,bake_anim_simplify_factor=0,path_mode='RELATIVE',embed_textures=False)
assert hashlib.sha256(source.read_bytes()).hexdigest()==digest
(R/'unity/Review/wolf-export.json').write_text(json.dumps({'source_sha256':digest,'source_unchanged':True,'clips':clips,'meshes':mesh_report,'materials':materials,'meshMaterials':[{'name':o.name,'materials':[m.name for m in o.data.materials]}for o in s.objects if o.type=='MESH'],'notes':'FBX uses native Unity importer; Editor builder remaps preserved PNG base maps. Unity visual comparison remains required.'},indent=2));print('WOLF_FBX_EXPORTED',len(clips),'actions')

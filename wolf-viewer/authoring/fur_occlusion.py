import bpy
from pathlib import Path
root=Path(__file__).resolve().parents[1];bpy.ops.wm.open_mainfile(filepath=str(root/'review/drafts/run-candidate.blend'))
coat=bpy.data.objects['Wolf ivory coat'];rig=bpy.data.objects['DivineWolfRig'];rig.animation_data.action=None
for b in rig.pose.bones:b.location=(0,0,0);b.rotation_euler=(0,0,0)
bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');coat.select_set(True);bpy.context.view_layer.objects.active=coat
mat=coat.data.materials[0];image=bpy.data.images.new('Soft fur occlusion',width=2048,height=2048);image.generated_color=(1,1,1,1);image.colorspace_settings.name='Non-Color';target=mat.node_tree.nodes.new('ShaderNodeTexImage');target.image=image;mat.node_tree.nodes.active=target
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=False;scene.render.bake.margin=12;bpy.ops.object.bake(type='AO');image.filepath_raw=str(root/'authoring/fur-occlusion.png');image.file_format='PNG';image.save()

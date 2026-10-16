"""Clean UV paint and fresh fur normals; retain every pose and rest vertex."""
import bpy,math,json,sys,numpy as np
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[1];stage=10
paint_only='--paint-only' in sys.argv
bpy.ops.wm.open_mainfile(filepath=str(root/'review/drafts/run-candidate.blend'))
rig=bpy.data.objects['DivineWolfRig'];coat=bpy.data.objects['Wolf ivory coat'];scene=bpy.context.scene
rig.animation_data.action=None
for b in rig.pose.bones:b.location=(0,0,0);b.rotation_euler=(0,0,0)
bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');coat.select_set(True);bpy.context.view_layer.objects.active=coat
# Repack the full surface rather than reusing the overlapping imported islands.
if not paint_only:
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(65),island_margin=.012,area_weight=.35,correct_aspect=True,scale_to_bounds=True);bpy.ops.object.mode_set(mode='OBJECT')
source=(root/'authoring/paint.py').read_text()
# The imported tangent normal texture belongs to the old UV map. Rebuild it.
insert='''# Rebuild tangent-space grain in the clean UV layout.
normal_atlas=bpy.data.images.new('Clean flowing fur normals',width=4096,height=4096);normal_atlas.generated_color=(.5,.5,1,1);normal_atlas.colorspace_settings.name='Non-Color'
normal_target=nodes.new('ShaderNodeTexImage');normal_target.image=normal_atlas;nodes.active=normal_target
scene.render.bake.margin=12;bpy.ops.object.bake(type='NORMAL');normal_atlas.filepath_raw=str(root/'authoring/fur-normals.png');normal_atlas.file_format='PNG';normal_atlas.save();normal_atlas.pack()
normal_node=nodes.new('ShaderNodeNormalMap');normal_node.inputs['Strength'].default_value=.40;links.new(normal_target.outputs['Color'],normal_node.inputs['Color']);links.new(normal_node.outputs['Normal'],bs.inputs['Normal'])
'''
if paint_only:
    # Only use after a complete geometry/normal bake; keep that UV layout.
    assert coat.data.uv_layers and (root/'authoring/fur-normals.png').is_file()
    insert="""normal_atlas=bpy.data.images.load(str(root/'authoring/fur-normals.png'),check_existing=False);normal_atlas.colorspace_settings.name='Non-Color';normal_atlas.pack()
normal_target=nodes.new('ShaderNodeTexImage');normal_target.image=normal_atlas
normal_node=nodes.new('ShaderNodeNormalMap');normal_node.inputs['Strength'].default_value=.40;links.new(normal_target.outputs['Color'],normal_node.inputs['Color']);links.new(normal_node.outputs['Normal'],bs.inputs['Normal'])
"""
# Replace the older helper's normal-map section inside its loaded source.
# Execute helper preparation up to its final exec, then adjust its assembled text.
prep=source[:source.rindex("exec(compile(text,'paint-body-and-face','exec'))")];exec(compile(prep,'prepare-clean-paint','exec'))
# Replace inherited normal-dependent paint with a continuous ivory wash.
a=text.index("a=source.index('# Layered ivory coat:')");b=text.index('\n',a)
text=text[:a]+"exec(compile((root/'authoring'/'coat_material.py').read_text(),'ivory-pigment','exec'))"+text[b:]
# Remove the flat shoulder and ankle scrolls replaced by sculpted curls;
# retain the tail ink. Texture blur alone cannot repair misplaced artwork.
text=text.replace("exec(paint_code)","paint_code=paint_code.replace('[(-1.30,3.55,.22),(-1.08,.79,.115),(2.13,.82,.13)]','[]')\nexec(paint_code)")
# Paint the newly lengthened muzzle tip, and process ribbons before projection.
watercolor_hook="exec(compile((root/'authoring/watercolor_pigment.py').read_text(),'watercolor-pigment','exec'))\nmask=watercolor_pigment(mask)\n"
text=text.replace("exec(paint_code)", "paint_code=paint_code.replace('default_value=-4.06','default_value=-4.203')\npaint_code=paint_code.replace('mask.save(root/',"+repr(watercolor_hook)+"+'mask.save(root/')\nexec(paint_code)")
a=text.index('# Keep the existing subtle UV-aligned normal grain.');b=text.index('rig.animation_data.action=previous',a);text=text[:a]+insert+'\n'+text[b:]
text=text.replace("scene.render.bake.margin=6","scene.render.bake.margin=12").replace("scene.cycles.samples=8","scene.cycles.samples=16")
exec(compile(text,'clean-uv-coat','exec'))
rig.animation_data.action=bpy.data.actions['Idle'];scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(root/'review/drafts/run-candidate.blend'))
print('FUR_FINISH',len(coat.data.vertices),len(coat.data.uv_layers),flush=True)

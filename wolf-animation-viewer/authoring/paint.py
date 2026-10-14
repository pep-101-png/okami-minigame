"""Repaint eyes and ribbons on the existing UVs without changing the mesh."""
import numpy as np
source=(root.parents[0]/'wolf-art-rebuild'/'build.py').read_text()
meshes=[coat]
a=source.index('# Layered ivory coat:');b=source.index('# Swept layered mane',a);exec(source[a:b])
a=source.index('from PIL import Image,ImageDraw');b=source.index('# A genuine deforming skeleton',a)
paint_code=source[a:b]
# Slightly forward and higher, but fitted to the same surface (no eye spheres).
paint_code=paint_code.replace('y-.04,z+.035','y-.105,z+.075')
if stage>=10:
 paint_code=paint_code.replace('math.tau*1.22','math.tau*1.10').replace('r=.045+.48*i/419','r=.035+.39*i/419').replace('(-.50+r*math.cos(a),3.62+r*math.sin(a))','(-1.05+r*math.cos(a),3.81+r*math.sin(a))').replace("points,.13,side)","points,.155,side)")
 paint_code=paint_code.replace("(-.15,3.22),(.40,3.24),(.99,3.56),(1.21,3.86)","(-.35,3.17),(.23,3.23),(.86,3.52),(1.16,3.79)")
 paint_code=paint_code.replace("(.16,3.48),(.72,3.71),(.94,4.03)","(.06,3.39),(.66,3.61),(.98,3.91)")
 paint_code=paint_code.replace("(-2.12,3.10),(-2.08,3.48),(-1.87,3.91),(-1.53,4.29)","(-2.13,3.07),(-2.10,3.43),(-1.88,3.89),(-1.55,4.18)")
if stage>=10:
 wash="""# Subtle pigment variation and softened edges turn flat ribbons into painted ink.
from PIL import ImageFilter
pixels=np.array(mask);red_pixels=(pixels[:,:,0]==185)&(pixels[:,:,1]==22)&(pixels[:,:,2]==10)
rng=np.random.default_rng(1040);grain=rng.normal(0,3,pixels.shape[:2]);yy,xx=np.indices(pixels.shape[:2]);wash=5*np.sin(xx*.015+yy*.006)+3*np.sin(yy*.047)+grain
for channel,amount in [(0,1),(1,.32),(2,.18)]:
 values=np.clip(pixels[:,:,channel].astype(float)+wash*amount,0,255).astype('uint8');pixels[:,:,channel][red_pixels]=values[red_pixels]
pixels[:,:,3][red_pixels]=249
mask=Image.fromarray(pixels).filter(ImageFilter.GaussianBlur(.35))
"""
 paint_code=paint_code.replace("mask.save(root/",wash+"\nmask.save(root/")
exec(paint_code)
# Use the existing UV arrangement and neutral rest pose to avoid sliding paint.
previous=rig.animation_data.action;rig.animation_data.action=None
for bone in rig.pose.bones:bone.rotation_euler=(0,0,0);bone.location=(0,0,0)
bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');coat.select_set(True);bpy.context.view_layer.objects.active=coat
atlas=bpy.data.images.new('Refined painted fur',width=4096,height=4096);target=nodes.new('ShaderNodeTexImage');target.image=atlas;nodes.active=target
scene.render.engine='CYCLES';scene.cycles.samples=8;scene.cycles.use_denoising=False;scene.render.bake.use_pass_direct=False;scene.render.bake.use_pass_indirect=False;scene.render.bake.use_pass_color=True;scene.render.bake.margin=6
bpy.ops.object.bake(type='DIFFUSE');atlas.filepath_raw=str(root/'authoring'/f'fur-pass-{stage:02}.png');atlas.file_format='PNG';atlas.save();atlas.pack();links.new(target.outputs['Color'],bs.inputs['Base Color'])
# Keep the existing subtle UV-aligned normal grain.
normal_image=bpy.data.images.get('Fur grain normals')
if normal_image:
 normal_tex=nodes.new('ShaderNodeTexImage');normal_tex.image=normal_image;normal=nodes.new('ShaderNodeNormalMap');normal.uv_map=coat.data.uv_layers.active.name;links.new(normal_tex.outputs['Color'],normal.inputs['Color']);links.new(normal.outputs['Normal'],bs.inputs['Normal'])
rig.animation_data.action=previous
